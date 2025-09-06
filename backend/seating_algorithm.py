import pandas as pd
from collections import defaultdict
import random
from config import EXAM_SLOTS, SESSIONS, DEPARTMENT_ALIASES, DEPT_SLOT_MAPPING

def generate_seating_arrangement(students, halls, schedule, exam_type, session_type):
    """
    Generate optimized seating arrangement based on student data, hall capacities, and exam schedule
    """
    # Convert to DataFrames for easier manipulation
    students_df = pd.DataFrame(students)
    halls_df = pd.DataFrame(halls)
    schedule_df = pd.DataFrame(schedule)
    
    # Filter schedule based on session type
    valid_slots = SESSIONS.get(session_type, [])
    schedule_df = schedule_df[schedule_df['slot'].isin(valid_slots)]
    
    # Group students by department and year
    grouped_students = students_df.groupby(['department', 'academic_year'])
    
    # Create a mapping of exams to departments
    exam_department_map = {}
    for _, exam in schedule_df.iterrows():
        dept_info = exam.get('department', '')
        if dept_info:
            # Extract departments from the string
            depts = extract_departments(dept_info)
            exam_department_map[exam['course_code']] = depts
    
    # Assign halls to exams based on department needs and slot
    arrangements = []
    hall_assignments = defaultdict(list)
    
    # Process each slot in the session
    for slot in valid_slots:
        # Get departments for this slot based on the fixed mapping
        slot_departments = DEPT_SLOT_MAPPING.get(slot, [])
        
        # Get exams for this slot
        slot_exams = schedule_df[schedule_df['slot'] == slot]
        
        for _, exam in slot_exams.iterrows():
            course_code = exam['course_code']
            course_name = exam['course_name']
            date = exam['date']
            exam_departments = exam_department_map.get(course_code, [])
            
            # Filter to only include departments that belong to this slot
            valid_exam_departments = [dept for dept in exam_departments if dept in slot_departments]
            
            if not valid_exam_departments:
                continue  # Skip exams that don't have departments in this slot
            
            # Get students from these departments
            slot_students = students_df[students_df['department'].isin(valid_exam_departments)]
            
            if len(slot_students) > 0:
                # Sort halls by capacity (descending)
                available_halls = halls_df.sort_values('capacity', ascending=False)
                
                # Assign students to halls
                students_assigned = 0
                total_students = len(slot_students)
                
                for _, hall in available_halls.iterrows():
                    if students_assigned >= total_students:
                        break
                    
                    hall_no = hall['hall_no']
                    hall_capacity = hall['capacity']
                    
                    # Check how many seats are already occupied in this hall for this slot
                    current_occupancy = len([a for a in arrangements if a['hall_no'] == hall_no and a['slot'] == slot])
                    available_seats = hall_capacity - current_occupancy
                    
                    if available_seats <= 0:
                        continue  # Hall is full for this slot
                    
                    # Get students for this hall
                    hall_students = slot_students.iloc[students_assigned:students_assigned + available_seats]
                    students_assigned += len(hall_students)
                    
                    for i, (_, student) in enumerate(hall_students.iterrows()):
                        seat_no = current_occupancy + i + 1
                        arrangements.append({
                            'hall_no': hall_no,
                            'seat_no': seat_no,
                            'reg_no': student['reg_no'],
                            'name': student['name'],
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
    Extract department names from schedule strings
    Example: "II YEAR(AGRI,EEE,ECE,MECH)" -> ["AGRI", "EEE", "ECE", "MECH"]
    """
    import re
    
    # Find text inside parentheses
    match = re.search(r'\((.*?)\)', dept_string)
    if match:
        departments = match.group(1).split(',')
        return [dept.strip() for dept in departments]
    
    # If no parentheses, try to extract departments from the string
    departments = []
    dept_string_upper = dept_string.upper()
    
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_string_upper:
                departments.append(dept)
                break
    
    return departments

def calculate_department_stats(students_df, schedule_df):
    """
    Calculate department-wise statistics for reporting
    """
    stats = {}
    
    # Group students by department and year
    dept_year_counts = students_df.groupby(['department', 'academic_year']).size().reset_index(name='count')
    
    # Calculate totals
    dept_totals = students_df.groupby('department').size().reset_index(name='total')
    year_totals = students_df.groupby('academic_year').size().reset_index(name='total')
    
    # Count exams by department
    exam_counts = {}
    for _, exam in schedule_df.iterrows():
        dept_info = exam.get('department', '')
        if dept_info:
            departments = extract_departments(dept_info)
            for dept in departments:
                exam_counts[dept] = exam_counts.get(dept, 0) + 1
    
    # Add slot information to department totals
    dept_totals['slot'] = dept_totals['department'].apply(get_slot_by_department)
    
    stats['dept_year_counts'] = dept_year_counts.to_dict('records')
    stats['dept_totals'] = dept_totals.to_dict('records')
    stats['year_totals'] = year_totals.to_dict('records')
    stats['exam_counts'] = exam_counts
    
    return stats

def generate_slot_report(students_df):
    """
    Generate a report showing student counts by slot and department
    """
    # Create a copy of the dataframe
    report_df = students_df.copy()
    
    # Add slot information
    report_df['slot'] = report_df['department'].apply(get_slot_by_department)
    
    # Group by slot and department
    slot_dept_counts = report_df.groupby(['slot', 'department']).size().reset_index(name='count')
    
    # Pivot the table to show departments as columns
    pivot_table = slot_dept_counts.pivot_table(
        index='slot', 
        columns='department', 
        values='count', 
        fill_value=0
    ).reset_index()
    
    # Calculate totals
    pivot_table['Total'] = pivot_table.sum(axis=1, numeric_only=True)
    
    return pivot_table

def validate_student_slot_assignment(students_df):
    """
    Validate that all students are assigned to the correct slot based on their department
    """
    invalid_assignments = []
    
    for _, student in students_df.iterrows():
        department = student['department']
        assigned_slot = get_slot_by_department(department)
        
        if assigned_slot is None:
            invalid_assignments.append({
                'reg_no': student['reg_no'],
                'name': student['name'],
                'department': department,
                'error': 'Department not assigned to any slot'
            })
    
    return invalid_assignments