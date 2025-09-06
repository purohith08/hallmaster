import pandas as pd
from docx import Document
import PyPDF2
import re
from config import DEPARTMENT_ALIASES, ACADEMIC_YEARS, DEPT_SLOT_MAPPING

def process_student_data(file_path):
    """Process student data from XLSX files"""
    df = pd.read_excel(file_path)
    
    # Standardize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Ensure required columns exist
    required_columns = ['name', 'reg_no', 'department', 'section', 'academic_year']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Standardize department names
    if 'department' in df.columns:
        df['department'] = df['department'].apply(standardize_department)
    
    # Standardize academic years
    if 'academic_year' in df.columns:
        df['academic_year'] = df['academic_year'].apply(standardize_academic_year)
    
    # Validate that all departments are assigned to slots
    invalid_departments = validate_departments(df['department'].unique())
    if invalid_departments:
        print(f"Warning: The following departments are not assigned to any slot: {', '.join(invalid_departments)}")
    
    return df.to_dict('records')

def process_hall_data(file_path):
    """Process hall configuration from PDF or DOCX files"""
    if file_path.endswith('.pdf'):
        return process_pdf_hall_data(file_path)
    elif file_path.endswith('.docx'):
        return process_docx_hall_data(file_path)
    else:
        raise ValueError("Unsupported file format for hall data")

def process_pdf_hall_data(file_path):
    """Extract hall data from PDF files"""
    halls = []
    
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        
        for page in reader.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            for line in lines:
                # Look for hall number and capacity patterns
                # Handle different patterns like "107 20", "107/20", "107:20", etc.
                patterns = [
                    r'(\w+[/-]?\d*)\s+(\d+)',  # Matches "107 20", "A-101 30"
                    r'(\w+)[:/](\d+)',         # Matches "107:20", "A101:30"
                    r'Room\s+(\w+).*?(\d+)'    # Matches "Room 107 capacity 20"
                ]
                
                for pattern in patterns:
                    hall_match = re.search(pattern, line)
                    if hall_match:
                        hall_no = hall_match.group(1).strip()
                        try:
                            capacity = int(hall_match.group(2))
                            halls.append({'hall_no': hall_no, 'capacity': capacity})
                            break
                        except ValueError:
                            continue
    
    return halls

def process_docx_hall_data(file_path):
    """Extract hall data from DOCX files"""
    halls = []
    doc = Document(file_path)
    
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) >= 2:
                # Try to extract hall number and capacity
                hall_no = cells[0]
                capacity_str = cells[1]
                
                # Check if capacity is a number
                if capacity_str.isdigit():
                    halls.append({'hall_no': hall_no, 'capacity': int(capacity_str)})
                else:
                    # Try to extract numbers from the string
                    numbers = re.findall(r'\d+', capacity_str)
                    if numbers:
                        halls.append({'hall_no': hall_no, 'capacity': int(numbers[0])})
    
    return halls

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
                            # Assign slot based on the first department found
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
    
    # Handle common variations
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
    
    # Check against aliases
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
    
    # Map variations to standard years
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
    """
    Extract department names from schedule strings
    Example: "II YEAR(AGRI,EEE,ECE,MECH)" -> ["AGRI", "EEE", "ECE", "MECH"]
    """
    import re
    
    # Find text inside parentheses
    match = re.search(r'\((.*?)\)', dept_string)
    if match:
        departments = match.group(1).split(',')
        return [standardize_department(dept.strip()) for dept in departments]
    
    # If no parentheses, try to extract departments from the string
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