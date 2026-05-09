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
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings "pydantic[email]" python-multipart cloudinary alembic
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

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/kyc/send-otp` | Send OTP to mobile |
| POST | `/api/kyc/verify-otp` | Verify OTP |
| POST | `/api/kyc/register` | Register KYC |
| POST | `/api/kyc/upload-id/{id}` | Upload ID proof |
| GET | `/api/kyc/status/{id}` | Check KYC status |
