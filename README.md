# Med-Emergency QR – AI-Based Medical Emergency Web Application

A student project prototype based on the uploaded Med-Emergency PPT.

## Features
- Patient registration and login
- Medical profile: age, blood group, reported allergies, medicines, history
- Emergency contact details
- Patient-controlled QR emergency display fields
- Unique QR code for each patient
- QR code opens a read-only emergency profile
- Local TF-IDF-based NLP summary using scikit-learn
- Profile update and last-updated timestamp

## Tech stack
Python, Flask, SQLite, scikit-learn (TF-IDF), qrcode, HTML, CSS, Bootstrap CDN.

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract this ZIP and open the folder in VS Code.
3. Open Terminal in the project folder.
4. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

5. Install packages:

```bash
pip install -r requirements.txt
```

6. Start the website:

```bash
python app.py
```

7. Open `http://127.0.0.1:5000` in Chrome.

The SQLite database `med_emergency.db` is created automatically when the app starts.
Demo: register a new account, fill in the profile, then open Dashboard > Download QR Code.
Scan the QR code using a phone camera.

## Important project limitations
- This is an educational prototype, not a certified clinical system.
- The AI feature summarizes patient-entered text with TF-IDF. It does not diagnose, predict disease, recommend medicines, or replace a clinician.
- QR emergency pages are accessible to anyone who has the QR link. Do not include details that should remain private; choose display fields carefully.
- Do not use real patient data for college demonstrations.
- Before real deployment, add HTTPS, CSRF protection, rate limiting, audit logs, stronger session configuration, backups, consent workflows, and security testing. A public QR link is not identity verification.
- Emergency information may be incomplete or outdated. Always verify details with the patient/caregiver or a qualified healthcare professional.

## Updated medication and emergency summary fields
The medical profile now includes Medicine Name, Dose/Strength, Frequency and Time. The AI summary highlights reported allergy information, blood group and the entered medication schedule, and displays the last profile update date. The same medication schedule is shown on the public QR emergency page only when `Show medicines` is enabled. This version supports one structured medicine entry plus the existing free-text current-medicines notes. It is an educational prototype; it does not verify prescriptions or provide medication advice.
