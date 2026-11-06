# VitaRoute

VitaRoute is a Flask + PyMongo demo healthcare organ-matching system.

## Run locally

1. Create a virtual environment.
2. Install dependencies:
   `pip install -r backend/requirements.txt`
3. Start MongoDB on localhost:27017. VitaRoute checks the MongoDB connection before enabling login; sign-in and dashboard/API access are blocked while the database is unavailable.
4. Run:
   `python3 backend/app.py`
5. Open http://localhost:5001/loading

## Demo credentials

- Admin email: `admin@example.org`, password `Admin@123`
- City General Hospital email: `admin@citygeneral.org`, password `Admin@123`
- Apollo sample account: `apollo@gmail.com`, password `apollo123456`
- Other Tamil Nadu sample hospital accounts use the demo credentials shown on the login page.

> All demo credentials are for local development only. Hospital sessions are restricted to their own records; pending or suspended hospitals cannot sign in.

The local demo database is seeded with synthetic Tamil Nadu hospital accounts and donor, patient, organ, matching, and transport records at startup. It includes twenty Tamil Nadu hospital accounts, ten demo organs, twelve demo matching results (including two unassigned alternatives), and ten demo transport records. The additional hospital accounts use the demo password `TNVita@123`; their `.example` email addresses and contact details are fictional. Running the matching engine uses waiting, medically eligible registered patients and currently available compatible organs, shows the results on the matching page, and reserves organs selected for a match. Hospital accounts only run matching for their own patients and see only matches/transports involving their hospital; the admin account can review all seeded records. Demo matching results are illustrative and are not clinical recommendations. Sample route distances and arrival times are estimates, not live routing or GPS data.
