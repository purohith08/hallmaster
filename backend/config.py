import os

# -----------------------------
# Base Paths
# -----------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'frontend', 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, '..', 'outputs')

# -----------------------------
# File Types
# -----------------------------
ALLOWED_EXTENSIONS = {
    'students': {'xlsx'},
    'halls': {'pdf', 'docx'},
    'schedules': {'docx'}
}

# -----------------------------
# Exam Slots and Sessions
# -----------------------------
EXAM_SLOTS = {
    'I': {'start': '09:30', 'end': '11:00'},
    'II': {'start': '12:00', 'end': '13:30'},
    'III': {'start': '14:30', 'end': '16:00'}
}

SESSIONS = {
    'FN': ['I', 'II'],  
    'AN': ['III']       
}

DEPT_SLOT_MAPPING = {
    'I': ['CSE', 'IOT', 'IT'],
    'II': ['AIDS'],
    'III': ['AGRI', 'BME', 'BT', 'ECE', 'EEE', 'MECH', 'AIML', 'CYS']
}


# -----------------------------
# Department Aliases
# -----------------------------
DEPARTMENT_ALIASES = {
    'AGRI': ['AGRICULTURE', 'AGRI', 'AGRICULTURAL'],
    'CSE': ['CSE', 'COMPUTER SCIENCE', 'COMPUTER SCIENCE ENGINEERING'],
    'IT': ['IT', 'INFORMATION TECHNOLOGY'],
    'IOT': ['IOT', 'INTERNET OF THINGS'],
    'AIDS': ['AIDS', 'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE'],
    'AIML': ['AIML', 'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING'],
    'CYS': ['CYS', 'CYBERSECURITY'],
    'ECE': ['ECE', 'ELECTRONICS AND COMMUNICATION'],
    'EEE': ['EEE', 'ELECTRICAL AND ELECTRONICS'],
    'MECH': ['MECH', 'MECHANICAL'],
    'BME': ['BME', 'BIOMEDICAL'],
    'BT': ['BT', 'BIOTECHNOLOGY']
}

# -----------------------------
# Academic Years
# -----------------------------
ACADEMIC_YEARS = ['I', 'II', 'III', 'IV']

# -----------------------------
# PostgreSQL Configuration
# -----------------------------
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', '123')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'postgres')
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')

DATABASE_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
