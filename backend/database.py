import copy
import datetime as dt
from typing import Any, Dict, List

from pymongo import MongoClient

from auth import hash_password
from config import Config

DEFAULT_PASSWORD_HASH = hash_password('Admin@123')
DEMO_TN_PASSWORD = 'TNVita@123'
TAMIL_NADU_DEMO_HOSPITALS = [
    ('Apollo Hospitals Chennai', 'apollo@gmail.com', 'Chennai'),
    ('MIOT International', 'miot.demo@vitaroute.example', 'Chennai'),
    ('Kauvery Hospital Chennai', 'kauvery.demo@vitaroute.example', 'Chennai'),
    ('MGM Healthcare', 'mgm.demo@vitaroute.example', 'Chennai'),
    ('Fortis Malar Hospital', 'fortis.malar.demo@vitaroute.example', 'Chennai'),
    ('Sri Ramachandra Medical Centre', 'srmc.demo@vitaroute.example', 'Chennai'),
    ('Christian Medical College Vellore', 'cmc.vellore.demo@vitaroute.example', 'Vellore'),
    ('PSG Hospitals', 'psg.demo@vitaroute.example', 'Coimbatore'),
    ('Kovai Medical Center and Hospital', 'kmch.demo@vitaroute.example', 'Coimbatore'),
    ('Meenakshi Mission Hospital', 'mmh.demo@vitaroute.example', 'Madurai'),
    ('Government Rajaji Hospital', 'rajaji.demo@vitaroute.example', 'Madurai'),
    ('Tirunelveli Medical College Hospital', 'tirunelveli.demo@vitaroute.example', 'Tirunelveli'),
    ('Thanjavur Medical College Hospital', 'thanjavur.demo@vitaroute.example', 'Thanjavur'),
    ('Government Mohan Kumaramangalam Medical College Hospital', 'salem.demo@vitaroute.example', 'Salem'),
    ('Government Erode Medical College Hospital', 'erode.demo@vitaroute.example', 'Perundurai'),
    ('Kanyakumari Government Medical College Hospital', 'kanyakumari.demo@vitaroute.example', 'Asaripallam'),
    ('Government Villupuram Medical College Hospital', 'villupuram.demo@vitaroute.example', 'Villupuram'),
    ('Government Dharmapuri Medical College Hospital', 'dharmapuri.demo@vitaroute.example', 'Dharmapuri'),
    ('Dindigul Medical College Hospital', 'dindigul.demo@vitaroute.example', 'Dindigul'),
    ('Government Sivagangai Medical College Hospital', 'sivagangai.demo@vitaroute.example', 'Sivaganga'),
]
TAMIL_NADU_DEMO_HOSPITAL_DETAILS = {
    'rajaji.demo@vitaroute.example': {
        'address': 'Panagal Road', 'district': 'Madurai', 'pin_code': '625020',
        'hospital_type': 'Government multi-specialty', 'contact_person': 'Demo Hospital Administrator',
    },
    'tirunelveli.demo@vitaroute.example': {
        'address': 'High Ground Road', 'district': 'Tirunelveli', 'pin_code': '627011',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'thanjavur.demo@vitaroute.example': {
        'address': 'Medical College Road', 'district': 'Thanjavur', 'pin_code': '613004',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'salem.demo@vitaroute.example': {
        'address': 'Salem Medical College Road', 'district': 'Salem', 'pin_code': '636030',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'erode.demo@vitaroute.example': {
        'address': 'Perundurai Road', 'district': 'Erode', 'pin_code': '638053',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'kanyakumari.demo@vitaroute.example': {
        'address': 'Asaripallam', 'district': 'Kanyakumari', 'pin_code': '629201',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'villupuram.demo@vitaroute.example': {
        'address': 'Mundiyampakkam', 'district': 'Villupuram', 'pin_code': '605601',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'dharmapuri.demo@vitaroute.example': {
        'address': 'Nethaji Bye-pass Road', 'district': 'Dharmapuri', 'pin_code': '636701',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'dindigul.demo@vitaroute.example': {
        'address': 'Adiyanuthu', 'district': 'Dindigul', 'pin_code': '624003',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
    'sivagangai.demo@vitaroute.example': {
        'address': 'Vaniyangudi', 'district': 'Sivaganga', 'pin_code': '630561',
        'hospital_type': 'Government teaching hospital', 'contact_person': 'Demo Hospital Administrator',
    },
}


class DatabaseManager:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.memory = {
            'admins': [],
            'hospitals': [],
            'donors': [],
            'patients': [],
            'organs': [],
            'organ_requests': [],
            'matches': [],
            'notifications': [],
            'transport_records': [],
            'transplant_records': [],
            'audit_logs': [],
        }
        self._connect()
        self._seed_demo_data()

    def _connect(self):
        try:
            self.mongo_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
            self.mongo_db = self.mongo_client[Config.DB_NAME]
            self.mongo_client.admin.command('ping')
        except Exception:
            if self.mongo_client is not None:
                self.mongo_client.close()
            self.mongo_client = None
            self.mongo_db = None

    def check_connection(self) -> bool:
        if self.mongo_client is None or self.mongo_db is None:
            self._connect()
        if self.mongo_client is None or self.mongo_db is None:
            return False
        try:
            self.mongo_client.admin.command('ping')
            return True
        except Exception:
            self.mongo_client = None
            self.mongo_db = None
            return False

    def _ensure_collection(self, name: str):
        if self.mongo_db is not None:
            if name not in self.mongo_db.list_collection_names():
                self.mongo_db.create_collection(name)
            return self.mongo_db[name]
        return self.memory[name]

    def _seed_demo_data(self):
        if self.mongo_db is not None:
            if self.mongo_db.admins.find_one({'username': 'admin'}) is None:
                self.mongo_db.admins.insert_one({
                    'admin_id': 'ADMIN-001',
                    'adminId': 'ADMIN-001',
                    'name': 'System Administrator',
                    'username': 'admin',
                    'email': 'admin@example.org',
                    'password': DEFAULT_PASSWORD_HASH,
                    'role': 'admin',
                    'status': 'active',
                })
            for hospital in [
                {
                    'hospitalId': 'HOSP-1001',
                    'hospital_id': 'HOSP-1001',
                    'name': 'City General Hospital',
                    'hospital_type': 'Multi-specialty',
                    'email': 'admin@citygeneral.org',
                    'username': 'citygeneral',
                    'password': DEFAULT_PASSWORD_HASH,
                    'contact_person': 'Dr. Nancy Reed',
                    'contact_number': '+1-555-0101',
                    'address': '12 Wellness Ave',
                    'city': 'Boston',
                    'district': 'Downtown',
                    'state': 'MA',
                    'pin_code': '02116',
                    'latitude': 42.3601,
                    'longitude': -71.0589,
                    'status': 'Approved',
                    'role': 'hospital',
                },
                {
                    'hospitalId': 'HOSP-1002',
                    'hospital_id': 'HOSP-1002',
                    'name': 'North Ridge Medical Centre',
                    'hospital_type': 'Regional',
                    'email': 'ops@northridge.org',
                    'username': 'northridge',
                    'password': DEFAULT_PASSWORD_HASH,
                    'contact_person': 'Dr. Amit Shah',
                    'contact_number': '+1-555-0102',
                    'address': '88 Cedar Lane',
                    'city': 'Chicago',
                    'district': 'Northside',
                    'state': 'IL',
                    'pin_code': '60611',
                    'latitude': 41.8781,
                    'longitude': -87.6298,
                    'status': 'Approved',
                    'role': 'hospital',
                },
            ]:
                if self.mongo_db.hospitals.find_one({'username': hospital['username']}) is None:
                    self.mongo_db.hospitals.insert_one(hospital)
            for index, (name, email, city) in enumerate(TAMIL_NADU_DEMO_HOSPITALS, start=1):
                if self.mongo_db.hospitals.find_one({'email': email}) is not None:
                    continue
                details = TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {})
                hospital_id = f'TN-DEMO-{index:03d}'
                self.mongo_db.hospitals.insert_one({
                    'hospitalId': hospital_id,
                    'hospital_id': hospital_id,
                    'name': name,
                    'hospitalName': name,
                    'hospital_type': details.get('hospital_type', 'Multi-specialty'),
                    'email': email,
                    'username': email,
                    'password': hash_password('apollo123456' if email == 'apollo@gmail.com' else DEMO_TN_PASSWORD),
                    'contact_person': details.get('contact_person', 'Demo Hospital Administrator'),
                    'contact_number': 'Demo contact only',
                    'address': details.get('address', city),
                    'city': city,
                    'district': details.get('district', city),
                    'state': 'Tamil Nadu',
                    'pin_code': details.get('pin_code', ''),
                    'latitude': None,
                    'longitude': None,
                    'status': 'Approved',
                    'role': 'hospital',
                    'demo_account': True,
                })
            self._seed_tamil_nadu_samples()
            if self.mongo_db.patients.count_documents({}) == 0:
                self.mongo_db.patients.insert_many([
                    {
                        'patient_id': 'PAT-2001',
                        'patient_name': 'Emma Johnson',
                        'age': 32,
                        'gender': 'Female',
                        'blood_group': 'O+',
                        'hospital_id': 'HOSP-1001',
                        'organ_required': 'Kidney',
                        'urgency': 'Critical',
                        'status': 'Waiting',
                        'medical_eligibility': 'Eligible',
                        'contact': '+1-555-2001',
                    },
                    {
                        'patient_id': 'PAT-2002',
                        'patient_name': 'Lucas Chen',
                        'age': 48,
                        'gender': 'Male',
                        'blood_group': 'A+',
                        'hospital_id': 'HOSP-1002',
                        'organ_required': 'Liver',
                        'urgency': 'High',
                        'status': 'Waiting',
                        'medical_eligibility': 'Eligible',
                        'contact': '+1-555-2002',
                    },
                ])
            if self.mongo_db.organs.count_documents({}) == 0:
                self.mongo_db.organs.insert_many([
                    {
                        'organ_id': 'ORG-3001',
                        'donor_id': 'DON-4001',
                        'organ_type': 'Kidney',
                        'blood_group': 'O+',
                        'condition': 'Excellent',
                        'consent': 'Confirmed',
                        'viability': 95,
                        'donor_hospital_id': 'HOSP-1001',
                        'status': 'Available',
                        'retrieval_datetime': '2026-11-05T10:00:00',
                        'expiry_datetime': '2026-11-06T10:00:00',
                    },
                    {
                        'organ_id': 'ORG-3002',
                        'donor_id': 'DON-4002',
                        'organ_type': 'Liver',
                        'blood_group': 'A+',
                        'condition': 'Good',
                        'consent': 'Confirmed',
                        'viability': 88,
                        'donor_hospital_id': 'HOSP-1002',
                        'status': 'Available',
                        'retrieval_datetime': '2026-11-05T09:30:00',
                        'expiry_datetime': '2026-11-06T09:30:00',
                    },
                ])
            return

        self.memory['admins'] = [{
            'admin_id': 'ADMIN-001',
            'name': 'System Administrator',
            'username': 'admin',
            'password': DEFAULT_PASSWORD_HASH,
            'role': 'admin',
            'status': 'active',
        }]
        self.memory['hospitals'] = [
            {
                'hospital_id': 'HOSP-1001',
                'name': 'City General Hospital',
                'hospital_type': 'Multi-specialty',
                'email': 'admin@citygeneral.org',
                'username': 'citygeneral',
                'password': DEFAULT_PASSWORD_HASH,
                'contact_person': 'Dr. Nancy Reed',
                'contact_number': '+1-555-0101',
                'address': '12 Wellness Ave',
                'city': 'Boston',
                'district': 'Downtown',
                'state': 'MA',
                'pin_code': '02116',
                'latitude': 42.3601,
                'longitude': -71.0589,
                'status': 'Approved',
                'role': 'hospital',
            },
            {
                'hospital_id': 'HOSP-1002',
                'name': 'North Ridge Medical Centre',
                'hospital_type': 'Regional',
                'email': 'ops@northridge.org',
                'username': 'northridge',
                'password': DEFAULT_PASSWORD_HASH,
                'contact_person': 'Dr. Amit Shah',
                'contact_number': '+1-555-0102',
                'address': '88 Cedar Lane',
                'city': 'Chicago',
                'district': 'Northside',
                'state': 'IL',
                'pin_code': '60611',
                'latitude': 41.8781,
                'longitude': -87.6298,
                'status': 'Approved',
                'role': 'hospital',
            },
        ]
        self.memory['hospitals'].extend([
            dict({
                'hospital_id': f'TN-DEMO-{index:03d}',
                'hospitalId': f'TN-DEMO-{index:03d}',
                'name': name,
                'hospitalName': name,
                'hospital_type': TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {}).get('hospital_type', 'Multi-specialty'),
                'email': email,
                'username': email,
                'password': hash_password('apollo123456' if email == 'apollo@gmail.com' else DEMO_TN_PASSWORD),
                'contact_person': TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {}).get('contact_person', 'Demo Hospital Administrator'),
                'contact_number': 'Demo contact only',
                'address': TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {}).get('address', city),
                'city': city,
                'district': TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {}).get('district', city),
                'state': 'Tamil Nadu',
                'pin_code': TAMIL_NADU_DEMO_HOSPITAL_DETAILS.get(email, {}).get('pin_code', ''),
                'status': 'Approved',
                'role': 'hospital',
                'demo_account': True,
            })
            for index, (name, email, city) in enumerate(TAMIL_NADU_DEMO_HOSPITALS, start=1)
        ])
        self.memory['patients'] = [
            {
                'patient_id': 'PAT-2001',
                'patient_name': 'Emma Johnson',
                'age': 32,
                'gender': 'Female',
                'blood_group': 'O+',
                'hospital_id': 'HOSP-1001',
                'organ_required': 'Kidney',
                'urgency': 'Critical',
                'status': 'Waiting',
                'medical_eligibility': 'Eligible',
                'contact': '+1-555-2001',
            },
            {
                'patient_id': 'PAT-2002',
                'patient_name': 'Lucas Chen',
                'age': 48,
                'gender': 'Male',
                'blood_group': 'A+',
                'hospital_id': 'HOSP-1002',
                'organ_required': 'Liver',
                'urgency': 'High',
                'status': 'Waiting',
                'medical_eligibility': 'Eligible',
                'contact': '+1-555-2002',
            },
        ]
        self.memory['organs'] = [
            {
                'organ_id': 'ORG-3001',
                'donor_id': 'DON-4001',
                'organ_type': 'Kidney',
                'blood_group': 'O+',
                'condition': 'Excellent',
                'consent': 'Confirmed',
                'viability': 95,
                'donor_hospital_id': 'HOSP-1001',
                'status': 'Available',
                'retrieval_datetime': '2026-11-05T10:00:00',
                'expiry_datetime': '2026-11-06T10:00:00',
            },
            {
                'organ_id': 'ORG-3002',
                'donor_id': 'DON-4002',
                'organ_type': 'Liver',
                'blood_group': 'A+',
                'condition': 'Good',
                'consent': 'Confirmed',
                'viability': 88,
                'donor_hospital_id': 'HOSP-1002',
                'status': 'Available',
                'retrieval_datetime': '2026-11-05T09:30:00',
                'expiry_datetime': '2026-11-06T09:30:00',
            },
        ]
        self._seed_tamil_nadu_samples()

    def _seed_tamil_nadu_samples(self):
        hospitals = self.find('hospitals')
        hospital_by_email = {hospital.get('email'): hospital for hospital in hospitals}
        apollo = hospital_by_email.get('apollo@gmail.com')
        miot = hospital_by_email.get('miot.demo@vitaroute.example')
        kauvery = hospital_by_email.get('kauvery.demo@vitaroute.example')
        psg = hospital_by_email.get('psg.demo@vitaroute.example')
        kmch = hospital_by_email.get('kmch.demo@vitaroute.example')
        cmc = hospital_by_email.get('cmc.vellore.demo@vitaroute.example')
        if not all((apollo, miot, kauvery, psg, kmch, cmc)):
            return

        def hospital_id(hospital):
            return hospital.get('hospital_id') or hospital.get('hospitalId')

        donors = [
            {
                'sample_id': 'TN-DEMO-DONOR-001', 'donor_id': 'DON-TN-001',
                'donor_name': 'Arun Kumar (Demo)', 'age': 34, 'gender': 'Male',
                'blood_group': 'O+', 'organ_type': 'Kidney', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(apollo), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-002', 'donor_id': 'DON-TN-002',
                'donor_name': 'Meera Nair (Demo)', 'age': 42, 'gender': 'Female',
                'blood_group': 'A+', 'organ_type': 'Liver', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(miot), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-003', 'donor_id': 'DON-TN-003',
                'donor_name': 'Vijay Raman (Demo)', 'age': 29, 'gender': 'Male',
                'blood_group': 'AB+', 'organ_type': 'Heart', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(kauvery), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-004', 'donor_id': 'DON-TN-004',
                'donor_name': 'Anitha Raj (Demo)', 'age': 37, 'gender': 'Female',
                'blood_group': 'B+', 'organ_type': 'Kidney', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(psg), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-005', 'donor_id': 'DON-TN-005',
                'donor_name': 'Suresh Kumar (Demo)', 'age': 45, 'gender': 'Male',
                'blood_group': 'O-', 'organ_type': 'Liver', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(cmc), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-006', 'donor_id': 'DON-TN-006',
                'donor_name': 'Lakshmi Devi (Demo)', 'age': 31, 'gender': 'Female',
                'blood_group': 'A-', 'organ_type': 'Kidney', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(apollo), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-007', 'donor_id': 'DON-TN-007',
                'donor_name': 'Karthik Selvan (Demo)', 'age': 39, 'gender': 'Male',
                'blood_group': 'B+', 'organ_type': 'Liver', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(miot), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-008', 'donor_id': 'DON-TN-008',
                'donor_name': 'Divya Srinivasan (Demo)', 'age': 27, 'gender': 'Female',
                'blood_group': 'O+', 'organ_type': 'Cornea', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(kauvery), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-009', 'donor_id': 'DON-TN-009',
                'donor_name': 'Prakash Mani (Demo)', 'age': 50, 'gender': 'Male',
                'blood_group': 'AB+', 'organ_type': 'Pancreas', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(psg), 'status': 'Approved', 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-DONOR-010', 'donor_id': 'DON-TN-010',
                'donor_name': 'Nandhini Kumar (Demo)', 'age': 35, 'gender': 'Female',
                'blood_group': 'B-', 'organ_type': 'Lungs', 'consent_status': 'Confirmed',
                'hospital_id': hospital_id(kmch), 'status': 'Approved', 'demo_record': True,
            },
        ]
        for donor in donors:
            if self.find_one('donors', {'sample_id': donor['sample_id']}) is None:
                self.insert('donors', donor)

        patients = [
            {
                'sample_id': 'TN-DEMO-PATIENT-001', 'patient_id': 'PAT-TN-001',
                'patient_name': 'Kavya M (Demo)', 'age': 32, 'gender': 'Female',
                'blood_group': 'O+', 'organ_required': 'Kidney', 'urgency': 'Critical',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(apollo), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-002', 'patient_id': 'PAT-TN-002',
                'patient_name': 'Ramesh S (Demo)', 'age': 46, 'gender': 'Male',
                'blood_group': 'A+', 'organ_required': 'Liver', 'urgency': 'High',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(miot), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-003', 'patient_id': 'PAT-TN-003',
                'patient_name': 'Meena R (Demo)', 'age': 28, 'gender': 'Female',
                'blood_group': 'AB+', 'organ_required': 'Heart', 'urgency': 'Critical',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(kauvery), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-004', 'patient_id': 'PAT-TN-004',
                'patient_name': 'Senthil K (Demo)', 'age': 51, 'gender': 'Male',
                'blood_group': 'B+', 'organ_required': 'Kidney', 'urgency': 'High',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(psg), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-005', 'patient_id': 'PAT-TN-005',
                'patient_name': 'Farah A (Demo)', 'age': 39, 'gender': 'Female',
                'blood_group': 'O+', 'organ_required': 'Liver', 'urgency': 'Medium',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(cmc), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-006', 'patient_id': 'PAT-TN-006',
                'patient_name': 'Naveen P (Demo)', 'age': 43, 'gender': 'Male',
                'blood_group': 'A-', 'organ_required': 'Kidney', 'urgency': 'Medium',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(kmch), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-007', 'patient_id': 'PAT-TN-007',
                'patient_name': 'Priya V (Demo)', 'age': 25, 'gender': 'Female',
                'blood_group': 'B+', 'organ_required': 'Liver', 'urgency': 'High',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(apollo), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-008', 'patient_id': 'PAT-TN-008',
                'patient_name': 'Madhan G (Demo)', 'age': 36, 'gender': 'Male',
                'blood_group': 'AB+', 'organ_required': 'Pancreas', 'urgency': 'Normal',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(miot), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-009', 'patient_id': 'PAT-TN-009',
                'patient_name': 'Aishwarya D (Demo)', 'age': 30, 'gender': 'Female',
                'blood_group': 'O+', 'organ_required': 'Lungs', 'urgency': 'Critical',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(kauvery), 'demo_record': True,
            },
            {
                'sample_id': 'TN-DEMO-PATIENT-010', 'patient_id': 'PAT-TN-010',
                'patient_name': 'Bala Murugan (Demo)', 'age': 47, 'gender': 'Male',
                'blood_group': 'A+', 'organ_required': 'Cornea', 'urgency': 'Normal',
                'medical_eligibility': 'Eligible', 'status': 'Waiting',
                'hospital_id': hospital_id(psg), 'demo_record': True,
            },
        ]
        for patient in patients:
            if self.find_one('patients', {'sample_id': patient['sample_id']}) is None:
                self.insert('patients', patient)

        now = dt.datetime.utcnow()
        organs = [
            {
                'sample_id': 'TN-DEMO-ORGAN-001', 'organ_id': 'ORG-TN-001',
                'donor_id': 'DON-TN-001', 'organ_type': 'Kidney', 'blood_group': 'O+',
                'condition': 'Excellent', 'consent': 'Confirmed', 'viability': 96,
                'donor_hospital_id': hospital_id(apollo), 'status': 'Available',
                'medical_approval': 'Approved', 'hla_code': 'A2, B7', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=18)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-002', 'organ_id': 'ORG-TN-002',
                'donor_id': 'DON-TN-002', 'organ_type': 'Liver', 'blood_group': 'A+',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 91,
                'donor_hospital_id': hospital_id(miot), 'status': 'Available',
                'medical_approval': 'Approved', 'hla_code': 'A1, B8', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=10)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-003', 'organ_id': 'ORG-TN-003',
                'donor_id': 'DON-TN-003', 'organ_type': 'Heart', 'blood_group': 'AB+',
                'condition': 'Excellent', 'consent': 'Confirmed', 'viability': 94,
                'donor_hospital_id': hospital_id(kauvery), 'status': 'In Transit',
                'medical_approval': 'Approved', 'hla_code': 'A3, B5', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=5)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-004', 'organ_id': 'ORG-TN-004',
                'donor_id': 'DON-TN-004', 'organ_type': 'Kidney', 'blood_group': 'B+',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 89,
                'donor_hospital_id': hospital_id(psg), 'status': 'Available',
                'medical_approval': 'Approved', 'hla_code': 'A11, B35', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=20)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-005', 'organ_id': 'ORG-TN-005',
                'donor_id': 'DON-TN-005', 'organ_type': 'Liver', 'blood_group': 'O-',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 87,
                'donor_hospital_id': hospital_id(cmc), 'status': 'Available',
                'medical_approval': 'Approved', 'hla_code': 'A2, B44', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=9)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-006', 'organ_id': 'ORG-TN-006',
                'donor_id': 'DON-TN-006', 'organ_type': 'Kidney', 'blood_group': 'A-',
                'condition': 'Excellent', 'consent': 'Confirmed', 'viability': 93,
                'donor_hospital_id': hospital_id(apollo), 'status': 'Reserved',
                'medical_approval': 'Approved', 'hla_code': 'A3, B7', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=22)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-007', 'organ_id': 'ORG-TN-007',
                'donor_id': 'DON-TN-007', 'organ_type': 'Liver', 'blood_group': 'B+',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 90,
                'donor_hospital_id': hospital_id(miot), 'status': 'In Transit',
                'medical_approval': 'Approved', 'hla_code': 'A9, B12', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=11)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-008', 'organ_id': 'ORG-TN-008',
                'donor_id': 'DON-TN-008', 'organ_type': 'Cornea', 'blood_group': 'O+',
                'condition': 'Excellent', 'consent': 'Confirmed', 'viability': 98,
                'donor_hospital_id': hospital_id(kauvery), 'status': 'Delivered',
                'medical_approval': 'Approved', 'hla_code': '', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=26)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-009', 'organ_id': 'ORG-TN-009',
                'donor_id': 'DON-TN-009', 'organ_type': 'Pancreas', 'blood_group': 'AB+',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 88,
                'donor_hospital_id': hospital_id(psg), 'status': 'Reserved',
                'medical_approval': 'Approved', 'hla_code': 'A24, B44', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=13)).isoformat(),
            },
            {
                'sample_id': 'TN-DEMO-ORGAN-010', 'organ_id': 'ORG-TN-010',
                'donor_id': 'DON-TN-010', 'organ_type': 'Lungs', 'blood_group': 'O-',
                'condition': 'Good', 'consent': 'Confirmed', 'viability': 86,
                'donor_hospital_id': hospital_id(kmch), 'status': 'In Transit',
                'medical_approval': 'Approved', 'hla_code': 'A2, B44', 'demo_record': True,
                'expiry_datetime': (now + dt.timedelta(hours=7)).isoformat(),
            },
        ]
        for organ in organs:
            if self.find_one('organs', {'sample_id': organ['sample_id']}) is None:
                self.insert('organs', organ)
            else:
                self.update_one('organs', {'sample_id': organ['sample_id']}, organ)

        matches = [
            ('ORG-TN-001', 'PAT-TN-001', apollo, apollo, 'Transportation Started', 8.5, 0.4),
            ('ORG-TN-002', 'PAT-TN-002', miot, miot, 'Pending', 6.2, 0.3),
            ('ORG-TN-003', 'PAT-TN-003', kauvery, kauvery, 'Transportation Started', 5.4, 0.25),
            ('ORG-TN-004', 'PAT-TN-004', psg, psg, 'Delivered', 4.1, 0.2),
            ('ORG-TN-005', 'PAT-TN-005', cmc, cmc, 'Transplant Completed', 3.8, 0.2),
            ('ORG-TN-006', 'PAT-TN-006', apollo, kmch, 'Pending', 496.0, 10.5),
            ('ORG-TN-007', 'PAT-TN-007', miot, apollo, 'Transportation Started', 19.5, 0.8),
            ('ORG-TN-008', 'PAT-TN-010', kauvery, psg, 'Delivered', 506.0, 11.0),
            ('ORG-TN-009', 'PAT-TN-008', psg, miot, 'Pending', 503.0, 10.8),
            ('ORG-TN-010', 'PAT-TN-009', kmch, kauvery, 'Transportation Started', 506.0, 10.8),
        ]
        sample_patients = {patient['patient_id']: patient for patient in self.find('patients')}
        sample_organs = {organ['organ_id']: organ for organ in self.find('organs')}
        for index, (organ_id, patient_id, donor_hospital, recipient_hospital, status, distance_km, travel_hours) in enumerate(matches, start=1):
            organ = sample_organs[organ_id]
            patient = sample_patients[patient_id]
            match_id = f'MATCH-TN-{index:03d}'
            organ_status = {
                'Pending': 'Reserved',
                'Transportation Started': 'In Transit',
                'Delivered': 'Delivered',
                'Transplant Completed': 'Transplanted',
            }[status]
            organ['status'] = organ_status
            self.update_one('organs', {'sample_id': organ['sample_id']}, {'status': organ_status})
            match = {
                'sample_id': f'TN-DEMO-MATCH-{index:03d}',
                'match_id': match_id,
                'organ_id': organ_id,
                'organ_type': organ['organ_type'],
                'donor_id': organ['donor_id'],
                'donor_hospital_id': hospital_id(donor_hospital),
                'recipient_hospital_id': hospital_id(recipient_hospital),
                'patient_id': patient_id,
                'patient_priority': patient.get('urgency', 'Normal'),
                'compatibility': 'Demo match result (not a clinical recommendation)',
                'distance_km': distance_km,
                'travel_time_hours': travel_hours,
                'remaining_expiry_hours': max(0, (dt.datetime.fromisoformat(organ['expiry_datetime']) - now).total_seconds() / 3600),
                'status': status,
                'created_at': now.isoformat(),
                'demo_record': True,
            }
            if self.find_one('matches', {'sample_id': match['sample_id']}) is None:
                self.insert('matches', match)
            else:
                self.update_one('matches', {'sample_id': match['sample_id']}, match)

            transport_status = 'In Transit' if status == 'Transportation Started' else (
                'Delivered' if status in {'Delivered', 'Transplant Completed'} else 'Scheduled'
            )
            transit = {
                'sample_id': f'TN-DEMO-TRANSIT-{index:03d}',
                'transport_id': f'TRANS-TN-{index:03d}',
                'match_id': match_id,
                'organ_id': organ_id,
                'organ_type': organ['organ_type'],
                'donor_hospital_id': hospital_id(donor_hospital),
                'recipient_hospital_id': hospital_id(recipient_hospital),
                'status': transport_status,
                'distance_km': distance_km,
                'travel_time_hours': travel_hours,
                'origin': f"{donor_hospital.get('name') or donor_hospital.get('hospitalName')}, {donor_hospital.get('city', '')}",
                'destination': f"{recipient_hospital.get('name') or recipient_hospital.get('hospitalName')}, {recipient_hospital.get('city', '')}",
                'estimated_arrival': (now + dt.timedelta(hours=travel_hours)).isoformat(),
                'expiry_deadline': organ['expiry_datetime'],
                'demo_record': True,
            }
            if self.find_one('transport_records', {'sample_id': transit['sample_id']}) is None:
                self.insert('transport_records', transit)
            else:
                self.update_one('transport_records', {'sample_id': transit['sample_id']}, transit)

        alternative_matches = [
            ('ORG-TN-001', 'PAT-TN-004', apollo, psg, 'MATCH-TN-001', 8.5, 0.4),
            ('ORG-TN-005', 'PAT-TN-007', cmc, apollo, 'MATCH-TN-005', 128.0, 2.8),
        ]
        for index, (organ_id, patient_id, donor_hospital, recipient_hospital, primary_match_id, distance_km, travel_hours) in enumerate(alternative_matches, start=11):
            organ = sample_organs[organ_id]
            patient = sample_patients[patient_id]
            alternative = {
                'sample_id': f'TN-DEMO-MATCH-{index:03d}',
                'match_id': f'MATCH-TN-{index:03d}',
                'organ_id': organ_id,
                'organ_type': organ['organ_type'],
                'donor_id': organ['donor_id'],
                'donor_hospital_id': hospital_id(donor_hospital),
                'recipient_hospital_id': hospital_id(recipient_hospital),
                'patient_id': patient_id,
                'patient_priority': patient.get('urgency', 'Normal'),
                'compatibility': 'Sample-compatible alternative; not assigned',
                'distance_km': distance_km,
                'travel_time_hours': travel_hours,
                'status': 'Alternative Candidate',
                'alternative_to': primary_match_id,
                'created_at': now.isoformat(),
                'demo_record': True,
            }
            if self.find_one('matches', {'sample_id': alternative['sample_id']}) is None:
                self.insert('matches', alternative)
            else:
                self.update_one('matches', {'sample_id': alternative['sample_id']}, alternative)

    def get_collection(self, name: str):
        if self.mongo_db is not None:
            return self.mongo_db[name]
        return self.memory.get(name, [])

    def insert(self, name: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        collection = self.get_collection(name)
        if self.mongo_db is not None:
            result = self.mongo_db[name].insert_one(doc)
            return self.mongo_db[name].find_one({'_id': result.inserted_id})
        collection.append(copy.deepcopy(doc))
        return copy.deepcopy(doc)

    @staticmethod
    def _matches_query(item: Dict[str, Any], query: Dict[str, Any]) -> bool:
        if not query:
            return True
        if '$or' in query:
            return any(DatabaseManager._matches_query(item, clause) for clause in query['$or'])
        for k, v in query.items():
            if isinstance(v, dict):
                if '$in' in v:
                    if item.get(k) not in v.get('$in', []):
                        return False
                    continue
                if '$ne' in v:
                    if item.get(k) == v.get('$ne'):
                        return False
                    continue
                if '$exists' in v:
                    exists = item.get(k) is not None
                    if exists != v.get('$exists'):
                        return False
                    continue
            if item.get(k) != v:
                return False
        return True

    def find(self, name: str, query: Dict[str, Any] = None):
        query = query or {}
        if self.mongo_db is not None:
            return list(self.mongo_db[name].find(query))
        return [copy.deepcopy(item) for item in self.memory.get(name, []) if self._matches_query(item, query)]

    def find_one(self, name: str, query: Dict[str, Any]):
        if self.mongo_db is not None:
            return self.mongo_db[name].find_one(query)
        for item in self.memory.get(name, []):
            if self._matches_query(item, query):
                return copy.deepcopy(item)
        return None

    def update_one(self, name: str, query: Dict[str, Any], changes: Dict[str, Any]):
        if self.mongo_db is not None:
            return self.mongo_db[name].update_one(query, {'$set': changes})
        for item in self.memory.get(name, []):
            if self._matches_query(item, query):
                item.update(changes)
                return None
        return None

    def count(self, name: str, query: Dict[str, Any] = None):
        query = query or {}
        if self.mongo_db is not None:
            return self.mongo_db[name].count_documents(query)
        return sum(1 for item in self.memory.get(name, []) if self._matches_query(item, query))

    def get_summary(self):
        return {
            'total_hospitals': self.count('hospitals', {'status': {'$in': ['Approved', 'Pending', 'Suspended']}}),
            'total_patients': self.count('patients'),
            'available_organs': self.count('organs', {'status': 'Available'}),
            'critical_patients': self.count('patients', {'urgency': 'Critical'}),
            'successful_matches': self.count('matches', {'status': 'Confirmed'}),
            'active_transits': self.count('transport_records', {'status': {'$ne': 'Completed'}}),
            'failed_matches': self.count('matches', {'status': {'$in': ['Rejected', 'Expired', 'Cancelled']}}),
        }
