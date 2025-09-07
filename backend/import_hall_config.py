# backend/import_hall_config.py
import pandas as pd
from db import get_connection

def import_halls(xlsx_path):
    df = pd.read_excel(xlsx_path)
    conn = get_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO halls (name, capacity, config) VALUES (%s, %s, %s)",
            (row['HallName'], int(row['Capacity']), row['Config'])
        )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    import_halls("uploads/halls.xlsx")
