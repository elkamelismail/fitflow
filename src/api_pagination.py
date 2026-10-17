import requests
import time
import os
from dotenv import load_dotenv
import psycopg
import logging
import random
from data_validation import is_valid
from psycopg.types.json import Jsonb

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("fitflow.log"),
            logging.StreamHandler()
        ]
)

url = "https://jsonplaceholder.typicode.com/posts"

page = 1
total_posts = 0
valid_posts = 0

page_size = 5
max_attempts = 3
base_delay = 1

retryable_statuses = {429, 500, 502, 503, 504}

load_dotenv()
logging.info("Starting FitFlow API ingestion pipeline")
conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()
cursor.execute(
    """
    SELECT last_processed_id
    FROM pipeline_watermark
    WHERE pipeline_name = %s
    """,
    ("fitflow_posts",)
)
row = cursor.fetchone()
last_processed_id = row[0]
logging.info(f"Last ID in MetaData Table : {last_processed_id}")

cursor.execute(
    """
    SELECT last_processed_offset
    FROM pipeline_watermark
    WHERE pipeline_name = %s
    """,
    ("fitflow_posts",)
)

row = cursor.fetchone()

if row is None:
    raise ValueError("Pipeline watermark not found")

last_processed_offset = row[0]

min_interval = 1.0
last_request_time = None
try:
    
    while True:
        params = {
            "_start":last_processed_offset,
            "_limit": page_size
        }

        for attempt in range(max_attempts):
            try:
                if last_request_time is not None:
                    elapsed = time.monotonic() - last_request_time
                    remaining = max(0,min_interval - elapsed)
                    time.sleep(remaining)

                last_request_time = time.monotonic()
                logging.info(f"Sending request for page {page} at {last_request_time:.2f}")

                response = requests.get(
                    url,
                    params=params,
                    timeout=10
                )

                response.raise_for_status()
                data = response.json()
                logging.info(f"Page {page}: Request successful!")
                break

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code

                # Permanent HTTP error → stop immediately
                if status not in retryable_statuses:
                    logging.error(f"Non-retryable HTTP error {status}. Stopping.")
                    raise


                if attempt == max_attempts - 1:
                    logging.error("All attempts failed. Stopping pipeline.")
                    raise
                logging.warning(f"Page {page}, attempt {attempt + 1}: HTTP {status}. Retrying.")

                # Respect Retry-After when provided as seconds
                retry_after = e.response.headers.get("Retry-After")

                if retry_after and retry_after.isdigit():
                    delay = int(retry_after)
                else:
                    delay = base_delay * (2 ** attempt)
                    delay += random.uniform(0,1)

                logging.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)

            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError) as e:


                if attempt == max_attempts - 1:
                    logging.exception("All attempts failed. Stopping pipeline.")
                    raise
                logging.warning(f"Page {page}, attempt {attempt + 1}: {e}. Retrying.")

                delay = base_delay * (2 ** attempt)
                delay += random.uniform(0,1)

                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

            except requests.exceptions.RequestException as e:
                logging.exception(f"Unexpected API request error.")
                raise

        # Stop pagination when there are no more posts
        if not data:
            logging.info("No more data. Stopping pagination.")
            break

        try:
            page_valid_posts = 0
            for post in data:
                cursor.execute(
                    """
                    INSERT INTO raw_api_post(payload)
                    VALUES(%s)
                    """,(Jsonb(post),)
                )
                logging.info(f"Raw Post inserted !")

            for post in data:
                #validate the post
                valid,reason = is_valid(post)
                if valid == False:
                    logging.warning(f"Rejected post{post.get('id')} : {reason}")
                    cursor.execute(
                        """
                        INSERT INTO rejected_api_post(payload,reason)
                        VALUES(%s,%s)
                        """,(Jsonb(post),reason)
                    )
                    continue
                
                cursor.execute(
                    """
                    INSERT INTO api_post(id,user_id,title,body)
                    VALUES(%s,%s,%s,%s)
                    ON CONFLICT(id)
                    DO UPDATE SET
                        user_id = EXCLUDED.user_id,
                        title = EXCLUDED.title,
                        body = EXCLUDED.body
                    """,
                (
                    post['id'],
                    post['userId'],
                    post['title'],
                    post['body']
                )
            )
                page_valid_posts += 1
            new_watermark = max((post["id"] for post in data if type(post.get("id")) is int and post["id"]>0),
                                default= last_processed_id)
            new_offset = last_processed_offset + len(data)
            cursor.execute(
                """
                UPDATE pipeline_watermark
                SET last_processed_id = %s
                WHERE pipeline_name = %s
                """,
                (new_watermark,'fitflow_posts')
            )
            cursor.execute(
                """
                UPDATE pipeline_watermark
                SET last_processed_offset = %s
                WHERE pipeline_name = %s    
                """,(new_offset,'fitflow_posts')
            )
            conn.commit()

            last_processed_offset = new_offset
            last_processed_id = new_watermark

            valid_posts += page_valid_posts
            logging.info(f"page {page} loaded !")
        except Exception as e:
            conn.rollback()
            logging.exception(f"Page {page} load Failed .")
            raise

        
        # Process current page
        logging.info(f"Page {page}: {len(data)} posts")
        logging.debug(f"IDs: {' '.join(str(post.get('id')) for post in data)}")
        total_posts += len(data)
        page += 1
finally:
    cursor.close()
    conn.close()

logging.info(f"FitFlow ingestion completed successfully. Total posts retrieved: {total_posts}")
logging.info(f"Total valid posts committed : {valid_posts}")
logging.info(f"Total rejected: {total_posts - valid_posts}")