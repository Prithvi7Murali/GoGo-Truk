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
| Background Jobs | APScheduler + FastAPI BackgroundTasks |
| Async Tasks | Celery + Redis (optional — falls back to BackgroundTasks) |
| Notifications | MSG91 (SMS) + SendGrid (email) |

---

## Onboarding (4 steps)

### 1 — Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings "pydantic[email]" python-multipart cloudinary alembic reportlab apscheduler celery redis
```

### 2 — Set Up `.env`
```bash
# from truck_app/
copy .env.example .env
```
All values in `.env.example` are pre-filled for the shared dev DB.

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
| Notifications | Printed to terminal | Real SMS + email via MSG91/SendGrid |
| Invoices | PDF generated and uploaded to Cloudinary | Same + email sent to customer |

### Document Proxy
Cloudinary URLs require auth. Never use raw Cloudinary URLs in the frontend.
Always proxy through:
```
GET /api/docs/view?url=<cloudinary_url>
```
Returns a `302` redirect to a 1-hour signed URL. Works for KYC docs, fleet docs, and invoice PDFs.

### Background Jobs (APScheduler)
Both jobs start automatically with the server:

| Job | Schedule | Action |
|-----|----------|--------|
| Expiry check | Daily at 08:00 | Alerts at 30 and 7 days before expiry, marks vehicle inactive if expired |
| Auto-reject | Every 10 minutes | Rejects bookings with no owner response within 2 hours |

### Celery (Optional)
If `REDIS_URL` is set, Celery is used for async notification delivery. Without it, FastAPI BackgroundTasks handles notifications — no setup needed for dev.

To run a Celery worker (production):
```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

### Enum Columns — Important Note
All status/type columns use `String` (not PostgreSQL native enum) to avoid SQLAlchemy name/value mismatch issues. Pydantic handles validation at the API boundary.

---

## Project Structure
```
truck_app/
├── app/
│   ├── main.py              # App entry point, lifespan, router registration
│   ├── config.py            # Settings (loaded from .env)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── celery_app.py        # Celery instance (active only when REDIS_URL is set)
│   ├── models/
│   │   ├── kyc.py           # CustomerKYC, CompanyKYC, OwnerKYC, OTPStore
│   │   ├── consent.py       # ConsentLog
│   │   ├── fleet.py         # Fleet
│   │   ├── vehicle_type.py  # VehicleType (master table)
│   │   ├── availability.py  # Availability
│   │   ├── booking.py       # Booking
│   │   ├── rate_card.py     # RateCard
│   │   ├── invoice.py       # Invoice
│   │   └── cancellation.py  # CancellationLog
│   ├── schemas/             # Pydantic request/response models
│   ├── routers/             # One file per feature
│   ├── tasks/
│   │   └── booking_tasks.py # Celery tasks for notifications + auto-reject
│   └── utils/
│       ├── cloudinary_client.py  # Upload + signed URL generation
│       ├── expiry_checker.py     # Document expiry logic
│       ├── notifier.py           # SMS/email (console in DEV_MODE)
│       ├── pdf_generator.py      # Consent PDF (ReportLab)
│       ├── invoice_pdf.py        # GST invoice PDF (ReportLab)
│       ├── pricing.py            # Pricing engine + GST calculator
│       ├── cache.py              # Redis cache + distributed lock
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

**Register fields:** `first_name`, `middle_name` (opt), `last_name`, `date_of_birth`, `mobile`, `email`, `address_1`, `address_2` (opt), `city` (opt), `state` (opt), `zip_code` (opt), `customer_type` (`"Individual"` or `"Company"`)

### Company KYC — Story 2
> Requires Individual KYC with `customer_type = "Company"` first.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/company-kyc/register` | Register company (requires `customer_kyc_id`) |
| POST | `/api/company-kyc/upload-docs/{id}` | Upload incorporation cert + GST certificate |
| GET  | `/api/company-kyc/status/{id}` | Get status |

`contact_person_mobile` accepts 10-digit mobile (starts 6–9) **or** 11-digit landline (starts with `0`).

