# GoGoTruk — Backend API

## Tech Stack
| Layer | Technology |
|-------|-----------|
| API | Python 3.11+ / FastAPI |
| Database | PostgreSQL (Supabase Cloud) |
| Migrations | Alembic (auto-generated + auto-applied on every uvicorn reload) |
| ORM | SQLAlchemy |
| File Storage | Cloudinary |
| PDF Generation | ReportLab |
| Background Jobs | APScheduler |

---

## Onboarding (4 steps)

### 1 — Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings "pydantic[email]" python-multipart cloudinary alembic reportlab apscheduler
```

### 2 — Set Up `.env`
```bash
# from truck_app/
copy .env.example .env
```
All values in `.env.example` are pre-filled for the shared dev DB.  
`SUPABASE_KEY` is optional — not used in any current endpoint.

### 3 — Run
```bash
# from truck_app/
uvicorn app.main:app --reload
```
Migrations run automatically on every startup. No manual `alembic` commands needed.

### 4 — Verify
- API root: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/docs

---

## Key Behaviours

### Auto-Migration
Everything is fully automated — no Alembic commands to remember.

Every uvicorn reload runs `_migrate.py` which:
1. Compares SQLAlchemy models against the live DB
2. Auto-generates a versioned migration file in `alembic/versions/` if anything changed
3. Deletes it automatically if there are no real changes (no empty files cluttering the folder)
4. Applies all pending migrations to the DB

**Complete workflow for adding a new table or column:**
1. Write or update a model in `app/models/`
2. Save the file — uvicorn reloads
3. Migration file is created, named, and applied — done

No `alembic revision`, no `alembic upgrade head`, no manual steps.  
The generated version files are committed to git so teammates get the schema change automatically on next pull + reload.

### DEV_MODE
Set in `.env` — default is `true`.

| Feature | DEV_MODE=true | DEV_MODE=false |
|---------|--------------|----------------|
| OTP | Auto-verified, returned as `dev_otp` in response | Real SMS via MSG91 |
| Notifications | Printed to terminal | Real SMS + email |

### Document Proxy
Cloudinary URLs require auth. Never use raw Cloudinary URLs in the frontend.
Always proxy through:
```
GET /api/docs/view?url=<cloudinary_url>
```
Returns a `302` redirect to a 1-hour signed URL.

### Expiry Check Scheduler
Runs daily at 08:00 (APScheduler, starts with the server).  
Checks all active fleet vehicles — sends alerts at 30 days and 7 days before expiry, marks inactive if expired.  
Trigger manually for testing: `POST /api/fleet/run-expiry-check`

---

## Project Structure
```
truck_app/
├── app/
│   ├── main.py              # App entry point, lifespan, router registration
│   ├── config.py            # Settings (loaded from .env)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models/
│   │   ├── kyc.py           # CustomerKYC, CompanyKYC, OwnerKYC, OTPStore
│   │   ├── consent.py       # ConsentLog
│   │   ├── fleet.py         # Fleet
│   │   └── vehicle_type.py  # VehicleType (master table)
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # One file per feature
│   └── utils/
│       ├── cloudinary_client.py  # Upload + signed URL generation
│       ├── expiry_checker.py     # Document expiry logic
│       ├── notifier.py           # SMS/email (console in DEV_MODE)
│       ├── pdf_generator.py      # Consent PDF (ReportLab)
│       └── scheduler.py          # APScheduler setup
├── alembic/
│   ├── env.py               # Imports all models for autogenerate
│   └── versions/            # Migration files (commit these)
├── _migrate.py              # Called by lifespan — auto-generate + upgrade
├── .env                     # Local secrets (gitignored)
├── .env.example             # Template with shared dev credentials
└── start.ps1                # Alternative: runs migrations then uvicorn
```

---

## API Endpoints

### Individual KYC — Story 1
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/kyc/send-otp` | Send OTP (`dev_otp` returned in DEV_MODE) |
| POST | `/api/kyc/verify-otp` | Verify OTP |
| POST | `/api/kyc/register` | Register individual KYC |
| POST | `/api/kyc/upload-id/{id}` | Upload ID proof (JPG/PNG/PDF) |
| GET  | `/api/kyc/status/{id}` | Get KYC status |

**Register request fields:** `first_name`, `middle_name` (opt), `last_name`, `date_of_birth`, `mobile`, `email`, `address_1`, `address_2` (opt), `city` (opt), `state` (opt), `zip_code` (opt), `customer_type` (`"Individual"` or `"Company"`)

**Status response fields:** `id`, `first_name`, `last_name`, `mobile`, `email`, `address_1`, `address_2`, `city`, `state`, `zip_code`, `customer_type`, `status`, `otp_verified`

