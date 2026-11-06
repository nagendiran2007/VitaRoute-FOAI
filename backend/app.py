import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path

from bson import ObjectId
from flask import Flask, jsonify, redirect, render_template, request, send_file, send_from_directory, session

from algorithms.csp import run_matching_engine
from auth import admin_required, hash_password, hospital_required, login_required, verify_password
from config import Config
from database import DatabaseManager, TAMIL_NADU_DEMO_HOSPITALS
from services.matching_service import create_match_records

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent.parent / 'frontend'))
app.config.from_object(Config)

db = DatabaseManager()
FRONTEND_DIR = Path(__file__).resolve().parent.parent / 'frontend'
PROTECTED_PAGE_PATHS = {
    '/admin-dashboard', '/hospital-dashboard', '/hospitals', '/patients',
    '/organs', '/matching', '/matches', '/transit', '/csp-center',
    '/notifications', '/donor-register', '/patient-register', '/donors',
    '/organ-register',
}
PUBLIC_API_PATHS = {'/api/database-status', '/api/session', '/api/logout'}


@app.before_request
def enforce_database_and_session():
    path = request.path.rstrip('/') or '/'
    protected_page = path in PROTECTED_PAGE_PATHS
    database_api = path.startswith('/api/') and path not in PUBLIC_API_PATHS
    if not protected_page and not database_api:
        return None

    if not db.check_connection():
        session.clear()
        if path.startswith('/api/'):
            return jsonify({'error': 'Database unavailable. Connect MongoDB before signing in or using the dashboard.'}), 503
        return redirect('/login?database=unavailable')

    user = session.get('user')
    if protected_page and not user:
        return redirect('/login')
    if user:
        account = None
        if user.get('role') == 'admin':
            account = db.find_one('admins', {'$or': [
                {'admin_id': user.get('id')},
                {'adminId': user.get('id')},
                {'email': user.get('email')},
            ]})
        elif user.get('role') == 'hospital':
            account = db.find_one('hospitals', {'$or': [
                {'hospital_id': user.get('id')},
                {'hospitalId': user.get('id')},
                {'email': user.get('email')},
            ]})
            if account and str(account.get('status', '')).lower() != 'approved':
                account = None
        if account is None:
            session.clear()
            if path.startswith('/api/'):
                return jsonify({'error': 'Your account is unavailable or not approved. Please sign in again.'}), 401
            return redirect('/login')

    if path == '/admin-dashboard' and user.get('role') != 'admin':
        return redirect('/hospital-dashboard')
    if path == '/hospital-dashboard' and user.get('role') == 'admin':
        return redirect('/admin-dashboard')
    if path == '/csp-center' and user.get('role') != 'admin':
        return redirect('/hospital-dashboard')
    return None


@app.route('/css/<path:filename>')
def frontend_css(filename):
    return send_from_directory(FRONTEND_DIR / 'css', filename)


@app.route('/js/<path:filename>')
def frontend_js(filename):
    return send_from_directory(FRONTEND_DIR / 'js', filename)


@app.route('/assets/<path:filename>')
def frontend_asset(filename):
    return send_from_directory(FRONTEND_DIR / 'assets', filename)


def jsonify_serializable(payload):
    return app.response_class(json.dumps(payload, default=_json_default), mimetype='application/json')


def _json_default(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, set):
        return list(value)
    raise TypeError(f'Object of type {type(value).__name__} is not JSON serializable')


def find_hospital_by_username(username):
    username = (username or '').strip()
    return db.find_one('hospitals', {'username': username}) or db.find_one('hospitals', {'email': username})


def find_admin_by_username(username):
    username = (username or '').strip()
    return (
        db.find_one('admins', {'username': username})
        or db.find_one('admins', {'email': username, 'password': {'$exists': True}})
        or db.find_one('admins', {'email': username, 'password_hash': {'$exists': True}})
        or db.find_one('admins', {'email': username})
    )


def safe_user(user):
    if not user:
        return None
    return {
        'id': user.get('hospital_id') or user.get('hospitalId') or user.get('admin_id') or user.get('adminId'),
        'name': user.get('name') or user.get('hospital_name') or user.get('hospitalName') or user.get('username'),
        'username': user.get('username'),
        'role': user.get('role', 'hospital'),
        'status': user.get('status', 'active'),
    }


