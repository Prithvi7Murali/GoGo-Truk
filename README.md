# \# 🚛 GoGoTruk API

# 

# A logistics platform connecting truck owners and fleet operators with customers who need freight and transport services across India.

# 

# \---

# 

# \## 📁 Project Structure

# 

# ```

# GoGo-Truk/

# └── truck\_app/

# &#x20;   ├── .env                  ← Environment variables

# &#x20;   └── app/

# &#x20;       ├── main.py           ← FastAPI app entry point

# &#x20;       ├── config.py         ← Settings from .env

# &#x20;       ├── database.py       ← SQLAlchemy DB connection

# &#x20;       ├── models/

# &#x20;       │   └── kyc.py        ← CustomerKYC \& OTPStore DB models

# &#x20;       ├── routers/

# &#x20;       │   └── kyc.py        ← API endpoints

# &#x20;       ├── schemas/

# &#x20;       │   └── kyc.py        ← Pydantic request/response schemas

# &#x20;       ├── services/

# &#x20;       │   └── kyc\_service.py

# &#x20;       └── utils/

# &#x20;           └── minio\_client.py ← MinIO file upload utility

# ```

# 

# \---

# 

# \## ⚙️ Tech Stack

# 

# | Layer | Technology |

# |-------|-----------|

# | Language | Python 3.11+ |

# | Framework | FastAPI |

# | Database | PostgreSQL |

# | ORM | SQLAlchemy |

# | Validation | Pydantic |

# | File Storage | MinIO |

# | Auth | Supabase Auth |

# | Task Queue | Celery + Redis |

# 

# \---

# 

# \## 🚀 Getting Started

# 

# \### Step 1 — Clone the Repository

# 

# ```bash

# git clone https://github.com/Prithvi7Murali/GoGo-Truk.git

# cd GoGo-Truk/truck\_app

# ```

# 

# \---

# 

# \### Step 2 — Install Dependencies

# 

# ```bash

# pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings pydantic\[email] python-multipart minio

# ```

# 

# \---

# 

# \### Step 3 — Configure Environment Variables

# 

# The `.env` file is located at `truck\_app/.env`. Update the values as needed:

# 

# ```env

# DATABASE\_URL=postgresql://postgres:password@localhost:5432/gogotruk

# MINIO\_ENDPOINT=localhost:9000

# MINIO\_ACCESS\_KEY=minioadmin

# MINIO\_SECRET\_KEY=minioadmin

# MINIO\_BUCKET=gogotruk-kyc

# SECRET\_KEY=gogotruk-super-secret-key-2026

# SUPABASE\_URL=https://your-project.supabase.co

# SUPABASE\_KEY=your-anon-key

# ```

# 

# \---

# 

# \### Step 4 — Setup PostgreSQL Database in pgAdmin

# 

# 1\. Open \*\*pgAdmin\*\*

# 2\. Right click \*\*Servers → Register → Server\*\*

# 3\. Fill in the connection details:

# 

# | Field | Value |

# |-------|-------|

# | Name | GoGoTruk |

# | Host | localhost |

# | Port | 5432 |

# | Username | postgres |

# | Password | password |

# 

# 4\. Click \*\*Save\*\*

# 5\. Right click \*\*Databases → Create → Database\*\*

# 6\. Set database name: `gogotruk`

# 7\. Click \*\*Save\*\*

# 

# > ✅ Tables are auto-created when the app starts via SQLAlchemy `Base.metadata.create\_all()`

# 

# \---

# 

# \### Step 5 — Run the Application

# 

# ```bash

# cd truck\_app

# uvicorn app.main:app --reload

# ```

# 

# Expected output:

# ```

# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

# INFO:     Started reloader process

# INFO:     Application startup complete.

# ```

# 

# \---

# 

# \### Step 6 — Open Swagger UI

# 

# Open your browser and navigate to:

# 

# ```

# http://127.0.0.1:8000/docs

# ```

# 

# Alternative ReDoc UI:

# ```

# http://127.0.0.1:8000/redoc

# ```

# 

# \---

# 

# \## 🔌 API Endpoints

# 

# \### Base URL

# ```

# http://127.0.0.1:8000

# ```

# 

# \### Health Check

# ```

# GET /

# ```

# Response:

# ```json

# {

# &#x20; "message": "GoGoTruk API is running!"

# }

# ```

# 

# \---

# 

# \## 🧪 Testing the KYC APIs

# 

# Follow these steps \*\*in order\*\* to test the full KYC registration flow:

# 

# \---

# 

# \### Step 1 — Send OTP

# 

# ```

# POST /api/kyc/send-otp

# ```

# 

# Request Body:

# ```json

# {

# &#x20; "mobile": "9876543210"

# }

# ```

# 

# Response:

# ```json

# {

# &#x20; "message": "OTP sent successfully",

# &#x20; "dev\_otp": "123456"

# }

# ```

# 

# > ⚠️ In development, the OTP is returned in the response and printed in the terminal. In production it will be sent via MSG91 SMS gateway.

# 

# \---

# 

# \### Step 2 — Verify OTP

# 

# ```

# POST /api/kyc/verify-otp

# ```

# 

# Request Body:

# ```json

# {

# &#x20; "mobile": "9876543210",

# &#x20; "otp": "123456"

# }

# ```

# 

# > Replace `123456` with the OTP received from Step 1.

# 

# Response:

# ```json

# {

# &#x20; "message": "OTP verified successfully"

# }

# ```

