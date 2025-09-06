// ==========================
// Navigation
// ==========================
document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));
        link.classList.add('active');
        const sectionId = link.getAttribute('data-section');
        document.getElementById(sectionId).classList.add('active');
    });
});

// ==========================
// API Base URL
// ==========================
const API_BASE = 'http://localhost:5000/api';

// ==========================
// File Upload & Listing
// ==========================
async function uploadFiles(inputId, statusId, endpoint, listDivId) {
    const files = document.getElementById(inputId).files;
    const statusDiv = document.getElementById(statusId);
    const listDiv = document.getElementById(listDivId);

    if (!files || files.length === 0) {
        showStatus(statusDiv, 'Please select at least one file', 'error');
        return;
    }

    // Hall file restriction to .xlsx
    if (endpoint === 'halls') {
        for (const file of files) {
            if (!file.name.toLowerCase().endsWith('.xlsx')) {
                showStatus(statusDiv, 'Only Excel (.xlsx) files are allowed for halls', 'error');
                return;
            }
        }
    }

    const formData = new FormData();
    Array.from(files).forEach(file => formData.append('file', file));

    try {
        showStatus(statusDiv, 'Uploading file(s)...', 'info');

        const response = await fetch(`${API_BASE}/upload/${endpoint}`, { method: 'POST', body: formData });
        const data = await response.json();

        if (response.ok) {
            showStatus(statusDiv, 'Upload successful!', 'success');
            fetchUploadedFiles(endpoint, listDivId); // Refresh file list
            updateDashboardStats(); // Refresh dashboard immediately
        } else {
            showStatus(statusDiv, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    }
}

// Upload functions
function uploadStudentFiles() { return uploadFiles('student-files', 'student-upload-status', 'students', 'student-file-list'); }

function uploadHallFile() { return uploadFiles('hall-file', 'hall-upload-status', 'halls', 'hall-file-list'); }

function uploadScheduleFile() { return uploadFiles('schedule-file', 'schedule-upload-status', 'schedule', 'schedule-file-list'); }

// Fetch and display uploaded files
async function fetchUploadedFiles(endpoint, listDivId) {
    const listDiv = document.getElementById(listDivId);
    listDiv.innerHTML = '<p>Loading files...</p>';

    try {
        const res = await fetch(`${API_BASE}/list-${endpoint}`);
        const data = await res.json();

        if (res.ok && Array.isArray(data.files)) {
            listDiv.innerHTML = '';
            if (data.files.length === 0) {
                listDiv.innerHTML = '<p>No files uploaded yet.</p>';
                return;
            }
            data.files.forEach(file => {
                const p = document.createElement('p');
                p.textContent = file;
                listDiv.appendChild(p);
            });
        } else {
            listDiv.innerHTML = `<p>Error fetching files</p>`;
        }
    } catch (error) {
        listDiv.innerHTML = `<p>Error: ${error.message}</p>`;
    }
}

// Initialize file lists on page load
['students', 'halls', 'schedule'].forEach(endpoint => {
    const listDivId = endpoint === 'students' ? 'student-file-list' :
        endpoint === 'halls' ? 'hall-file-list' : 'schedule-file-list';
    fetchUploadedFiles(endpoint, listDivId);
});

// ==========================
// Generate Seating Arrangement
// ==========================
async function generateSeating() {
    const examType = document.getElementById('exam-type').value;
    const sessionType = document.getElementById('session-type').value;
    const resultDiv = document.getElementById('seating-result');
    resultDiv.innerHTML = '';

    try {
        showStatus(resultDiv, 'Generating seating arrangement...', 'info');

        // Backend will pick latest uploaded files automatically
        const response = await fetch(`${API_BASE}/generate-seating`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_files: [],
                hall_file: "",
                schedule_file: "",
                exam_type: examType,
                session_type: sessionType
            })
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(resultDiv, 'Seating arrangement generated successfully!', 'success');
            displaySeatingResult(data.data);

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

// ==========================
// Display Seating Table
// ==========================
function displaySeatingResult(data) {
    const resultDiv = document.getElementById('seating-result');
    const table = document.createElement('table');
    table.className = 'seating-table';

    if (data.length > 0) {
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        Object.keys(data[0]).forEach(key => {
            const th = document.createElement('th');
            th.textContent = key.replace(/_/g, ' ').toUpperCase();
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

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
    } else {
        resultDiv.appendChild(document.createElement('p')).textContent = 'No seating data available.';
    }

    resultDiv.appendChild(table);
}

// ==========================
// Download File
// ==========================
async function downloadFile(filename) {
    try {
        const response = await fetch(`${API_BASE}/download/${filename}`);
        if (!response.ok) throw new Error('Failed to download file');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        alert(`Error downloading file: ${error.message}`);
    }
}

// ==========================
// Update Dashboard Stats
// ==========================
async function updateDashboardStats() {
    try {
        // Get slot report for student counts
        const slotRes = await fetch(`${API_BASE}/slot-report`);
        let slotData = [];
        if (slotRes.ok) {
            const slotJson = await slotRes.json();
            slotData = slotJson.data || [];
        }
        const studentCount = slotData.reduce((acc, row) => acc + (row.count || 0), 0);

        // Get uploaded halls and schedule counts
        const hallCount = await getUploadedCount('halls');
        const examCount = await getUploadedCount('schedule');

        // Update dashboard UI
        document.getElementById('student-count').textContent = studentCount;
        document.getElementById('hall-count').textContent = hallCount;
        document.getElementById('exam-count').textContent = examCount;

    } catch (err) {
        console.error('Error updating dashboard stats:', err);
    }
}

// Helper to get number of uploaded files
async function getUploadedCount(type) {
    try {
        const res = await fetch(`${API_BASE}/list-${type}`);
        if (!res.ok) return 0;
        const data = await res.json();
        return (data.files && data.files.length) || 0;
    } catch {
        return 0;
    }
}

// ==========================
// Status Message Helper
// ==========================
function showStatus(element, message, type) {
    element.innerHTML = '';
    const statusDiv = document.createElement('div');
    statusDiv.textContent = message;
    statusDiv.className = `status-message status-${type}`;
    element.appendChild(statusDiv);
}

// ==========================
// Initialize Dashboard
// ==========================
updateDashboardStats();