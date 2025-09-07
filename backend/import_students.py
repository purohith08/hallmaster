# backend/import_students.py
import pandas as pd
from db import get_connection

def import_students(xlsx_path):
    df = pd.read_excel(xlsx_path)
    conn = get_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO students (name, department, hall_id) VALUES (%s, %s, %s)",
            (row['Name'], row['Department'], int(row['HallID']))
        )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    import_students("uploads/students.xlsx")
