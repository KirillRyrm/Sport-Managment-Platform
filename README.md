# Sport Management Platform
 
A cloud-native web platform for running a network of sports facilities. It handles gyms and their locations, equipment inventory, subscription plans, trainers, clients, training sessions, client goals, progress notes, and feedback, all behind a role-based permission system. Built with Django, Django REST Framework, and PostgreSQL, packaged with Docker, and deployed behind Nginx with Let's Encrypt TLS.
 
This was my Bachelor's thesis project at Odesa I.I. Mechnikov National University and the basis of a peer-reviewed publication ([DOI: 10.30525/978-9934-26-630-0-5](https://doi.org/10.30525/978-9934-26-630-0-5), International Scientific Conference, Riga, December 2025).
 
---
 
## What it does
 
The platform serves three roles, each with its own dashboard and API surface.
 
**Clients** browse the gym network, subscribe to plans, sign up for training sessions, set personal goals, track their progress, and leave feedback on trainers. **Trainers** manage their own session schedule, see the clients registered for each session, and record progress notes after a session ends. **Administrators** manage the underlying catalogue (gyms, locations, equipment, subscription plans, training types, goals), oversee user accounts, and access analytics on client attendance, training-type popularity, and location utilisation.
 
The same data is exposed both as server-rendered HTML pages (for staff working in a browser) and as JSON over REST (for any future mobile client or integration), with permissions enforced identically on both surfaces.
 
## Architecture
 
The project is a single Django application split into four domain apps that map cleanly to the database schemas:
 
```
sportmanagment/        # project settings, root URLconf
├── auth_app/          # users, custom auth backend, roles & permissions
├── gym_app/           # gyms, locations, equipment, subscriptions, goals
├── training_app/      # trainers, training types, sessions, analytics
└── client_app/        # clients, subscriptions, goals, progress, feedback
```
 
Each domain app follows the same internal layout: `models.py` describes the entities, `views.py` contains the HTML CRUD views, `forms.py` the Django forms, an `api/` subpackage holds one DRF `APIView` module per resource, and `templates/` contains the Bootstrap-based templates extending a shared `base.html`.
 
**Database.** PostgreSQL with three logical schemas: `gym_scheme`, `training_scheme`, and `client_scheme`. Django models are declared with `managed = False`, meaning the schema is owned and versioned by SQL scripts rather than Django migrations — Django reads and writes to existing tables but does not control their structure. This was a deliberate choice for the thesis, which had a separate database-design component evaluated independently.
 
**Authentication.** A custom `UserCredentials` model lives in its own table, separate from `auth_user`, and is paired with a custom `UserCredentialsBackend` that authenticates against hashed passwords stored there. The model implements the full Django auth contract (`is_authenticated`, `is_staff`, `has_perm`, `get_all_permissions`, and so on) so it slots into the standard `@login_required` decorator and DRF's `IsAuthenticated` permission class without further glue.
 
**Authorisation.** Three roles — `admin`, `trainer`, `client` — backed by Django's `Group` and `Permission` framework. The full access matrix (sixteen resources × three roles × CRUD verbs) is encoded in a single `setup_roles` management command, so the permission model is reproducible and version-controlled rather than scattered across the admin UI. Every API view checks `request.user.has_perm(...)` explicitly before serving data, and protected HTML views check `request.user.user_role` for higher-level role gates (analytics, for example, is admin-only).
 
**REST API.** DRF with session and basic authentication, `IsAuthenticated` as the global default, and per-view permission checks. Every resource has both a list endpoint (`GET`/`POST /api/<resource>/`) and a detail endpoint (`GET`/`PUT`/`DELETE /api/<resource>/<id>/`). Serialisers handle the foreign-key relationships explicitly so the JSON contract stays stable as the database evolves.
 
**Logging.** Per-app `logging.getLogger(__name__)` loggers wrap every API action, distinguishing successful operations (`info`), denied permission attempts (`warning`), and integrity errors (`error`). Useful when reviewing access patterns after deployment.
 
## Deployment
 
Three containers, orchestrated with `docker-compose`:
 
- **`web`** — the Django application served by Gunicorn on port 8000, with static and media files mounted on named volumes.
- **`nginx`** — reverse proxy on ports 80 and 443, terminating TLS with Let's Encrypt certificates, serving static and media files directly, and proxying everything else to `web`.
- **`certbot`** — runs `certbot renew` on a schedule, sharing the certificate volumes with Nginx and reloading it via a deploy hook.
The production deployment lives at `fitness.ukrnic.com` on DigitalOcean. The Nginx configuration redirects HTTP to HTTPS, enforces TLS 1.2/1.3, and caches static assets for 30 days.
 
## Running locally
 
```bash
git clone <this-repo>
cd Sport-Managment-Platform-main
 
# create a .env file with the database credentials and Django secret
cat > .env <<EOF
DJANGO_SECRET_KEY=dev-secret-change-me
DB_NAME=sportmgmt
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
EOF
 
# bring everything up
docker-compose up --build
```
 
The database schema itself is not part of this repository — it is created from a separate set of SQL scripts (the thesis's database-design deliverable). Once the schema is in place, seed the role and permission groups:
 
```bash
docker-compose exec web python manage.py setup_roles
docker-compose exec web python manage.py sync_user_groups
```
 
After that the platform is reachable on `http://localhost` and the API at `http://localhost/auth/api/`, `http://localhost/api/gym_list/`, and so on.
