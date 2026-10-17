import os
import csv
import psycopg
from dotenv import load_dotenv

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
with open(r'C:\Users\issma\Desktop\fitflow\data\users.csv','w',newline='',encoding='utf-8') as csvfile:
    header = ['id', 'name', 'email']
    writer = csv.writer(csvfile,delimiter=',',)
    writer.writerow(header)
    while True:
        rows = cursor.fetchmany(batch_size)

        if not rows:
            break
        print('--- Batch ',i,' ---')
        for row in rows:
            print(row)
        writer.writerows(rows)
        print(f"Batch {i} appended !")
        i+=1
        



cursor.close()
conn.close()