@app.route('/')
def index():
    return redirect('/loading')


@app.route('/loading')
def loading_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'loading.html'))


@app.route('/login')
def login_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'login.html'))


@app.route('/register-hospital')
def register_hospital_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'hospital-register.html'))


@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user' not in session:
        return redirect('/login')
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'admin-dashboard.html'))


@app.route('/hospital-dashboard')
def hospital_dashboard():
    if 'user' not in session:
        return redirect('/login')
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'hospital-dashboard.html'))


@app.route('/hospitals')
def hospitals_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'hospitals.html'))


@app.route('/patients')
def patients_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'patients.html'))


@app.route('/organs')
def organs_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'organs.html'))


@app.route('/matching')
def matching_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'matching.html'))


@app.route('/matches')
def matches_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'matches.html'))


@app.route('/transit')
def transit_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'transit.html'))


@app.route('/csp-center')
def csp_center_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'csp-center.html'))


@app.route('/notifications')
def notifications_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'notifications.html'))


@app.route('/donor-register')
def donor_register_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'donor-register.html'))


@app.route('/patient-register')
def patient_register_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'patient-register.html'))


@app.route('/donors')
def donors_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'donors.html'))


@app.route('/organ-register')
def organ_register_page():
    return send_file(str(Path(__file__).resolve().parent.parent / 'frontend' / 'organ-register.html'))


@app.route('/api/session')
def api_session():
    connected = db.check_connection()
    if not connected:
        session.clear()
    return jsonify({'user': session.get('user'), 'database_connected': connected})

@app.route('/api/database-status')
def api_database_status():
    connected = db.check_connection()
    return jsonify({
        'connected': connected,
        'message': 'Database connected.' if connected else 'Database unavailable. Sign-in is disabled until MongoDB is connected.',
    }), 200 if connected else 503

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or data.get('username') or '').strip().lower()
    password = data.get('password') or ''
    user = find_admin_by_username(email)
    if user is None:
        user = find_hospital_by_username(email)
        if user is None:
            return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401
        if str(user.get('status', '')).lower() != 'approved':
            return jsonify({'success': False, 'message': 'This hospital account is not approved yet.'}), 403
        role = 'hospital'
    else:
        role = 'admin'
    if not verify_password(user.get('password', ''), password):
        return jsonify({'success': False, 'message': 'Invalid username or password.'}), 401
    session['user'] = {
        'id': user.get('hospital_id') or user.get('hospitalId') or user.get('admin_id') or user.get('adminId'),
        'name': user.get('name') or user.get('contact_person') or user.get('hospitalName') or user.get('username'),
        'username': user.get('username') or user.get('email'),
        'email': user.get('email'),
        'role': role,
    }
    return jsonify({'success': True, 'redirect': '/admin-dashboard' if role == 'admin' else '/hospital-dashboard', 'user': session['user']})


@app.route('/api/register-hospital', methods=['POST'])
def api_register_hospital():
    data = request.get_json(silent=True) or {}
    required = ['hospital_name', 'hospital_registration_id', 'hospital_type', 'email', 'username', 'password', 'contact_person', 'contact_number', 'address', 'city', 'state', 'pin_code']
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({'success': False, 'message': f'Missing required fields: {", ".join(missing)}'}), 400
    if data['password'] != data.get('confirm_password'):
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400
    if db.find_one('hospitals', {'username': data['username']}):
        return jsonify({'success': False, 'message': 'Username already registered.'}), 400
    hospital = {
        'hospital_id': data.get('hospital_registration_id') or f"HOSP-{len(db.find('hospitals')) + 1001}",
        'name': data['hospital_name'],
        'hospital_type': data['hospital_type'],
        'email': data['email'],
        'username': data['username'],
        'password': hash_password(data['password']),
        'contact_person': data['contact_person'],
        'contact_number': data['contact_number'],
        'address': data['address'],
        'city': data['city'],
        'district': data.get('district', 'Pending'),
        'state': data['state'],
        'pin_code': data['pin_code'],
        'latitude': float(data.get('latitude', 0)),
        'longitude': float(data.get('longitude', 0)),
        'status': 'Pending',
        'role': 'hospital',
    }
    db.insert('hospitals', hospital)
    return jsonify({'success': True, 'message': 'Hospital registration submitted for approval.'})


