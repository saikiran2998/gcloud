# Deployment notes

This project is intended for local demonstration first. The included Dockerfile is an initial container setup, not a claim of production readiness.

Before a public deployment:
- Set `FLASK_SECRET_KEY` to a strong secret via a secret manager.
- Remove demo accounts or require secure account provisioning.
- Add CSRF protection, rate limiting, password reset policies, and comprehensive tests.
- Move from SQLite to Cloud SQL for PostgreSQL if using multiple Cloud Run instances; a local SQLite file is not a durable shared production database.
- Configure Cloud Storage for private certificate uploads if that feature is added.
- Review Google Cloud pricing and create budget alerts before enabling billable services.

Suggested first deployment path: validate locally, then containerize and deploy to Cloud Run; treat database migration and secret configuration as separate required steps.