### Owner KYC — Story 3
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/owner-kyc/register` | Register truck owner |
| POST | `/api/owner-kyc/upload-docs/{id}` | Upload driving license + owner ID |
| GET  | `/api/owner-kyc/status/{id}` | Get status |

**Register fields:** `first_name`, `middle_name` (opt), `last_name`, `date_of_birth`, `mobile`, `email`, `company_name` (opt), `address_1`, `address_2` (opt), `city` (opt), `state` (opt), `zip_code` (opt)

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
| POST | `/api/admin/kyc/customer/{id}/review` | Approve or reject — body: `{ "action": "Verified"/"Rejected", "remarks": "..." }` |
| GET  | `/api/admin/kyc/company/{id}` | Company KYC detail |
| POST | `/api/admin/kyc/company/{id}/review` | Approve or reject |
| GET  | `/api/admin/kyc/owner/{id}` | Owner KYC detail |
| POST | `/api/admin/kyc/owner/{id}/review` | Approve or reject |

### Fleet Registration — Story 6
> Owner KYC must be `Verified` before registering vehicles.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/fleet/register` | Register a vehicle |
| POST | `/api/fleet/upload-docs/{fleet_id}` | Upload RC book, insurance, permit, PUC (with optional expiry dates) |
| GET  | `/api/fleet/owner/{owner_kyc_id}` | List owner's active vehicles |
| GET  | `/api/fleet/{fleet_id}` | Single vehicle detail |

**Register fields:** `owner_kyc_id`, `vehicle_type`, `registration_number` (Indian format e.g. `MH12AB1234`), `engine_number`, `chassis_number`, `description` (opt), `max_load_capacity` (opt, float), `dimensions` (opt)

### Vehicle Type Management — Story 7
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/vehicle-types` | List active vehicle types (public, for dropdowns) |
| GET  | `/api/admin/vehicle-types` | All types including inactive |
| POST | `/api/admin/vehicle-types` | Create new vehicle type |
| PUT  | `/api/admin/vehicle-types/{id}` | Update (set `is_active: true` to reactivate) |
| DELETE | `/api/admin/vehicle-types/{id}` | Soft-deactivate |

Seeded types: Mini Truck, Medium Truck, Large Truck, Container 20ft, Container 40ft

### Fleet Document Expiry Tracking — Story 8
> Scheduler runs daily at 08:00. Alerts at 30 and 7 days. Vehicle marked inactive on expiry.

| Method | Endpoint | Description |
|--------|----------|-------------|
| PUT  | `/api/fleet/{fleet_id}/expiry-dates` | Set/update RC, insurance, permit, PUC expiry dates |
| POST | `/api/fleet/run-expiry-check` | Manually trigger expiry check (testing) |

### Truck Availability — Story 9
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/availability` | Set availability — bulk dates, single city/state |
| GET  | `/api/availability/fleet/{fleet_id}` | List a truck's availability (opt: `?status=Available`) |
| GET  | `/api/availability/search` | Search by `?city=&state=&date=` |
| PUT  | `/api/availability/{id}` | Update date, city, state, or status |
| DELETE | `/api/availability/{id}` | Delete slot (blocked if Booked) |
| POST | `/api/availability/{id}/book` | Atomically mark slot as Booked |
| POST | `/api/availability/{id}/release` | Release Booked slot back to Available |

**Status values:** `Available`, `Booked`, `Cancelled`

### Search Available Trucks — Story 10
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search/trucks` | Search with filters + pagination |

**Query params:** `city`, `state`, `date`, `date_from`, `date_to`, `page` (default 1), `page_size` (default 10, max 50)

Results cached in Redis for 5 minutes. Only `Available` slots returned.

### Create Booking — Story 12
> Customer KYC must be `Verified` to book.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings` | Create booking — atomically locks availability slot |
| GET  | `/api/bookings/{booking_id}` | Get booking detail |
| GET  | `/api/bookings/customer/{customer_kyc_id}` | List customer's bookings |
| GET  | `/api/bookings/owner/{owner_kyc_id}` | List all bookings across owner's fleet |

**Create fields:** `customer_kyc_id`, `availability_id`, `pickup_address`, `destination_address`, `goods_type`, `goods_weight_kg`, `declaration_accepted` (must be `true`)

**Booking statuses:** `Pending` → `Confirmed` / `Rejected` / `Cancelled` / `Completed`

