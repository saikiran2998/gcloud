# CareerIQ — Working Prototype

CareerIQ connects students, faculty/admin, and companies in a college demonstration web application. It uses Flask, SQLite, Jinja2, HTML, CSS and JavaScript.

## Features
- Role-based demo sign-in with hashed passwords and backend route checks.
- Student profile, career goal, skills, certificates and project records.
- Faculty student overview, academic score updates, certificate review status.
- Company job/internship creation, opening/closing postings, application review.
- Student opportunity search, duplicate-safe job applications and status tracking.
- Difficulty-weighted skill test: Basic = 1, Intermediate = 2, Advanced = 3. Time is not included in scoring.
- Rule-based career roadmap and skill coverage.
- Responsive dashboards, search, status labels and health endpoint at `/health`.

## Run on Windows PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

If activation is blocked, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current terminal and activate again.

## Demo accounts
| Role | Email | Password |
|---|---|---|
| Student | student@careeriq.demo | Student@123 |
| Faculty/Admin | faculty@careeriq.demo | Faculty@123 |
| Company | company@careeriq.demo | Company@123 |

The database and fictional demo records are created automatically. The local SQLite database is excluded from Git.

## Push to GitHub
```powershell
git status
git add .
git commit -m "Build CareerIQ working prototype"
git push
```

## Important limitations
This is a prototype, not a production service. Career recommendations are rule-based, not a trained AI model. Jobs are demo records, not live feeds. Certificate records have review statuses but do not validate issuer websites or store uploaded files. Before public deployment, add CSRF protection, rate limiting, password reset/email verification as appropriate, comprehensive automated tests, production secrets, and a managed persistent database. Do not expose demo credentials publicly.

## Google Cloud direction
Recommended next step after local testing: containerize and deploy to Cloud Run. For multi-instance production usage, replace SQLite with Cloud SQL for PostgreSQL, use Secret Manager for secrets, and Cloud Storage for private certificate files. Deployment may incur charges; review pricing and configure a budget alert first.