@app.route('/api/admin/overview')
@admin_required
def admin_overview():
    summary = db.get_summary()
    return jsonify_serializable(summary)


@app.route('/api/hospital/overview')
@hospital_required
def hospital_overview():
    user = session.get('user', {})
    hospital_id = user.get('id')
    if hospital_id is None:
        return jsonify({'error': 'No hospital found'}), 400
    patients = db.find('patients', {'hospital_id': hospital_id})
    organs = db.find('organs', {'donor_hospital_id': hospital_id})
    return jsonify_serializable({
        'total_donors': len(db.find('donors', {'hospital_id': hospital_id})),
        'total_patients': len(patients),
        'donated_organs': len(organs),
        'required_organs': len([p for p in patients if p.get('organ_required')]),
        'available_organs': len([o for o in organs if o.get('status') == 'Available']),
        'incoming_matches': len(db.find('matches', {'recipient_hospital_id': hospital_id})),
        'outgoing_matches': len(db.find('matches', {'donor_hospital_id': hospital_id})),
        'successful_matches': len(db.find('matches', {'recipient_hospital_id': hospital_id, 'status': 'Confirmed'})),
    })


@app.route('/api/register-donor', methods=['POST'])
@hospital_required
def api_register_donor():
    data = request.get_json(silent=True) or {}
    user = session.get('user', {})
    required = ['donor_name', 'age', 'gender', 'contact_number', 'address', 'blood_group', 'organ_type', 'consent_status']
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing)}'}), 400
    donor_id = data.get('donor_id') or f"DON-{uuid.uuid4().hex[:8].upper()}"
    donor = {
        'donor_id': donor_id,
        'donor_name': data['donor_name'],
        'age': int(data.get('age', 0)),
        'gender': data['gender'],
        'contact_number': data['contact_number'],
        'address': data['address'],
        'blood_group': data['blood_group'],
        'organ_type': data['organ_type'],
        'consent_status': data['consent_status'],
        'hospital_id': user.get('id'),
        'status': 'Pending',
    }
    db.insert('donors', donor)
    return jsonify({'success': True, 'message': 'Donor registered successfully.', 'donor_id': donor_id})


@app.route('/api/donors')
@hospital_required
def donors_list():
    user = session.get('user', {})
    query = {} if user.get('role') == 'admin' else {'hospital_id': user.get('id')}
    demo_names = {email: name for name, email, _city in TAMIL_NADU_DEMO_HOSPITALS}
    hospitals = {
        hospital.get('hospital_id') or hospital.get('hospitalId'): demo_names.get(
            hospital.get('email'), hospital.get('name') or hospital.get('hospitalName', 'Hospital')
        )
        for hospital in db.find('hospitals')
    }
    donors = db.find('donors', query)
    for donor in donors:
        donor['hospital_name'] = hospitals.get(donor.get('hospital_id'), 'Hospital')
    return jsonify_serializable(donors)


