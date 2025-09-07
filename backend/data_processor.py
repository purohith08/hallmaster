import pandas as pd
from docx import Document
from generate_seating_arrangement import standardize_department, get_slot_by_department, extract_departments
from config import DEPARTMENT_ALIASES, ACADEMIC_YEARS, DEPT_SLOT_MAPPING

# ------------------- STUDENT DATA -------------------
def process_student_data(filepath):
    df = pd.read_excel(filepath)

    # Normalize column names
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Map variations to standard column names
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

    # Required columns
    required_columns = ["reg_no", "department", "semester", "section", "academic_year"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Excel must have columns: {required_columns}")

    # Standardize department
    df['department'] = df['department'].apply(standardize_department)
    return df.to_dict(orient="records")


# ------------------- HALL DATA -------------------
def process_hall_data(file_path):
    if file_path.endswith('.xlsx'):
        return process_xlsx_hall_data(file_path)
    raise ValueError("Unsupported file format for hall data")

def process_xlsx_hall_data(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    if 'hall_no' not in df.columns or 'capacity' not in df.columns:
        raise ValueError("Excel must have 'hall_no' and 'capacity' columns")
    df['capacity'] = df['capacity'].astype(int)
    return df.to_dict(orient='records')


# ------------------- SCHEDULE DATA -------------------
def process_schedule_data(file_path):
    """
    Process exam schedule from DOCX files.
    Assign slot purely based on department mapping (DEPT_SLOT_MAPPING).
    """
    schedule = []
    doc = Document(file_path)

    for table in doc.tables:
        headers = []
        for i, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]

            if i == 0:
                headers = [h.lower().replace(' ', '_') for h in cells]
            else:
                if len(cells) >= 4:  # Ensure enough columns
                    exam_data = {headers[j]: cells[j] for j in range(len(cells))}

                    # Extract departments and assign slot
                    dept_info = exam_data.get('department', '')
                    if dept_info:
                        departments = extract_departments(dept_info)
                        if departments:
                            # Assign slot based on first department
                            slot = get_slot_by_department(departments[0])
                            if slot:
                                exam_data['slot'] = slot
                            else:
                                exam_data['slot'] = None
                        else:
                            exam_data['slot'] = None
                    else:
                        exam_data['slot'] = None

                    schedule.append(exam_data)

    return schedule
