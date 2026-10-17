import requests
import psycopg
import os
from dotenv import load_dotenv

url = "https://jsonplaceholder.typicode.com/users"
try:
    response = requests.get(url,timeout=10)
    response.raise_for_status()

    data = response.json()
except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
    raise

users_transformed = []
#we wanna keep only id,name,email,city,company_name
try:
    for user in data:
        new_user = {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'city': user['address']['city'],
            'company_name': user['company']['name']
        }
        users_transformed.append(new_user)

except (KeyError, TypeError) as e:
    print(f"Transformation failed : {e}")
    raise


load_dotenv()
conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()

try:
    for user in users_transformed:
        cursor.execute(
        """
        INSERT INTO api_user (id, name, email, city, company_name)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT(id)
        DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            city = EXCLUDED.city,
            company_name = EXCLUDED.company_name
        """,
        (
            user["id"],
            user["name"],
            user["email"],
            user["city"],
            user["company_name"]
        )
    )
    conn.commit()
    print('Load completed !')
except psycopg.Error as e:
    conn.rollback()
    print(f"Database load failed: {e}")
    raise
finally:
    cursor.close()
    conn.close()