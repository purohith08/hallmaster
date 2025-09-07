import pandas as pd
from collections import defaultdict
import random
from config import EXAM_SLOTS, SESSIONS, DEPARTMENT_ALIASES, DEPT_SLOT_MAPPING

# ------------------- SEATING ARRANGEMENT -------------------
def generate_seating_arrangement(students, halls, schedule, exam_type, session_type):
    """
    Generate optimized seating arrangement based on student data, hall capacities, and exam schedule.
    """
    # Convert lists to DataFrames
    students_df = pd.DataFrame(students)
    students_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)

    halls_df = pd.DataFrame(halls)
    schedule_df = pd.DataFrame(schedule)

    # Filter schedule based on session type
    valid_slots = SESSIONS.get(session_type, [])
    schedule_df = schedule_df[schedule_df['slot'].isin(valid_slots)]

    # Map exams to departments
    exam_department_map = {}
    for _, exam in schedule_df.iterrows():
        dept_info = exam.get('department', '')
        if dept_info:
            depts = extract_departments(dept_info)
            exam_department_map[exam['course_code']] = depts

    arrangements = []

    # Process each slot
    for slot in valid_slots:
        slot_departments = DEPT_SLOT_MAPPING.get(slot, [])
        slot_exams = schedule_df[schedule_df['slot'] == slot]

        for _, exam in slot_exams.iterrows():
            course_code = exam['course_code']
            course_name = exam['course_name']
            date = exam['date']
            exam_departments = exam_department_map.get(course_code, [])

            # Only departments assigned to this slot
            valid_exam_departments = [dept for dept in exam_departments if dept in slot_departments]
            if not valid_exam_departments:
                continue

            # Select students in these departments
            slot_students = students_df[students_df['department'].isin(valid_exam_departments)]
            if len(slot_students) == 0:
                continue

            # Sort halls by capacity descending
            available_halls = halls_df.sort_values('capacity', ascending=False)
            students_assigned = 0
            total_students = len(slot_students)

            for _, hall in available_halls.iterrows():
                if students_assigned >= total_students:
                    break

                hall_no = hall['hall_no']
                hall_capacity = hall['capacity']

                # Current occupancy in this hall for this slot
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
                        'name': student.get('name', student.get('Name', '')),
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

    return pd.DataFrame(arrangements)

# ------------------- HELPERS -------------------
def get_departments_by_slot(slot):
    """Get departments assigned to a specific slot"""
    return DEPT_SLOT_MAPPING.get(slot, [])

def get_slot_by_department(department):
    """Get the slot assigned to a specific department"""
    for slot, depts in DEPT_SLOT_MAPPING.items():
        if department in depts:
            return slot
    return None

def extract_departments(dept_string):
    """
    Extract department names from schedule strings.
    Example: "II YEAR(AGRI,EEE,ECE,MECH)" -> ["AGRI", "EEE", "ECE", "MECH"]
    """
    import re
    match = re.search(r'\((.*?)\)', dept_string)
    if match:
        return [dept.strip() for dept in match.group(1).split(',')]

    departments = []
    dept_upper = dept_string.upper()
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_upper:
                departments.append(dept)
                break
    return departments

# ------------------- REPORTS -------------------
def calculate_department_stats(students_df, schedule_df):
    """Calculate department-wise statistics for reporting"""
    stats = {}

    dept_year_counts = students_df.groupby(['department', 'academic_year']).size().reset_index(name='count')
    dept_totals = students_df.groupby('department').size().reset_index(name='total')
    year_totals = students_df.groupby('academic_year').size().reset_index(name='total')

    exam_counts = {}
    for _, exam in schedule_df.iterrows():
        dept_info = exam.get('department', '')
        if dept_info:
            for dept in extract_departments(dept_info):
                exam_counts[dept] = exam_counts.get(dept, 0) + 1

    dept_totals['slot'] = dept_totals['department'].apply(get_slot_by_department)

    stats['dept_year_counts'] = dept_year_counts.to_dict('records')
    stats['dept_totals'] = dept_totals.to_dict('records')
    stats['year_totals'] = year_totals.to_dict('records')
    stats['exam_counts'] = exam_counts

    return stats

def generate_slot_report(students_df):
    """Generate a report showing student counts by slot and department"""
    report_df = students_df.copy()
    report_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)
    report_df['slot'] = report_df['department'].apply(get_slot_by_department)

    slot_dept_counts = report_df.groupby(['slot', 'department']).size().reset_index(name='count')
    pivot_table = slot_dept_counts.pivot_table(
        index='slot',
        columns='department',
        values='count',
        fill_value=0
    ).reset_index()

    pivot_table['Total'] = pivot_table.sum(axis=1, numeric_only=True)
    return pivot_table

def validate_student_slot_assignment(students_df):
    """Validate that all students are assigned to the correct slot based on their department"""
    invalid_assignments = []
    students_df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"), inplace=True)

    for _, student in students_df.iterrows():
        department = student['department']
        assigned_slot = get_slot_by_department(department)
        if assigned_slot is None:
            invalid_assignments.append({
                'reg_no': student['reg_no'],
                'name': student.get('name', student.get('Name', '')),
                'department': department,
                'error': 'Department not assigned to any slot'
            })

    return invalid_assignments
