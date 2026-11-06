import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / 'frontend'

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-vitaroute-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = os.getenv('DB_NAME', 'vitaroute')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600
    FRONTEND_DIR = str(FRONTEND_DIR)

BLOOD_COMPATIBILITY = {
    'O-': ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'],
    'O+': ['O+', 'A+', 'B+', 'AB+'],
    'A-': ['A-', 'A+', 'AB-', 'AB+'],
    'A+': ['A+', 'AB+'],
    'B-': ['B-', 'B+', 'AB-', 'AB+'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB-', 'AB+'],
    'AB+': ['AB+'],
}

ORGAN_TYPES = ['Kidney', 'Liver', 'Heart', 'Lungs', 'Pancreas', 'Intestine', 'Cornea']
URGENT_LEVELS = ['Critical', 'High', 'Medium', 'Normal']

def get_preservation_window(organ_type):
    durations = {
        'Kidney': 24,
        'Liver': 12,
        'Heart': 6,
        'Lungs': 6,
        'Pancreas': 12,
        'Intestine': 6,
        'Cornea': 24,
    }
    return durations.get(organ_type, 12)
