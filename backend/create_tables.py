# backend/create_tables.py
from db import get_connection

sql_statements = [
    """
   -- ========================
-- 1. Students Table
-- ========================
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    Reg_No VARCHAR(50) UNIQUE NOT NULL,   -- ✅ Added
    department VARCHAR(50) NOT NULL
);


-- ========================
-- 2. Exams Table
-- ========================
CREATE TABLE exams (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,
    exam_date DATE NOT NULL
);

-- ========================
-- 3. Halls Table
-- ========================
CREATE TABLE halls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0)
);

-- ========================
-- 4. Seating Arrangements
-- (Mapping Students to Exam & Hall)
-- ========================
CREATE TABLE arrangements (
    id SERIAL PRIMARY KEY,
    exam_id INT NOT NULL,
    hall_id INT NOT NULL,
    student_id INT NOT NULL,
    seat_number INT NOT NULL,

    CONSTRAINT fk_exam FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
    CONSTRAINT fk_hall FOREIGN KEY (hall_id) REFERENCES halls(id) ON DELETE CASCADE,
    CONSTRAINT fk_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,

    UNIQUE (exam_id, student_id),  -- Prevent same student from being seated twice in same exam
    UNIQUE (exam_id, hall_id, seat_number) -- Prevent seat conflicts
);

    """
]

def main():
    conn = get_connection()
    cur = conn.cursor()
    for sql in sql_statements:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
