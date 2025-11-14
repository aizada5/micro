Software Architecture
Assignment 4 - Deploying a FastAPI Application with MongoDB Atlas and Render
Public GitHub/GitLab repository URL: https://github.com/aizada5/micro
Live Render URL: https://micro-0gg1.onrender.com
Swagger UI: https://micro-0gg1.onrender.com/docs#/default/health_check_health_db_get
Deployment Write-up
Student: Aizada
Project: User Authentication and QR Code Microservice
Deployment Platform: Render (Docker)
Database: MongoDB Atlas (M0 Cluster)
 
Project Overview
This microservice provides user management, JWT-based authentication, and QR code generation capabilities. It is built with FastAPI, uses MongoDB Atlas for data persistence, and is deployed on Render using Docker containers.
Issues Encountered and Solutions
1. TLS/SSL Certificate Issues with MongoDB Atlas
When initially deploying to Render, the application failed to connect to MongoDB Atlas with SSL/TLS certificate verification errors. The connection was timing out or throwing certificate validation errors.
It  is because Docker containers by default may not include the necessary CA certificates required to verify SSL/TLS connections to MongoDB Atlas, which uses encrypted connections.
So to solve that I updated the Dockerfile to explicitly install system certificates before running the application:
# Install system certificates (REQUIRED for MongoDB Atlas SSL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*
Result: MongoDB Atlas connection now works reliably with proper SSL/TLS encryption.
2. Bcrypt Password Hashing - 72 Byte Limitation
The application crashed during user registration with the error:
ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
It was because Bcrypt algorithm has a built-in limitation of 72 bytes for password length. The passlib library was attempting to verify this during initialization, causing crashes even before user input.
What I did to solve this:
Step 1: Updated password hashing functions to truncate passwords:
def hash_password(password: str) -> str:
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate password to 72 bytes for bcrypt compatibility
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)
Step 2: Updated CryptContext configuration:
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True
)
Password hashing now works correctly with automatic truncation for edge cases.
3. Python Library Version Compatibility Issues
Multiple dependency conflicts occurred during deployment:
Issue A: passlib[bcrypt] version conflict
AttributeError: module 'bcrypt' has no attribute '__about__'
Issue B: motor and pymongo incompatibility
ImportError: cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'
It was because:
•	Newer versions of dependencies had breaking changes
•	motor 3.3.2 was incompatible with pymongo 4.15.4
•	passlib[bcrypt] notation was pulling incompatible bcrypt versions
So  I: Pinned specific compatible versions in requirements.txt:
# Before (problematic):
motor==3.3.2
passlib[bcrypt]==1.7.4

# After (fixed):
pymongo==4.5.0
motor==3.3.1
passlib==1.7.4
bcrypt==4.0.1
Key Changes:
•	Downgraded motor from 3.3.2 to 3.3.1 (stable version)
•	Explicitly pinned pymongo==4.5.0 (compatible with motor 3.3.1)
•	Separated passlib and bcrypt dependencies with specific versions
•	Removed bracket notation [bcrypt] to avoid automatic version resolution
All dependencies now install and work together without conflicts.

Testing Results
Health Check Endpoint
Endpoint: GET /health/db
Response:
{
  "status": "healthy",
  "database": "connected",
  "service": "User/Auth/QR Microservice"
}
Status: Working - MongoDB connection verified

User Registration
Endpoint: POST /auth/register
Test Input:
{
  "username": "Yerkanat",
  "email": "yerkanat@gmail.com",
  "password": "yerkanat01",
  "full_name": "Yerkanat Malayev",
  "role": "student"
}
Response:
{
  "id": "6916cbc709d9eedb316de5c3",
  "username": "Yerkanat",
  "email": "yerkanat@gmail.com",
  "full_name": "Yerkanat Malayev",
  "role": "student",
  "created_at": "2025-11-14T06:27:19.247455",
  "qr_code": null
}
Status: Working - User created in MongoDB

Authentication
Endpoint: POST /auth/login
Test Input:
{
  "email": "yerkanat@gmail.com",
  "password": "yerkanat01"
}
Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
Status: Working - JWT token generated successfully

