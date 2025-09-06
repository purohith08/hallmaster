import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Upload configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'frontend', 'uploads')
ALLOWED_EXTENSIONS = {
    'students': {'xlsx'},
    'halls': {'pdf', 'docx'},
    'schedules': {'docx'}
}

# Output configuration
OUTPUT_FOLDER = os.path.join(BASE_DIR, '..', 'outputs')

# Exam slot configuration
EXAM_SLOTS = {
    'I': {'start': '09:30', 'end': '11:00'},
    'II': {'start': '12:00', 'end': '13:30'},
    'III': {'start': '14:30', 'end': '16:00'}
}

# Session types
SESSIONS = {
    'FN': ['I', 'II'],  # Forenoon sessions
    'AN': ['III']       # Afternoon session
}

# Department to slot mapping based on the provided data
DEPT_SLOT_MAPPING = {
    'I': ['CSE', 'IOT', 'IT'],
    'II': ['AIDS'],
    'III': ['AGRI', 'BME', 'BT', 'ECE', 'EEE', 'MECH', 'AIML', 'CYS']
}

# Department mappings (for parsing exam schedules)
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

# Default academic years
ACADEMIC_YEARS = ['I', 'II', 'III', 'IV']