### Company KYC — Story 2
> Requires an Individual KYC with `customer_type = "Company"` first.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/company-kyc/register` | Register company (requires `customer_kyc_id`) |
| POST | `/api/company-kyc/upload-docs/{id}` | Upload incorporation cert + GST certificate |
| GET  | `/api/company-kyc/status/{id}` | Get status |

**`contact_person_mobile`** accepts both:
- Mobile: 10 digits starting with 6–9 (e.g. `9876543210`)
- Landline: 11 digits starting with `0` (e.g. `01140001234`)

### Owner KYC — Story 3
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/owner-kyc/register` | Register truck owner |
| POST | `/api/owner-kyc/upload-docs/{id}` | Upload driving license + owner ID |
| GET  | `/api/owner-kyc/status/{id}` | Get status |

**Register request fields:** `first_name`, `middle_name` (opt), `last_name`, `date_of_birth`, `mobile`, `email`, `company_name` (opt), `address_1`, `address_2` (opt), `city` (opt), `state` (opt), `zip_code` (opt)

**Status response fields:** `id`, `first_name`, `last_name`, `mobile`, `email`, `company_name`, `address_1`, `address_2`, `city`, `state`, `zip_code`, `driving_license_url`, `owner_id_url`, `status`, `otp_verified`

### Digital Consent — Story 4
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/consent/submit` | Submit consent (IP + user-agent captured server-side) |
| GET  | `/api/consent/status/{customer_kyc_id}` | Check consent status |
| GET  | `/api/consent/pdf/{consent_id}` | Download consent PDF |

### Admin Review — Story 5
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/admin/kyc/pending` | List all pending KYC records |
| GET  | `/api/admin/kyc/customer/{id}` | Individual KYC detail |
| POST | `/api/admin/kyc/customer/{id}/review` | Approve or reject |
| GET  | `/api/admin/kyc/company/{id}` | Company KYC detail |
| POST | `/api/admin/kyc/company/{id}/review` | Approve or reject |
| GET  | `/api/admin/kyc/owner/{id}` | Owner KYC detail |
| POST | `/api/admin/kyc/owner/{id}/review` | Approve or reject |

### Fleet Registration — Story 6
> Owner KYC must be `Verified` before registering vehicles.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/fleet/register` | Register a vehicle |
| POST | `/api/fleet/upload-docs/{fleet_id}` | Upload RC book + insurance (with optional expiry dates) |
| GET  | `/api/fleet/owner/{owner_kyc_id}` | List owner's active vehicles |
| GET  | `/api/fleet/{fleet_id}` | Single vehicle detail |

### Vehicle Type Management — Story 7
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/vehicle-types` | List active vehicle types (public, for dropdowns) |
| GET  | `/api/admin/vehicle-types` | List all types including inactive |
| POST | `/api/admin/vehicle-types` | Create new vehicle type |
| PUT  | `/api/admin/vehicle-types/{id}` | Update vehicle type |
| DELETE | `/api/admin/vehicle-types/{id}` | Deactivate vehicle type |

### Fleet Document Expiry Tracking — Story 8
> Scheduler runs daily at 08:00. Alerts sent at 30 and 7 days before expiry. Vehicle marked inactive if any document expires.

| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT  | `/api/fleet/{fleet_id}/expiry-dates` | Set/update RC, insurance, permit, PUC expiry dates |
| POST | `/api/fleet/run-expiry-check` | Manually trigger expiry check (use for testing) |

### Document Proxy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docs/view?url=<cloudinary_url>` | Proxy any KYC/fleet document via signed URL |

---

## Validation Rules
| Field | Rule |
|-------|------|
| Mobile (individual / owner) | 10-digit Indian number starting with 6–9 |
| Contact person number (company) | 10-digit mobile (6–9 start) **or** 11-digit landline starting with `0` |
| GST Number | 15-character Indian GST format |
| Pincode | 6-digit Indian pincode |
| Registration Number | Indian format e.g. `MH12AB1234` |
| Vehicle Type | Must exist and be active in VEHICLE_TYPE table |
| Max Load Capacity | Must be > 0 if provided |

---

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary API secret |
| `SECRET_KEY` | Yes | App secret key |
| `DEV_MODE` | No | Default `true` — skips real SMS/email |
| `MSG91_API_KEY` | No | Required only when `DEV_MODE=false` |
| `SENDGRID_API_KEY` | No | Required only when `DEV_MODE=false` |
| `SENDGRID_FROM_EMAIL` | No | Required only when `DEV_MODE=false` |
