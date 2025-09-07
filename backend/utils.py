import os
import pandas as pd
from config import OUTPUT_FOLDER


# -----------------------------
# Excel Export Utility
# -----------------------------
def export_seating_arrangement(df: pd.DataFrame, prefix='seating_arrangement') -> str:
    """
    Save the seating arrangement DataFrame to Excel and return the file path.

    Args:
        df (pd.DataFrame): Seating arrangement DataFrame
        prefix (str): Filename prefix

    Returns:
        str: Full path to the saved Excel file
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{timestamp}.xlsx"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    try:
        df.to_excel(filepath, index=False)
        return filepath
    except Exception as e:
        raise ValueError(f"Failed to export Excel: {e}")


# -----------------------------
# Standardization Utilities
# -----------------------------
def standardize_keys(records: list[dict]) -> list[dict]:
    """
    Standardize keys for a list of dictionaries.
    Converts spaces to underscores and lowercases all keys.

    Args:
        records (list[dict]): List of dictionaries (students, halls, etc.)

    Returns:
        list[dict]: Standardized records
    """
    standardized = []
    for rec in records:
        standardized.append({
            str(k).strip().lower().replace(' ', '_'): v for k, v in rec.items()
        })
    return standardized


# -----------------------------
# File Utilities
# -----------------------------
def save_uploaded_file(file, upload_folder: str, prefix='file') -> str:
    """
    Save an uploaded file to the specified folder with a timestamped filename.

    Args:
        file (werkzeug.FileStorage): Uploaded file
        upload_folder (str): Folder path to save
        prefix (str): Filename prefix

    Returns:
        str: Full path to saved file
    """
    os.makedirs(upload_folder, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else ''
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{timestamp}.{ext}" if ext else f"{prefix}_{timestamp}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath
