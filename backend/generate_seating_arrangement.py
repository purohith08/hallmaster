import pandas as pd
from collections import defaultdict
from config import EXAM_SLOTS, SESSIONS, DEPARTMENT_ALIASES, DEPT_SLOT_MAPPING

# -----------------------------
# Generate Seating Arrangement
# -----------------------------
def generate_seating_arrangement(students, halls, schedule, exam_type, session_type):
    print("[DEBUG] Starting seating arrangement generation...")

    students_df = pd.DataFrame(students)
    students_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
    students_df['department'] = students_df['department'].apply(standardize_department)
    print(f"[DEBUG] Students DataFrame shape: {students_df.shape}")

    halls_df = pd.DataFrame(halls)
    schedule_df = pd.DataFrame(schedule)
    print(f"[DEBUG] Halls shape: {halls_df.shape}, Schedule shape: {schedule_df.shape}")

    valid_slots = SESSIONS.get(session_type, [])
    schedule_df = schedule_df[schedule_df['slot'].isin(valid_slots)]
    print(f"[DEBUG] Valid slots for session '{session_type}': {valid_slots}")

    # Map exams to departments
    exam_department_map = {}
    for _, exam in schedule_df.iterrows():
        dept_info = exam.get('department', '')
        if dept_info:
            depts = extract_departments(dept_info)
            exam_department_map[exam['course_code']] = depts

    arrangements = []

    # Assign students to halls per slot
    for slot in valid_slots:
        slot_departments = DEPT_SLOT_MAPPING.get(slot, [])
        slot_exams = schedule_df[schedule_df['slot'] == slot]
        print(f"[DEBUG] Slot {slot} departments: {slot_departments}, Exams: {len(slot_exams)}")

        for _, exam in slot_exams.iterrows():
            course_code = exam['course_code']
            course_name = exam['course_name']
            date = exam['date']
            exam_departments = exam_department_map.get(course_code, [])
            valid_exam_departments = [d for d in exam_departments if d in slot_departments]

            if not valid_exam_departments:
                continue

            slot_students = students_df[students_df['department'].isin(valid_exam_departments)]
            if slot_students.empty:
                continue

            available_halls = halls_df.sort_values('capacity', ascending=False)
            students_assigned = 0
            total_students = len(slot_students)

            for _, hall in available_halls.iterrows():
                if students_assigned >= total_students:
                    break
                hall_no = hall['hall_no']
                hall_capacity = hall['capacity']
                current_occupancy = len([a for a in arrangements if a['hall_no'] == hall_no and a['slot'] == slot])
                available_seats = hall_capacity - current_occupancy
                if available_seats <= 0:
                    continue

                hall_students = slot_students.iloc[students_assigned:students_assigned + available_seats]
                students_assigned += len(hall_students)

                for i, (_, student) in enumerate(hall_students.iterrows()):
                    seat_no = current_occupancy + i + 1
                    arrangements.append({
                        'hall_no': hall_no,
                        'seat_no': seat_no,
                        'reg_no': student['reg_no'],
                        'name': student.get('name', ''),
                        'department': student['department'],
                        'year': student['academic_year'],
                        'course_code': course_code,
                        'course_name': course_name,
                        'date': date,
                        'slot': slot,
                        'start_time': EXAM_SLOTS[slot]['start'],
                        'end_time': EXAM_SLOTS[slot]['end'],
                        'exam_type': exam_type
                    })

    df = pd.DataFrame(arrangements)
    print(f"[DEBUG] Completed seating arrangement, total rows: {len(df)}")
    return df

# -----------------------------
# Slot Report
# -----------------------------
def generate_slot_report(students_df):
    print("[DEBUG] Generating slot report...")
    students_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
    students_df['slot'] = students_df['department'].apply(get_slot_by_department)
    slot_dept_counts = students_df.groupby(['slot', 'department']).size().reset_index(name='count')
    pivot_table = slot_dept_counts.pivot_table(index='slot', columns='department', values='count', fill_value=0).reset_index()
    pivot_table['Total'] = pivot_table.sum(axis=1, numeric_only=True)
    print(f"[DEBUG] Slot report generated with shape: {pivot_table.shape}")
    return pivot_table

# -----------------------------
# Validate Student Slot Assignment
# -----------------------------
def validate_student_slot_assignment(students_df):
    print("[DEBUG] Validating student slot assignments...")
    students_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
    invalid_assignments = []
    for _, student in students_df.iterrows():
        department = student['department']
        assigned_slot = get_slot_by_department(department)
        if assigned_slot is None:
            invalid_assignments.append({
                'reg_no': student['reg_no'],
                'name': student.get('name', ''),
                'department': department,
                'error': 'Department not assigned to any slot'
            })
    print(f"[DEBUG] Total invalid assignments: {len(invalid_assignments)}")
    return invalid_assignments

# -----------------------------
# Helper Functions
# -----------------------------
def extract_departments(dept_string):
    import re
    match = re.search(r'\((.*?)\)', dept_string)
    if match:
        return [standardize_department(d.strip()) for d in match.group(1).split(',')]
    departments = []
    dept_upper = dept_string.upper()
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_upper:
                departments.append(dept)
                break
    return departments

def standardize_department(dept_name):
    if not isinstance(dept_name, str):
        return dept_name
    dept_name_upper = dept_name.upper().strip()
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_name_upper:
                return dept
    return dept_name

def get_slot_by_department(department):
    for slot, depts in DEPT_SLOT_MAPPING.items():
        if department in depts:
            return slot
    return None

__all__ = [
    "generate_seating_arrangement",
    "generate_slot_report",
    "validate_student_slot_assignment"
]
