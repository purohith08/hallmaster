import pandas as pd
from docx import Document
import re
from config import DEPARTMENT_ALIASES, ACADEMIC_YEARS, DEPT_SLOT_MAPPING

def process_student_data(filepath):
    df = pd.read_excel(filepath)

    # Normalize column names (strip spaces, lowercase, underscores)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Map possible variations to standard names
    rename_map = {
        "reg no": "reg_no",
        "register_number": "reg_no",
        "rollno": "reg_no",
        "roll_no": "reg_no",
        "roll number": "reg_no",

        "department": "department",
        "dept": "department",

        "semester": "semester",
        "sem": "semester",

        "section": "section",

        "year": "academic_year",
        "academic_year": "academic_year",
        "academic year": "academic_year"
    }
    df.rename(columns=rename_map, inplace=True)

    # Required columns (no name, Semester included)
    required_columns = ["reg_no", "department", "semester", "section", "academic_year"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Excel must have {required_columns} columns")

    return df.to_dict(orient="records")

def process_hall_data(file_path):
    """Process hall configuration from XLSX files"""
    if file_path.endswith('.xlsx'):
        return process_xlsx_hall_data(file_path)
    else:
        raise ValueError("Unsupported file format for hall data")

def process_xlsx_hall_data(file_path):
    """Read hall data from Excel and return list of dicts"""
    try:
        df = pd.read_excel(file_path)
        # Expecting columns: 'hall_no', 'capacity'
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        if 'hall_no' not in df.columns or 'capacity' not in df.columns:
            raise ValueError("Excel must have 'hall_no' and 'capacity' columns")
        df['capacity'] = df['capacity'].astype(int)
        halls = df.to_dict(orient='records')
        return halls
    except Exception as e:
        raise ValueError(f"Error reading hall Excel file: {e}")

def process_schedule_data(file_path):
    """Process exam schedule from DOCX files"""
    schedule = []
    doc = Document(file_path)
    
    for table in doc.tables:
        headers = []
        for i, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]
            
            if i == 0:
                # This is the header row
                headers = [h.lower().replace(' ', '_') for h in cells]
            else:
                if len(cells) >= 4:  # Ensure we have enough data
                    exam_data = {}
                    for j, header in enumerate(headers):
                        if j < len(cells):
                            exam_data[header] = cells[j]
                    
                    # Extract slot information based on department
                    dept_info = exam_data.get('department', '')
                    if dept_info:
                        departments = extract_departments(dept_info)
                        if departments:
                            slot = get_slot_by_department(departments[0])
                            if slot:
                                exam_data['slot'] = slot
                    
                    # If slot not assigned by department, try to extract from time
                    if 'slot' not in exam_data:
                        time_str = exam_data.get('time', '') or exam_data.get('time_slot', '')
                        if '9:30' in time_str or '11:00' in time_str or '9.30' in time_str or '11.00' in time_str:
                            exam_data['slot'] = 'I'
                        elif '12:00' in time_str or '1:30' in time_str or '12.00' in time_str or '1.30' in time_str:
                            exam_data['slot'] = 'II'
                        elif '2:30' in time_str or '4:00' in time_str or '2.30' in time_str or '4.00' in time_str:
                            exam_data['slot'] = 'III'
                    
                    schedule.append(exam_data)
    
    return schedule

def standardize_department(dept_name):
    """Standardize department names using the aliases"""
    if not isinstance(dept_name, str):
        return dept_name
    
    dept_name_upper = dept_name.upper().strip()
    
    if 'COMPUTER' in dept_name_upper and 'SCIENCE' in dept_name_upper:
        return 'CSE'
    if 'INFORMATION' in dept_name_upper and 'TECHNOLOGY' in dept_name_upper:
        return 'IT'
    if 'INTERNET' in dept_name_upper and 'THINGS' in dept_name_upper:
        return 'IOT'
    if 'ARTIFICIAL' in dept_name_upper and 'INTELLIGENCE' in dept_name_upper:
        if 'DATA' in dept_name_upper and 'SCIENCE' in dept_name_upper:
            return 'AIDS'
        if 'MACHINE' in dept_name_upper and 'LEARNING' in dept_name_upper:
            return 'AIML'
    if 'CYBER' in dept_name_upper or 'SECURITY' in dept_name_upper:
        return 'CYS'
    if 'ELECTRONIC' in dept_name_upper and 'COMMUNICATION' in dept_name_upper:
        return 'ECE'
    if 'ELECTRICAL' in dept_name_upper and 'ELECTRONIC' in dept_name_upper:
        return 'EEE'
    if 'MECHANICAL' in dept_name_upper:
        return 'MECH'
    if 'BIOMEDICAL' in dept_name_upper:
        return 'BME'
    if 'BIOTECH' in dept_name_upper:
        return 'BT'
    if 'AGRICULTURAL' in dept_name_upper or 'AGRI' in dept_name_upper:
        return 'AGRI'
    
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_name_upper:
                return dept
    
    return dept_name

def standardize_academic_year(year):
    """Standardize academic year format"""
    if not isinstance(year, str):
        return year
    
    year = year.upper().strip()
    
    year_mapping = {
        'I': ['1', 'I', 'FIRST', '1ST', 'IYEAR', 'I YEAR'],
        'II': ['2', 'II', 'SECOND', '2ND', 'IIYEAR', 'II YEAR'],
        'III': ['3', 'III', 'THIRD', '3RD', 'IIIYEAR', 'III YEAR'],
        'IV': ['4', 'IV', 'FOURTH', '4TH', 'IVYEAR', 'IV YEAR']
    }
    
    for std_year, variants in year_mapping.items():
        if year in variants:
            return std_year
    
    return year

def extract_departments(dept_string):
    """Extract department names from schedule strings"""
    match = re.search(r'\((.*?)\)', dept_string)
    if match:
        departments = match.group(1).split(',')
        return [standardize_department(dept.strip()) for dept in departments]
    
    departments = []
    dept_string_upper = dept_string.upper()
    
    for dept, aliases in DEPARTMENT_ALIASES.items():
        for alias in aliases:
            if alias.upper() in dept_string_upper:
                departments.append(dept)
                break
    
    return departments

def get_slot_by_department(department):
    """Get the slot assigned to a specific department"""
    for slot, depts in DEPT_SLOT_MAPPING.items():
        if department in depts:
            return slot
    return None

def validate_departments(departments):
    """Validate that all departments are assigned to slots"""
    invalid_departments = []
    
    for dept in departments:
        if get_slot_by_department(dept) is None:
            invalid_departments.append(dept)
    
    return invalid_departments
