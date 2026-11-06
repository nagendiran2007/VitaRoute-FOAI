import datetime as dt

from algorithms.compatibility import hla_score, is_blood_compatible, medical_eligible, urgency_weight
from algorithms.distance import estimated_travel_time_km, haversine_km
from algorithms.ac3 import ac3
from algorithms.backtracking import backtracking_solve


def run_matching_engine(db, patient_hospital_id=None):
    hospitals = db.find('hospitals')
    hospitals_by_id = {
        hospital.get('hospital_id') or hospital.get('hospitalId'): hospital
        for hospital in hospitals
        if str(hospital.get('status', '')).lower() == 'approved'
    }
    active_match_statuses = {'pending', 'confirmed', 'approved', 'in progress', 'transportation started'}
    active_matches = [
        match for match in db.find('matches')
        if str(match.get('status', '')).lower() in active_match_statuses
    ]
    assigned_organ_ids = {match.get('organ_id') for match in active_matches}
    assigned_patient_ids = {match.get('patient_id') for match in active_matches}
    available_organs = [
        organ for organ in db.find('organs', {'status': 'Available'})
        if organ.get('organ_id') not in assigned_organ_ids
    ]
    active_requests = db.find('patients', {'status': 'Waiting', 'medical_eligibility': 'Eligible'})
    active_requests = [
        patient for patient in active_requests
        if patient.get('patient_id') not in assigned_patient_ids
    ]
    if patient_hospital_id:
        active_requests = [
            patient for patient in active_requests
            if patient.get('hospital_id') == patient_hospital_id
        ]

    variables = []
    domains = {}
    logs = []
    feasible_matches = []
    candidate_matches = []

    for organ in available_organs:
        hospital = hospitals_by_id.get(organ.get('donor_hospital_id'))
        if hospital is None:
            continue
        candidate_list = []
        for patient in active_requests:
            patient_hospital = hospitals_by_id.get(patient.get('hospital_id'))
            if patient_hospital is None:
                continue
            if patient.get('organ_required') != organ.get('organ_type'):
                continue
            if not medical_eligible(patient):
                continue
            if not is_blood_compatible(organ.get('blood_group'), patient.get('blood_group')):
                continue
            if organ.get('status') != 'Available':
                continue
            if organ.get('expiry_datetime'):
                expiry = dt.datetime.fromisoformat(str(organ['expiry_datetime']))
                if dt.datetime.now() >= expiry:
                    continue
            coordinates = (
                hospital.get('latitude'), hospital.get('longitude'),
                patient_hospital.get('latitude'), patient_hospital.get('longitude'),
            )
            if organ.get('donor_hospital_id') == patient.get('hospital_id'):
                patient_distance = 0.0
                travel_hours = 0.0
            elif all(isinstance(value, (int, float)) for value in coordinates):
                patient_distance = haversine_km(*coordinates)
                travel_hours = estimated_travel_time_km(patient_distance)
            else:
                patient_distance = None
                travel_hours = None
            candidate = {
                'organ_id': organ['organ_id'],
                'patient_id': patient['patient_id'],
                'distance_km': round(patient_distance, 2) if patient_distance is not None else None,
                'travel_hours': round(travel_hours, 2) if travel_hours is not None else None,
                'priority': urgency_weight(patient.get('urgency', 'Normal')),
                'compatibility': round(hla_score(organ.get('hla_code'), patient.get('hla_info')), 2),
            }
            candidate_list.append(candidate)
            candidate_matches.append({
                **candidate,
                'organ_type': organ.get('organ_type'),
                'organ_blood_group': organ.get('blood_group'),
                'patient_name': patient.get('patient_name') or patient.get('name') or patient['patient_id'],
                'patient_blood_group': patient.get('blood_group'),
                'patient_priority': patient.get('urgency', 'Normal'),
                'donor_hospital_id': organ.get('donor_hospital_id'),
                'recipient_hospital_id': patient.get('hospital_id'),
            })
        variables.append(organ['organ_id'])
        domains[organ['organ_id']] = [c['patient_id'] for c in candidate_list]
        if candidate_list:
            logs.append(f"Organ {organ['organ_id']} has {len(candidate_list)} eligible patients")
        else:
            logs.append(f"Organ {organ['organ_id']} has no eligible candidates")

    neighbors = {var: [] for var in variables}
    for i, var1 in enumerate(variables):
        for var2 in variables[i + 1:]:
            neighbors[var1].append(var2)
            neighbors[var2].append(var1)

    reduced_domains, removed_values, pruned = ac3(variables, neighbors, {k: list(v) for k, v in domains.items()})
    for organ_id, candidates in reduced_domains.items():
        if candidates:
            feasible_matches.append({'organ_id': organ_id, 'candidates': candidates})

    assignment, steps, solved = backtracking_solve(variables, reduced_domains, {})
    if not solved:
        assignment = {}

    for organ_id, patient_id in assignment.items():
        feasible_matches.append({'organ_id': organ_id, 'assigned_patient': patient_id})

    return {
        'variables': len(variables),
        'initial_domain_size': sum(len(v) for v in domains.values()),
        'ac3_removed_values': removed_values,
        'remaining_candidates': sum(len(v) for v in reduced_domains.values()),
        'backtracking_steps': steps,
        'valid_assignments': len(assignment),
        'infeasible_assignments': max(0, len(variables) - len(assignment)),
        'final_feasible_matches': feasible_matches,
        'candidate_matches': candidate_matches,
        'logs': logs,
    }
