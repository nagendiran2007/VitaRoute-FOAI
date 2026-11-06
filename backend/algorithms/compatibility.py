from config import BLOOD_COMPATIBILITY


def is_blood_compatible(donor_blood, recipient_blood):
    return recipient_blood in BLOOD_COMPATIBILITY.get(donor_blood, [])


def hla_score(donor_hla, recipient_hla):
    if not donor_hla or not recipient_hla:
        return 0.75
    if donor_hla == recipient_hla:
        return 1.0
    shared = 0
    donor_tokens = str(donor_hla).split(',')
    recipient_tokens = str(recipient_hla).split(',')
    for token in donor_tokens:
        if token.strip() in recipient_tokens:
            shared += 1
    if not donor_tokens or not recipient_tokens:
        return 0.5
    return min(1.0, max(0.0, shared / max(len(donor_tokens), len(recipient_tokens))))


def medical_eligible(patient):
    return str(patient.get('medical_eligibility', '')).lower() == 'eligible'


def urgency_weight(level):
    weights = {'Critical': 5, 'High': 4, 'Medium': 3, 'Normal': 2}
    return weights.get(level, 1)
