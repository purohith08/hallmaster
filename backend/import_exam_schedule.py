# backend/import_exam_schedule.py
import pandas as pd
from db import get_connection

def import_exams(xlsx_path):
    df = pd.read_excel(xlsx_path)
    conn = get_connection()
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO exams (subject, exam_date, hall_id) VALUES (%s, %s, %s)",
            (row['Subject'], row['ExamDate'], int(row['HallID']))
        )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    import_exams("uploads/exams.xlsx")
