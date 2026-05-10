# GoGoTruk API

## Tech Stack
- **Backend:** Python 3.11+ / FastAPI
- **Database:** PostgreSQL (Supabase Cloud — shared by all teammates)
- **Migrations:** Alembic
- **File Storage:** Cloudinary
- **ORM:** SQLAlchemy

---

## Onboarding a New Machine (5 steps)

### 1 — Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings "pydantic[email]" python-multipart cloudinary alembic reportlab
```

### 2 — Set Up `.env`
```bash
# from the truck_app directory
cp .env.example .env
```
All values in `.env.example` are pre-filled for the shared dev DB.  
Only `SUPABASE_KEY` needs to be filled — get it from the Supabase dashboard:  
**Settings → API → anon public key**

### 3 — Apply DB Migrations
```bash
# from truck_app/
alembic upgrade head
```
> First time connecting to the existing shared Supabase DB (tables already exist)?  
> Run `alembic stamp head` instead — this tells Alembic the DB is already up to date.

### 4 — (Optional) Seed Test Data
```bash
python seed.py
```
Inserts 3 sample KYC records. Safe to run multiple times — skips existing records.

### 5 — Run the App
```bash
# from truck_app/
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

---

## DEV_MODE

Set `DEV_MODE=true` in `.env` (default) to skip real SMS/email:
- OTP is auto-verified and returned in the API response as `dev_otp`
- Notifications print to the terminal instead of calling MSG91/SendGrid

Set `DEV_MODE=false` for staging/production — requires valid `MSG91_API_KEY` and `SENDGRID_API_KEY`.

---

## Adding Schema Changes (Migrations Workflow)

When you add a column, new table, or change a model:

```bash
# 1. Make your changes in app/models/
# 2. Generate the migration
alembic revision --autogenerate -m "describe_what_changed"

# 3. Apply it locally
alembic upgrade head

# 4. Commit the generated file
git add alembic/versions/
git commit -m "add migration: describe_what_changed"
```

Teammates then run `alembic upgrade head` to pick up the change — no manual SQL needed.

---

## Document Proxy

Cloudinary document URLs require authentication. Never use raw Cloudinary URLs directly in the UI. Instead, wrap any stored document URL through the proxy endpoint:

```
GET /api/docs/view?url=<cloudinary_url>
```

Returns a `302` redirect to a short-lived (1 hour) signed URL.

```js
// Example — open a document in a new tab
window.open(`/api/docs/view?url=${encodeURIComponent(record.id_proof_url)}`)
```

---

## API Endpoints

### Individual KYC (Story 1)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/kyc/send-otp` | Send OTP to mobile (returns `dev_otp` in DEV_MODE) |
| POST | `/api/kyc/verify-otp` | Verify OTP |
| POST | `/api/kyc/register` | Register individual KYC |
| POST | `/api/kyc/upload-id/{id}` | Upload ID proof (JPG, PNG, PDF) |
| GET  | `/api/kyc/status/{id}` | Get KYC status |

### Company KYC (Story 2)
> Requires an Individual KYC record with `customer_type = "Company"` first.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/company-kyc/register` | Register company KYC (requires `customer_kyc_id`) |
| POST | `/api/company-kyc/upload-docs/{id}` | Upload incorporation cert + GST certificate |
| GET  | `/api/company-kyc/status/{id}` | Get company KYC status |

### Owner KYC (Story 3)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/owner-kyc/register` | Register truck owner KYC |
| POST | `/api/owner-kyc/upload-docs/{id}` | Upload driving license + owner ID |
| GET  | `/api/owner-kyc/status/{id}` | Get owner KYC status |

### Digital Consent (Story 4)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/consent/submit` | Submit consent (IP + user-agent captured server-side) |
| GET  | `/api/consent/status/{customer_kyc_id}` | Check consent status |
| GET  | `/api/consent/pdf/{consent_id}` | Download consent PDF |

### Admin Review (Story 5)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/admin/pending` | List all pending KYC records (individual + company + owner) |
| GET  | `/api/admin/individual/{id}` | View individual KYC detail |
| POST | `/api/admin/individual/{id}/review` | Approve or reject individual KYC |
| GET  | `/api/admin/company/{id}` | View company KYC detail |
| POST | `/api/admin/company/{id}/review` | Approve or reject company KYC |
| GET  | `/api/admin/owner/{id}` | View owner KYC detail |
| POST | `/api/admin/owner/{id}/review` | Approve or reject owner KYC |

### Document Proxy
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/docs/view?url=<cloudinary_url>` | Stream any KYC document via signed URL |