@app.route('/api/register-organ', methods=['POST'])
@hospital_required
def api_register_organ():
    data = request.get_json(silent=True) or {}
    user = session.get('user', {})
    required = ['donor_id', 'organ_type', 'blood_group', 'consent', 'condition', 'expiry_datetime']
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing)}'}), 400

    hospital_id = user.get('id')
    donor = db.find_one('donors', {'donor_id': data['donor_id'], 'hospital_id': hospital_id})
    if donor is None:
        return jsonify({'success': False, 'message': 'Select a donor registered at your hospital.'}), 400
    try:
        expiry = datetime.fromisoformat(data['expiry_datetime'])
        if expiry <= datetime.now():
            return jsonify({'success': False, 'message': 'Expiry must be a future date and time.'}), 400
        viability = int(data.get('viability', 0))
        if not 0 <= viability <= 100:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Enter a valid future expiry and viability from 0 to 100.'}), 400

    organ_id = f"ORG-{uuid.uuid4().hex[:8].upper()}"
    organ = {
        'organ_id': organ_id,
        'donor_id': donor['donor_id'],
        'organ_type': data['organ_type'],
        'blood_group': data['blood_group'],
        'condition': data['condition'],
        'consent': data['consent'],
        'viability': viability,
        'donor_hospital_id': hospital_id,
        'expiry_datetime': expiry.isoformat(),
        'hla_code': data.get('hla_code', ''),
        'status': 'Available' if data['consent'] == 'Confirmed' and data.get('medical_approval') == 'Approved' else 'Pending Approval',
        'medical_approval': data.get('medical_approval', 'Pending'),
        'preservation_method': data.get('preservation_method', ''),
    }
    db.insert('organs', organ)
    return jsonify({
        'success': True,
        'message': 'Organ registered successfully.' if organ['status'] == 'Available' else 'Organ recorded and pending medical approval.',
        'organ_id': organ_id,
        'status': organ['status'],
    })


@app.route('/api/register-patient', methods=['POST'])
@hospital_required
def api_register_patient():
    data = request.get_json(silent=True) or {}
    user = session.get('user', {})
    required = ['patient_name', 'age', 'gender', 'blood_group', 'organ_required', 'urgency', 'medical_eligibility']
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({'success': False, 'message': f'Missing fields: {", ".join(missing)}'}), 400
    patient_id = data.get('patient_id') or f"PAT-{uuid.uuid4().hex[:8].upper()}"
    patient = {
        'patient_id': patient_id,
        'patient_name': data['patient_name'],
        'age': int(data.get('age', 0)),
        'gender': data['gender'],
        'blood_group': data['blood_group'],
        'organ_required': data['organ_required'],
        'urgency': data['urgency'],
        'medical_eligibility': data['medical_eligibility'],
        'hospital_id': user.get('id'),
        'status': 'Waiting',
        'contact': data.get('contact', ''),
    }
    db.insert('patients', patient)
    return jsonify({'success': True, 'message': 'Patient registered successfully.', 'patient_id': patient_id})


@app.route('/api/hospitals')
@hospital_required
def hospital_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        hospitals = db.find('hospitals')
    else:
        hospitals = db.find('hospitals', {'$or': [
            {'hospital_id': user.get('id')},
            {'hospitalId': user.get('id')},
        ]})
    for hospital in hospitals:
        hospital.pop('password', None)
        hospital.pop('password_hash', None)
    return jsonify_serializable(hospitals)


@app.route('/api/patients')
@hospital_required
def patients_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        items = db.find('patients')
    else:
        items = db.find('patients', {'hospital_id': user.get('id')})
    return jsonify_serializable(items)


@app.route('/api/organs')
@hospital_required
def organs_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        items = db.find('organs')
    else:
        items = db.find('organs', {'donor_hospital_id': user.get('id')})
    demo_names = {email: name for name, email, _city in TAMIL_NADU_DEMO_HOSPITALS}
    hospitals = {
        hospital.get('hospital_id') or hospital.get('hospitalId'): demo_names.get(
            hospital.get('email'), hospital.get('name') or hospital.get('hospitalName', 'Hospital')
        )
        for hospital in db.find('hospitals')
    }
    for organ in items:
        organ['donor_hospital_name'] = hospitals.get(organ.get('donor_hospital_id'), 'Hospital')
    return jsonify_serializable(items)


@app.route('/api/matches')
@hospital_required
def matches_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        items = db.find('matches')
    else:
        items = db.find('matches', {'$or': [{'donor_hospital_id': user.get('id')}, {'recipient_hospital_id': user.get('id')}]})
    demo_names = {email: name for name, email, _city in TAMIL_NADU_DEMO_HOSPITALS}
    hospitals = {
        hospital.get('hospital_id') or hospital.get('hospitalId'): demo_names.get(
            hospital.get('email'), hospital.get('name') or hospital.get('hospitalName', 'Hospital')
        )
        for hospital in db.find('hospitals')
    }
    patients = {patient.get('patient_id'): patient for patient in db.find('patients')}
    for match in items:
        match['donor_hospital_name'] = hospitals.get(match.get('donor_hospital_id'), 'Hospital')
        match['recipient_hospital_name'] = hospitals.get(match.get('recipient_hospital_id'), 'Hospital')
        patient = patients.get(match.get('patient_id'), {})
        match['patient_name'] = patient.get('patient_name', 'Patient')
        match['patient_priority'] = match.get('patient_priority') or patient.get('urgency', 'Normal')
    return jsonify_serializable(items)