Protected Endpoints
Endpoint: GET /users/me
Authorization: Bearer token required
Response:
{
  "id": "6916cbc709d9eedb316de5c3",
  "username": "Yerkanat",
  "email": "yerkanat@gmail.com",
  "full_name": "Yerkanat Malayev",
  "role": "student",
  "created_at": "2025-11-14T06:27:19.247455",
  "qr_code": null
}
Status: Working - JWT authentication verified

QR Code Generation
Endpoint: POST /qr/generate
Authorization: Bearer token required
Response:
{
  "user_id": "6916cbc709d9eedb316de5c3",
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "data": "USER:6916cbc709d9eedb316de5c3|EMAIL:yerkanat@gmail.com|ROLE:student"
}
Status: Working - QR code generated and stored

Deployment Architecture
┌─────────────────┐
│   GitHub Repo   │
│  (Source Code)  │
└────────┬────────┘
         │
         │ (Git Push triggers deployment)
         │
         ▼
┌─────────────────┐
│  Render.com     │
│  (Docker Build) │
│  - Dockerfile   │
│  - Env Vars     │
└────────┬────────┘
         │
         │ (Connects via SSL/TLS)
         │
         ▼
┌─────────────────┐
│  MongoDB Atlas  │
│  (M0 Cluster)   │
│  - Database     │
│  - Collections  │
└─────────────────┘

Conclusion
The deployment was successful after resolving TLS/SSL certificate issues, bcrypt limitations, and dependency version conflicts. The microservice is now fully operational on Render with:
•	Secure MongoDB Atlas connection with SSL/TLS
•	Working user authentication with JWT
•	QR code generation and storage
•	Proper error handling and logging
•	Environment-based configuration
•	Docker containerization
•	All endpoints tested and verified
 C:\Users\A\Desktop\university\3 year\software architecture\user-service X0sx6DSE1ASVM90i
mongodb+srv://u22ayzada_db_user:<db_password>@clusteraizada.t0yilnj.mongodb.net/?appName=ClusterAizada





Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install uvicorn
uvicorn main:app –reload

mongodb+srv://u22ayzada_db_user:<db_password>@clusteraizada.t0yilnj.mongodb.net/?appName=ClusterAizada
 
MONGO_URI=mongodb://localhost:27017
DB_NAME =assignmentdb
JWT_SECRET = aizada100ballmozhnopozhalusta

mongodb+srv://u22ayzada_db_user:< X0sx6DSE1ASVM90i >@clusteraizada.t0yilnj.mongodb.net/?appName=ClusterAizada


aizada
passhundredpoints

mongodb+srv://aizada:passhundredpoints@clusteraizada.t0yilnj.mongodb.net/?appName=ClusterAizada
 
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTE2Y2JjNzA5ZDllZWRiMzE2ZGU1YzMiLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc2MzE4ODA5Mn0.1HMMEr4drkYk6B_xEJ_t8j6nUVUt7TpBptFGxfvSaiY

token yerkanat


{
  "username": "Aizada",
  "email": "aizada@gmail.com",
  "password": "aizada01",
  "full_name": "Aizada Utepova",
  "role": "student"
}

{
  "id": "6916d46db7cac390db7f1017",
  "username": "Aizada",
  "email": "aizada@gmail.com",
  "full_name": "Aizada Utepova",
  "role": "student",
  "created_at": "2025-11-14T07:04:13.991730",
  "qr_code": null
}

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTE2ZDQ2ZGI3Y2FjMzkwZGI3ZjEwMTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc2MzE5MDMyNX0.2Q68CTDgI2idX1Ru3Hlo-QsaD-IyT5owoz7f4dyseTs",
  "token_type": "bearer"
}

          
{
  "username": "admin",
  "email": "admin@gmail.com",
  "password": "admin123",
  "full_name": "Admin Adminov",
  "role": "admin"
}

