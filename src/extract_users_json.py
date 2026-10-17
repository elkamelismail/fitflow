import json
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()
conn = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, email
    FROM app_user
    ORDER BY id;
""")
batch_size = 5
i = 1

with open(r'C:\Users\issma\Desktop\fitflow\data\users.json','w',encoding='utf-8') as jsonfile:
    jsonfile.write("[\n")
    first_record = True
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        print('--- Batch ',i,' ---')
        for row in rows:
            print(row)
            row_dict = {
                "id": row[0],
                "name": row[1],
                "email": row[2]
            }
            if not first_record:
                jsonfile.write(",\n")
            json.dump(row_dict,jsonfile,indent=4)

            first_record = False
        print(f"Batch {i} written!")
        i+=1
    jsonfile.write("\n]")

cursor.close()
conn.close()