### Booking Confirmation — Story 13
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bookings/{booking_id}/review` | Owner accepts or rejects — body: `{ "action": "Confirmed"/"Rejected", "reason": "..." }` |

- `reason` required when action is `"Rejected"`
- Bookings not reviewed within 2 hours are auto-rejected (APScheduler + Celery)
- `owner_response_deadline` returned in BookingResponse for countdown display

### Pricing & Invoice — Story 14
> Rate cards must be seeded before any invoice can be generated.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/rate-cards` | List active rate cards (public) |
| GET  | `/api/admin/rate-cards` | All rate cards including inactive |
| POST | `/api/admin/rate-cards` | Create rate card |
| PUT  | `/api/admin/rate-cards/{id}` | Update rate/base fare/active flag |
| POST | `/api/invoices/preview` | Pricing preview — no invoice created |
| POST | `/api/invoices/generate` | Generate GST invoice + PDF + email customer |
| GET  | `/api/invoices/{invoice_id}` | Get invoice detail |
| GET  | `/api/invoices/booking/{booking_id}` | Get invoice for a booking |
| GET  | `/api/invoices/{invoice_id}/pdf` | Stream invoice PDF |

**GST types:** `CGST+SGST` (intrastate) or `IGST` (interstate). Rates: `0`, `5`, `12`, `18` (5% standard for GTA freight).

Invoice number format: `INV-YYYYMMDD-000001`

### Booking Cancellation — Story 15
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/bookings/{booking_id}/cancellation-preview` | Preview charge before cancelling |
| POST | `/api/bookings/{booking_id}/cancel` | Cancel booking — body: `{ "cancelled_by": "Customer"/"Owner", "reason": "..." }` |
| GET  | `/api/bookings/{booking_id}/cancellation` | Get cancellation record |

**Cancellation charge rules:**
| Booking Status | Hours Before Pickup | Charge |
|----------------|---------------------|--------|
| Pending | Any | 0% |
| Confirmed | > 48 hours | 0% |
| Confirmed | 24–48 hours | 25% of invoice total |
| Confirmed | < 24 hours | 50% of invoice total |

On cancel: slot released to Available, search cache invalidated, both parties notified via SMS.

### Document Proxy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docs/view?url=<cloudinary_url>` | Proxy any document or invoice PDF via signed URL |

---

## Database Tables
| Table | Story | Description |
|-------|-------|-------------|
| `CUSTOMER_KYC` | 1 | Individual customers |
| `COMPANY_KYC` | 2 | Company details linked to customer |
| `OWNER_KYC` | 3 | Truck owners |
| `OTP_STORE` | 1 | OTP records |
| `CONSENT_LOG` | 4 | Digital consent records |
| `FLEET` | 6 | Registered vehicles |
| `VEHICLE_TYPE` | 7 | Master list of vehicle types |
| `AVAILABILITY` | 9 | Truck availability slots |
| `BOOKING` | 12 | Booking records |
| `CANCELLATION_LOG` | 15 | Cancellation + refund records |
| `RATE_CARD` | 14 | Pricing slabs per vehicle type |
| `INVOICE` | 14 | GST invoices |

---

## Validation Rules
| Field | Rule |
|-------|------|
| Mobile (individual / owner) | 10-digit Indian number starting with 6–9 |
| Contact person number (company) | 10-digit mobile **or** 11-digit landline starting with `0` |
| GST Number | 15-character Indian GST format |
| Pincode | 6-digit Indian pincode |
| Registration Number | Indian format e.g. `MH12AB1234` |
| Vehicle Type | Must exist and be active in VEHICLE_TYPE table |
| Availability Dates | Cannot be in the past; no duplicates for same truck |
| Goods Weight | Must be > 0 |
| GST Rate | Must be 0, 5, 12, or 18 |
| Declaration | Must be `true` to create a booking |

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
| `MSG91_API_KEY` | No | Required when `DEV_MODE=false` |
| `SENDGRID_API_KEY` | No | Required when `DEV_MODE=false` |
| `SENDGRID_FROM_EMAIL` | No | Required when `DEV_MODE=false` |
| `REDIS_URL` | No | Enables Redis caching + Celery async tasks |
| `FCM_SERVER_KEY` | No | Firebase push notifications to owners |
| `SUPABASE_URL` | No | Not used in current endpoints |
| `SUPABASE_KEY` | No | Not used in current endpoints |
