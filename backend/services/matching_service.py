import datetime as dt
import uuid

from algorithms.csp import run_matching_engine


def create_match_records(db, patient_hospital_id=None):
    results = run_matching_engine(db, patient_hospital_id=patient_hospital_id)
    created = []
    candidates = sorted(
        results.get('candidate_matches', []),
        key=lambda item: (
            -item.get('priority', 0),
            -item.get('compatibility', 0),
            item.get('distance_km') if item.get('distance_km') is not None else float('inf'),
        ),
    )
    assigned_organs = set()
    assigned_patients = set()
    for item in candidates:
        organ_id = item['organ_id']
        patient_id = item['patient_id']
        if organ_id in assigned_organs or patient_id in assigned_patients:
            continue
        organ = db.find_one('organs', {'organ_id': organ_id, 'status': 'Available'})
        patient = db.find_one('patients', {'patient_id': patient_id, 'status': 'Waiting'})
        if organ is None or patient is None:
            continue
        match_id = f"MATCH-{uuid.uuid4().hex[:8].upper()}"
        created_at = dt.datetime.utcnow().isoformat()
        record = {
            'match_id': match_id,
            'organ_id': organ_id,
            'organ_type': organ.get('organ_type'),
            'donor_hospital_id': organ.get('donor_hospital_id'),
            'recipient_hospital_id': patient.get('hospital_id'),
            'patient_id': patient_id,
            'patient_name': patient.get('patient_name') or patient.get('name') or patient_id,
            'patient_blood_group': patient.get('blood_group'),
            'patient_priority': patient.get('urgency', 'Normal'),
            'donor_id': organ.get('donor_id'),
            'compatibility': 'Compatible; sample algorithm result',
            'compatibility_score': item.get('compatibility'),
            'distance_km': item.get('distance_km'),
            'travel_time_hours': item.get('travel_hours'),
            'remaining_expiry_hours': max(
                0,
                (dt.datetime.fromisoformat(str(organ['expiry_datetime'])) - dt.datetime.utcnow()).total_seconds() / 3600,
            ) if organ.get('expiry_datetime') else None,
            'status': 'Pending',
            'created_at': created_at,
        }
        db.insert('matches', record)

        notification = {
            'notification_id': f"NOTIF-{uuid.uuid4().hex[:8].upper()}",
            'match_id': match_id,
            'donor_hospital_id': organ.get('donor_hospital_id'),
            'recipient_hospital_id': patient.get('hospital_id'),
            'message': f"New match for {organ.get('organ_type')} organ to patient {patient_id}",
            'status': 'Pending',
            'type': 'Match',
            'created_at': created_at,
        }
        db.insert('notifications', notification)

        transport = {
            'transport_id': f"TRANS-{uuid.uuid4().hex[:8].upper()}",
            'match_id': match_id,
            'organ_id': organ_id,
            'organ_type': organ.get('organ_type'),
            'donor_hospital_id': organ.get('donor_hospital_id'),
            'recipient_hospital_id': patient.get('hospital_id'),
            'status': 'Scheduled',
            'distance_km': item.get('distance_km'),
            'travel_time_hours': item.get('travel_hours'),
            'estimated_arrival': (
                dt.datetime.utcnow() + dt.timedelta(hours=item['travel_hours'])
            ).isoformat() if item.get('travel_hours') is not None else None,
            'expiry_deadline': organ.get('expiry_datetime'),
            'demo_record': bool(organ.get('demo_record') or patient.get('demo_record')),
        }
        db.insert('transport_records', transport)

        db.update_one('organs', {'organ_id': organ_id}, {'status': 'Reserved'})
        assigned_organs.add(organ_id)
        assigned_patients.add(patient_id)
        created.append(record)
    return created