{
  "id": "6916d6cfb7cac390db7f1018",
  "username": "admin",
  "email": "admin@gmail.com",
  "full_name": "Admin Adminov",
  "role": "admin",
  "created_at": "2025-11-14T07:14:23.583300",
  "qr_code": null
}

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OTE2ZDZjZmI3Y2FjMzkwZGI3ZjEwMTgiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NjMxOTA5Mzd9.fMES8ZdAsq5rakc0t_izX-BinsW4Stsermj6m0vCoPQ",
  "token_type": "bearer"
}

[
  {
    "id": "6916cbc709d9eedb316de5c3",
    "username": "Yerkanat",
    "email": "yerkanat@gmail.com",
    "full_name": "Yerkanat Malayev",
    "role": "student",
    "created_at": "2025-11-14T06:27:19.247000",
    "qr_code": null
  },
  {
    "id": "6916d46db7cac390db7f1017",
    "username": "Aizada",
    "email": "aizada@gmail.com",
    "full_name": "Aizada Utepova",
    "role": "student",
    "created_at": "2025-11-14T07:04:13.991000",
    "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAdYAAAHWAQAAAADiYZX3AAADc0lEQVR4nO2dXW7bMBCEZysBfaQBHyBHoW+QIwW9mXSUHMAA9RhAwvSBv3aKSk0cNxZmH4LI1gdGwGDJHS4VIz4ay48Po4BYsWLFihUrVqxYsWL/IUiSHOplAMjQxfU8BwAc3Bx/pHAkyfkRn1fsfdisqySVJCnPdAnffDZf3fyIzyv2PmyRygygpiU3A54kgC5+G1U3AJCuxH6AnXpwQJoH4TnHz758XLH7ZuMyajGMh8X467CYvZDEePjaccXuiS2JqCOABcD0kwbX0co9xHScDQ6Ab+35R3xesfdlJzMz6wG4N+OAxWqNiPHpLV6amZmdbjiu2H2yKV+1eaij+bDAfADhA+IlUNZctxhX7L7Zi3oQyb+CDx3bAhBAXnhlQvWg2L9FEkkAkt8ZUDzQjmRRGMlkYslnELsaWVcdk3/VGFZkchwc8xToSPntYtejmQd9sdobcQVkEytLqrjxj/i8Yu/DtvOgD3V9VXYKScKHC0LzoNjVqNNd1EvcYwbyjAggT3xXIV2JXWcXiybWy2sPwJH2EgDE/UEsZqeph50AmB1uOK7YXbLVNUCq/XLvQvx2ANAUiqkoVL4SuxK1Hqx2Aoe6Rg95MvQhLa1UD4pdj7peinoZkOUThYTWzoolo3QldjXafBWApqUPAHK+6nJRqHwldlPUehDNDqCbs2uFLssse6XSldj1qP5VbhVlSVAXNmnNYdKV2NWo82Au+7q2+3jImSuJK67vpSuxK/EuXzXL87k9ihPTVwCUr8SuR6uriwaGNAW6soxvdqWlK7HbWc83s5ObkTpHswcfz03419RNevNxxe6PbfoZ6vK8dsfU44Txbs2DYrdF1lUxQktRWBRWj33Jbxe7MRpdpeaqvFMYl1EBuR7MgpOuxK5H1dXFFk7rKQC1YwbqvxK7JXgVtSgckPsZSr+oztGL3RhZTeWyaWAoCqtOFgDNg2I3s8WmGg+L5dyUDtMDze5hc4jwf//NYr8vW87RLz3gzvF382HpOT4T5sNxBiYDAAPgzsbx+fPjit03+/5FMe7cE9OR5l8NHA8w+HCcDe58dfMjPq/Y+7B/fAERxlMHjE9zb55LT2AGMf1kfivI58cVu2/2/fv6clSXPW8Xan9Q7Oa4rgdT7ce8RnflQAWpfgaxG8P0/ybEihUrVqxYsWLFiv327G/AeRc2LmN9mQAAAABJRU5ErkJggg=="
  },
  {
    "id": "6916d6cfb7cac390db7f1018",
    "username": "admin",
    "email": "admin@gmail.com",
    "full_name": "Admin Adminov",
    "role": "admin",
    "created_at": "2025-11-14T07:14:23.583000",
    "qr_code": null
  }
]


