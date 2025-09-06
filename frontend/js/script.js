// Navigation
document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();

        // Remove active class from all links and sections
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));

        // Add active class to clicked link
        link.classList.add('active');

        // Show corresponding section
        const sectionId = link.getAttribute('data-section');
        document.getElementById(sectionId).classList.add('active');
    });
});

// API Base URL
const API_BASE = 'http://localhost:5000/api';

// Upload student files
async function uploadStudentFiles() {
    const files = document.getElementById('student-files').files;
    const statusDiv = document.getElementById('student-upload-status');

    if (files.length === 0) {
        showStatus(statusDiv, 'Please select at least one file', 'error');
        return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('file', files[i]);
    }

    try {
        showStatus(statusDiv, 'Uploading files...', 'info');

        const response = await fetch(`${API_BASE}/upload/students`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, 'Files uploaded successfully!', 'success');
            updateDashboardStats();
        } else {
            showStatus(statusDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
}

// Upload hall file
async function uploadHallFile() {
    const file = document.getElementById('hall-file').files[0];
    const statusDiv = document.getElementById('hall-upload-status');

    if (!file) {
        showStatus(statusDiv, 'Please select a file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showStatus(statusDiv, 'Uploading file...', 'info');

        const response = await fetch(`${API_BASE}/upload/halls`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, 'File uploaded successfully!', 'success');
            updateDashboardStats();
        } else {
            showStatus(statusDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
}

// Upload schedule file
async function uploadScheduleFile() {
    const file = document.getElementById('schedule-file').files[0];
    const statusDiv = document.getElementById('schedule-upload-status');

    if (!file) {
        showStatus(statusDiv, 'Please select a file', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showStatus(statusDiv, 'Uploading file...', 'info');

        const response = await fetch(`${API_BASE}/upload/schedule`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, 'File uploaded successfully!', 'success');
            updateDashboardStats();
        } else {
            showStatus(statusDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
}

// Generate seating arrangement
async function generateSeating() {
    const examType = document.getElementById('exam-type').value;
    const sessionType = document.getElementById('session-type').value;
    const resultDiv = document.getElementById('seating-result');

    // In a real implementation, we would get the uploaded file paths from the server
    // For this demo, we'll use placeholder data
    const studentFiles = ['frontend/uploads/students_sample.xlsx'];
    const hallFile = 'frontend/uploads/halls_sample.pdf';
    const scheduleFile = 'frontend/uploads/schedule_sample.docx';

    try {
        showStatus(resultDiv, 'Generating seating arrangement...', 'info');

        const response = await fetch(`${API_BASE}/generate-seating`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_files: studentFiles,
                hall_file: hallFile,
                schedule_file: scheduleFile,
                exam_type: examType,
                session_type: sessionType
            })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(resultDiv, 'Seating arrangement generated successfully!', 'success');

            // Display the result in a table
            displaySeatingResult(data.data);

            // Add download button
            const downloadBtn = document.createElement('button');
            downloadBtn.textContent = 'Download Seating Arrangement';
            downloadBtn.onclick = () => downloadFile(data.file);
            resultDiv.appendChild(downloadBtn);
        } else {
            showStatus(resultDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(resultDiv, `Error: ${error.message}`, 'error');
    }
}

// Display seating result in a table
function displaySeatingResult(data) {
    const resultDiv = document.getElementById('seating-result');
    const table = document.createElement('table');

    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    if (data.length > 0) {
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key.replace(/_/g, ' ').toUpperCase();
            headerRow.appendChild(th);
        });
    }

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');

    data.forEach(item => {
        const row = document.createElement('tr');

        Object.values(item).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    resultDiv.appendChild(table);
}

// Generate attendance sheets
async function generateAttendanceSheets() {
    const resultDiv = document.getElementById('report-result');
    showStatus(resultDiv, 'This feature will be implemented in the next version', 'info');
}

// Generate seating report
async function generateSeatingReport() {
    const resultDiv = document.getElementById('report-result');
    showStatus(resultDiv, 'This feature will be implemented in the next version', 'info');
}

// Generate department report
async function generateDepartmentReport() {
    const resultDiv = document.getElementById('report-result');
    showStatus(resultDiv, 'This feature will be implemented in the next version', 'info');
}

// Download file
async function downloadFile(filename) {
    try {
        const response = await fetch(`${API_BASE}/download/${filename}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            alert('Error downloading file');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Update dashboard statistics
async function updateDashboardStats() {
    // In a real implementation, we would fetch these counts from the server
    // For this demo, we'll use placeholder values
    document.getElementById('student-count').textContent = '1250';
    document.getElementById('hall-count').textContent = '45';
    document.getElementById('exam-count').textContent = '18';
}

// Show status message
function showStatus(element, message, type) {
    element.innerHTML = '';
    const statusDiv = document.createElement('div');
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    element.appendChild(statusDiv);
}

// Initialize dashboard
updateDashboardStats();