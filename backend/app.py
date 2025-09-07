from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
import json

# Internal modules
from data_processor import process_student_data, process_hall_data, process_schedule_data
from seating_algorithm import (
    generate_seating_arrangement,
    generate_slot_report,
    validate_student_slot_assignment
)
from config import UPLOAD_FOLDER, OUTPUT_FOLDER, ALLOWED_EXTENSIONS, DEPT_SLOT_MAPPING

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit


# -----------------------------
# File Upload APIs
# -----------------------------
@app.route('/api/upload/students', methods=['POST'])
def upload_students():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename, {'xlsx'}):
        filename = f"students_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            student_data = process_student_data(filepath)

            # ✅ Standardize keys for consistency
            standardized = []
            for s in student_data:
                new_s = {k.strip().lower().replace(" ", "_"): v for k, v in s.items()}
                standardized.append(new_s)

            return jsonify({'message': 'File uploaded successfully', 'data': standardized})
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/upload/halls', methods=['POST'])
def upload_halls():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename, {'xlsx'}):
        filename = f"halls_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            hall_data = process_hall_data(filepath)
            return jsonify({'message': 'File uploaded successfully', 'data': hall_data})
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type. Please upload an Excel (.xlsx) file'}), 400


@app.route('/api/upload/schedule', methods=['POST'])
def upload_schedule():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename, {'docx'}):
        filename = f"schedule_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            schedule_data = process_schedule_data(filepath)
            return jsonify({'message': 'File uploaded successfully', 'data': schedule_data})
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file type'}), 400


# -----------------------------
# List Uploaded Files APIs
# -----------------------------
@app.route('/api/list-students', methods=['GET'])
def list_students():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('students_')]
    return jsonify({'files': files})


@app.route('/api/list-halls', methods=['GET'])
def list_halls():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('halls_')]
    return jsonify({'files': files})


@app.route('/api/list-schedule', methods=['GET'])
def list_schedule():
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('schedule_')]
    return jsonify({'files': files})


# -----------------------------
# Seating Arrangement
# -----------------------------
@app.route('/api/generate-seating', methods=['POST'])
def generate_seating():
    data = request.json
    student_files = data.get('student_files', [])
    hall_file = data.get('hall_file')
    schedule_file = data.get('schedule_file')
    exam_type = data.get('exam_type', 'Internal')
    session_type = data.get('session_type', 'FN')  # ✅ Added for new algorithm

    try:
        # Use latest uploaded files if none provided
        if not student_files:
            student_files = sorted(
                [os.path.join(app.config['UPLOAD_FOLDER'], f)
                 for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('students_')],
                key=os.path.getmtime,
                reverse=True
            )
        if not hall_file:
            halls = sorted(
                [os.path.join(app.config['UPLOAD_FOLDER'], f)
                 for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('halls_')],
                key=os.path.getmtime,
                reverse=True
            )
            hall_file = halls[0] if halls else None
        if not schedule_file:
            schedules = sorted(
                [os.path.join(app.config['UPLOAD_FOLDER'], f)
                 for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('schedule_')],
                key=os.path.getmtime,
                reverse=True
            )
            schedule_file = schedules[0] if schedules else None

        if not student_files or not hall_file or not schedule_file:
            return jsonify({'error': 'Required files are missing'}), 400

        all_students = []
        for file_path in student_files:
            students = process_student_data(file_path)

            # ✅ Standardize keys
            for s in students:
                standardized = {k.strip().lower().replace(" ", "_"): v for k, v in s.items()}
                all_students.append(standardized)

        halls = process_hall_data(hall_file)
        schedule = process_schedule_data(schedule_file)

        result = generate_seating_arrangement(all_students, halls, schedule, exam_type, session_type)

        output_file = os.path.join(
            OUTPUT_FOLDER,
            f'seating_arrangement_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        result.to_excel(output_file, index=False)

        return jsonify({
            'message': 'Seating arrangement generated successfully',
            'file': output_file,
            'data': result.to_dict('records')
        })
    except Exception as e:
        return jsonify({'error': f'Error generating seating arrangement: {str(e)}'}), 500


# -----------------------------
# Reports & Validation
# -----------------------------
@app.route('/api/slot-report', methods=['GET'])
def get_slot_report():
    try:
        student_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('students_')]
        if not student_files:
            return jsonify({'error': 'No student data found'}), 400

        all_students = []
        for filename in student_files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            students = process_student_data(filepath)

            # ✅ Standardize keys
            for s in students:
                standardized = {k.strip().lower().replace(" ", "_"): v for k, v in s.items()}
                all_students.append(standardized)

        students_df = pd.DataFrame(all_students)
        report = generate_slot_report(students_df)

        return jsonify({
            'message': 'Slot report generated successfully',
            'data': report.to_dict('records'),
            'slot_mapping': DEPT_SLOT_MAPPING
        })
    except Exception as e:
        return jsonify({'error': f'Error generating slot report: {str(e)}'}), 500


@app.route('/api/validate-assignments', methods=['GET'])
def validate_assignments():
    try:
        student_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith('students_')]
        if not student_files:
            return jsonify({'error': 'No student data found'}), 400

        all_students = []
        for filename in student_files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            students = process_student_data(filepath)

            # ✅ Standardize keys
            for s in students:
                standardized = {k.strip().lower().replace(" ", "_"): v for k, v in s.items()}
                all_students.append(standardized)

        students_df = pd.DataFrame(all_students)
        invalid_assignments = validate_student_slot_assignment(students_df)

        return jsonify({
            'message': 'Validation completed',
            'invalid_assignments': invalid_assignments,
            'total_students': len(students_df),
            'invalid_count': len(invalid_assignments)
        })
    except Exception as e:
        return jsonify({'error': f'Error validating assignments: {str(e)}'}), 500


# -----------------------------
# File Download
# -----------------------------
@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


# -----------------------------
# Helper
# -----------------------------
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# -----------------------------
# Main
# -----------------------------
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, port=5000)