# 

# \---

# 

# \### Step 3 — Register KYC

# 

# ```

# POST /api/kyc/register

# ```

# 

# Request Body:

# ```json

# {

# &#x20; "first\_name": "John",

# &#x20; "middle\_name": "A",

# &#x20; "last\_name": "Doe",

# &#x20; "date\_of\_birth": "1990-01-15",

# &#x20; "mobile": "9876543210",

# &#x20; "email": "john@example.com",

# &#x20; "address\_1": "123 Main Street",

# &#x20; "address\_2": "Bangalore",

# &#x20; "address\_3": "Karnataka",

# &#x20; "customer\_type": "Individual"

# }

# ```

# 

# > `customer\_type` must be either `Individual` or `Company`

# 

# Response:

# ```json

# {

# &#x20; "id": 1,

# &#x20; "first\_name": "John",

# &#x20; "last\_name": "Doe",

# &#x20; "mobile": "9876543210",

# &#x20; "email": "john@example.com",

# &#x20; "status": "Pending",

# &#x20; "otp\_verified": "true"

# }

# ```

# 

# \---

# 

# \### Step 4 — Upload ID Proof (Requires MinIO)

# 

# ```

# POST /api/kyc/upload-id/{kyc\_id}

# ```

# 

# \- Replace `{kyc\_id}` with the `id` returned from Step 3

# \- Upload a file (JPG, PNG or PDF only)

# \- Use \*\*form-data\*\* in Postman or Swagger UI

# 

# > ⚠️ This endpoint requires MinIO to be running. Skip during initial testing.

# 

# \---

# 

# \### Step 5 — Check KYC Status

# 

# ```

# GET /api/kyc/status/{kyc\_id}

# ```

# 

# \- Replace `{kyc\_id}` with the `id` from Step 3

# 

# Response:

# ```json

# {

# &#x20; "id": 1,

# &#x20; "first\_name": "John",

# &#x20; "last\_name": "Doe",

# &#x20; "mobile": "9876543210",

# &#x20; "email": "john@example.com",

# &#x20; "status": "Pending",

# &#x20; "otp\_verified": "true"

# }

# ```

# 

# \---

# 

# \## 🗄️ Verify Data in pgAdmin

# 

# After testing the APIs, run these queries in pgAdmin \*\*Query Tool\*\* to verify data:

# 

# ```sql

# \-- Check registered customers

# SELECT \* FROM "CUSTOMER\_KYC";

# 

# \-- Check OTP records

# SELECT \* FROM "OTP\_STORE";

# ```

# 

# \---

# 

# \## 🗃️ Database Models

# 

# \### CUSTOMER\_KYC Table

# 

# | Column | Type | Description |

# |--------|------|-------------|

# | id | Integer | Primary key |

# | first\_name | String(100) | Customer first name |

# | middle\_name | String(100) | Optional middle name |

# | last\_name | String(100) | Customer last name |

# | date\_of\_birth | Date | Date of birth |

# | mobile | String(15) | Unique mobile number |

# | email | String(255) | Unique email address |

# | address\_1 | String(255) | Primary address |

# | address\_2 | String(255) | Optional address line 2 |

# | address\_3 | String(255) | Optional address line 3 |

# | customer\_type | String(50) | Individual or Company |

# | id\_proof\_url | String(500) | MinIO file path |

# | otp\_verified | String(5) | true or false |

# | status | Enum | Pending / Verified / Rejected |

# | created\_at | DateTime | Auto timestamp |

# | updated\_at | DateTime | Auto updated timestamp |

# 

# \### OTP\_STORE Table

# 

# | Column | Type | Description |

# |--------|------|-------------|

# | id | Integer | Primary key |

# | mobile | String(15) | Mobile number |

# | otp | String(6) | 6-digit OTP |

# | is\_verified | String(5) | true or false |

# | created\_at | DateTime | Auto timestamp |

# 

# \---

# 

# \## ✅ Validation Rules

# 

# | Field | Rule |

# |-------|------|

# | mobile | Must be a valid 10-digit Indian number starting with 6-9 |

# | customer\_type | Must be `Individual` or `Company` |

# | email | Must be a valid email format |

# | id\_proof file | Must be JPG, PNG or PDF only |

# 

# \---

# 

# \## 🔮 Upcoming Features (Roadmap)

# 

# \- \[ ] Story 2 — Company KYC Registration

# \- \[ ] Story 3 — Truck Owner KYC Registration

# \- \[ ] Story 4 — Customer Digital Consent

# \- \[ ] Story 5 — Admin KYC Approval Panel

# \- \[ ] Story 6 — Fleet Vehicle Registration

# \- \[ ] Story 9 — Truck Availability Management

# \- \[ ] Story 10 — Search Available Trucks

# \- \[ ] Story 12 — Create Booking Request

# \- \[ ] Story 14 — Pricing \& Invoice Generation

# \- \[ ] Story 16 — Admin Dashboard

# 

# \---

# 

# \## 💰 Monthly Cost

# 

# | Item | Cost |

# |------|------|

# | Hetzner CX21 VPS | \~Rs. 400 |

# | Domain Name | \~Rs. 100 |

# | SMS - MSG91 | \~Rs. 150 |

# | All other tools | Rs. 0 |

# | \*\*TOTAL\*\* | \*\*\~Rs. 650/month\*\* |

# 

# \---

# 

# \## 📞 Support

# 

# For any issues or questions, raise a GitHub issue or contact the development team.