@app.route('/api/notifications')
@hospital_required
def notifications_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        items = db.find('notifications')
    else:
        items = db.find('notifications', {'$or': [{'donor_hospital_id': user.get('id')}, {'recipient_hospital_id': user.get('id')}]})
    return jsonify_serializable(items)


@app.route('/api/transit')
@hospital_required
def transit_list():
    user = session.get('user', {})
    if user.get('role') == 'admin':
        items = db.find('transport_records')
    else:
        items = db.find('transport_records', {'$or': [{'donor_hospital_id': user.get('id')}, {'recipient_hospital_id': user.get('id')}]})
    demo_names = {email: name for name, email, _city in TAMIL_NADU_DEMO_HOSPITALS}
    hospitals = {
        hospital.get('hospital_id') or hospital.get('hospitalId'): demo_names.get(
            hospital.get('email'), hospital.get('name') or hospital.get('hospitalName', 'Hospital')
        )
        for hospital in db.find('hospitals')
    }
    organ_types = {organ.get('organ_id'): organ.get('organ_type') for organ in db.find('organs')}
    for transport in items:
        transport['donor_hospital_name'] = hospitals.get(transport.get('donor_hospital_id'), 'Hospital')
        transport['recipient_hospital_name'] = hospitals.get(transport.get('recipient_hospital_id'), 'Hospital')
        transport['organ_type'] = transport.get('organ_type') or organ_types.get(transport.get('organ_id'), 'Organ')
    return jsonify_serializable(items)


@app.route('/api/csp')
@admin_required
def csp_stats():
    metrics = run_matching_engine(db)
    return jsonify_serializable(metrics)


@app.route('/api/matches/run', methods=['POST'])
@hospital_required
def run_matching():
    user = session.get('user', {})
    patient_hospital_id = None if user.get('role') == 'admin' else user.get('id')
    created = create_match_records(db, patient_hospital_id=patient_hospital_id)
    metrics = run_matching_engine(db, patient_hospital_id=patient_hospital_id)
    alternatives = db.find('matches', {
        'demo_record': True,
        'status': 'Alternative Candidate',
    })
    if user.get('role') != 'admin':
        alternatives = [
            match for match in alternatives
            if patient_hospital_id in {
                match.get('donor_hospital_id'),
                match.get('recipient_hospital_id'),
            }
        ]
    hospitals_by_id = {
        hospital.get('hospital_id') or hospital.get('hospitalId'):
            next(
                (name for name, email, _city in TAMIL_NADU_DEMO_HOSPITALS if email == hospital.get('email')),
                hospital.get('name') or hospital.get('hospitalName', 'Hospital'),
            )
        for hospital in db.find('hospitals')
    }
    patients_by_id = {patient.get('patient_id'): patient for patient in db.find('patients')}
    for match in alternatives:
        patient = patients_by_id.get(match.get('patient_id'), {})
        match['patient_name'] = patient.get('patient_name') or patient.get('name') or match.get('patient_id')
        match['patient_blood_group'] = patient.get('blood_group')
        match['donor_hospital_name'] = hospitals_by_id.get(match.get('donor_hospital_id'), 'Hospital')
        match['recipient_hospital_name'] = hospitals_by_id.get(match.get('recipient_hospital_id'), 'Hospital')
    return jsonify_serializable({
        'success': True,
        'matches': created,
        'alternatives': alternatives,
        'metrics': metrics,
    })


if __name__ == '__main__':
    os.makedirs(Config.FRONTEND_DIR, exist_ok=True)
    port = int(os.getenv('PORT', '5001'))
    app.run(debug=True, host='0.0.0.0', port=port)
