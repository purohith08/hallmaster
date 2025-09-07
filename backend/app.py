from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd

# ----------------------------- #
# Internal Modules
# ----------------------------- #
from generate_seating_arrangement import (
    generate_seating_arrangement,
    generate_slot_report,
    validate_student_slot_assignment
)
from data_processor import process_student_data, process_hall_data, process_schedule_data
from utils import export_seating_arrangement, standardize_keys
from config import UPLOAD_FOLDER, OUTPUT_FOLDER, ALLOWED_EXTENSIONS, DEPT_SLOT_MAPPING

# ----------------------------- #
# Flask Setup
# ----------------------------- #
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB


# ----------------------------- #
# File Upload
# ----------------------------- #
@app.route('/api/upload/<file_type>', methods=['POST'])
def upload_file(file_type):
    allowed_ext = ALLOWED_EXTENSIONS.get(file_type)
    if not allowed_ext:
        return jsonify({'error': 'Unknown file type'}), 400
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_ext:
        filepath = save_file(file, file_type)
        try:
            if file_type == 'students':
                data = process_student_data(filepath)
            elif file_type == 'halls':
                data = process_hall_data(filepath)
            elif file_type == 'schedules':
                data = process_schedule_data(filepath)
            else:
                data = None
            return jsonify({
                'message': 'File uploaded successfully',
                'data': standardize_keys(data) if file_type == 'students' else data
            })
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    return jsonify({'error': 'Invalid file type'}), 400


# ----------------------------- #
# List Uploaded Files
# ----------------------------- #
@app.route('/api/list/<file_type>', methods=['GET'])
def list_files(file_type):
    prefix_map = {'students': 'students_', 'halls': 'halls_', 'schedules': 'schedule_'}
    prefix = prefix_map.get(file_type)
    if not prefix:
        return jsonify({'error': 'Unknown file type'}), 400
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(prefix)]
    files.sort()
    return jsonify({'files': files})


# ----------------------------- #
# Generate Seating Arrangement
# ----------------------------- #
@app.route('/api/generate-seating', methods=['POST'])
def generate_seating():
    try:
        data = request.json or {}
        student_files = data.get('student_files', []) or get_latest_files('students_')
        hall_file_list = get_latest_files('halls_')
        schedule_file_list = get_latest_files('schedule_')

        if not student_files or not hall_file_list or not schedule_file_list:
            return jsonify({'error': 'Required files are missing'}), 400

        hall_file = data.get('hall_file') or hall_file_list[0]
        schedule_file = data.get('schedule_file') or schedule_file_list[0]
        exam_type = data.get('exam_type', 'Internal')

        # Load students
        all_students = []
        for f in student_files:
            students = process_student_data(f)
            all_students.extend(standardize_keys(students))

        # Load halls & schedule
        halls = process_hall_data(hall_file)
        schedule = process_schedule_data(schedule_file)

        # Generate arrangement
        arrangement_df = generate_seating_arrangement(all_students, halls, schedule, exam_type, session_type=None)
        output_file = export_seating_arrangement(arrangement_df)

        return jsonify({
            'message': 'Seating arrangement generated successfully',
            'file': output_file,
            'data': arrangement_df.to_dict('records')
        })

    except Exception as e:
        return jsonify({'error': f'Error generating seating arrangement: {str(e)}'}), 500


# ----------------------------- #
# Slot Report
# ----------------------------- #
@app.route('/api/slot-report', methods=['GET'])
def slot_report():
    try:
        student_files = get_latest_files('students_')
        if not student_files:
            return jsonify({'error': 'No student data found'}), 400

        all_students = []
        for f in student_files:
            students = process_student_data(f)
            all_students.extend(standardize_keys(students))

        report = generate_slot_report(pd.DataFrame(all_students))
        return jsonify({
            'message': 'Slot report generated',
            'data': report.to_dict('records'),
            'slot_mapping': DEPT_SLOT_MAPPING
        })
    except Exception as e:
        return jsonify({'error': f'Error generating slot report: {str(e)}'}), 500


# ----------------------------- #
# Validate Assignments
# ----------------------------- #
@app.route('/api/validate-assignments', methods=['GET'])
def validate_assignments():
    try:
        student_files = get_latest_files('students_')
        if not student_files:
            return jsonify({'error': 'No student data found'}), 400

        all_students = []
        for f in student_files:
            students = process_student_data(f)
            all_students.extend(standardize_keys(students))

        invalid_assignments = validate_student_slot_assignment(pd.DataFrame(all_students))
        return jsonify({
            'message': 'Validation completed',
            'invalid_assignments': invalid_assignments,
            'total_students': len(all_students),
            'invalid_count': len(invalid_assignments)
        })
    except Exception as e:
        return jsonify({'error': f'Error validating assignments: {str(e)}'}), 500


# ----------------------------- #
# Download File
# ----------------------------- #
@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


# ----------------------------- #
# Helper Functions
# ----------------------------- #
def save_file(file, prefix):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filename = f"{prefix}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.',1)[-1]}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath

def get_latest_files(prefix):
    files = [os.path.join(app.config['UPLOAD_FOLDER'], f)
             for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(prefix)]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


# ----------------------------- #
# Main
# ----------------------------- #
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)
