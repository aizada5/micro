from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import jwt
import qrcode
import io
import base64
import os
from bson import ObjectId

# Environment variables
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "assignmentdb")
JWT_SECRET = os.getenv("JWT_SECRET", "aizada100ballmozhnopozhalusta")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Initialize FastAPI
app = FastAPI(
    title="User/Auth/QR Microservice",
    description="User management, authentication, and QR code generation service",
    version="1.0.0"
)

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["users"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Pydantic Models
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: str = Field(default="student", pattern="^(student|teacher|admin)$")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime
    qr_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class QRCodeResponse(BaseModel):
    user_id: str
    qr_code_base64: str
    data: str

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Health Check Endpoint
@app.get("/health/db")
async def health_check():
    """Check database connectivity"""
    try:
        await db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "service": "User/Auth/QR Microservice"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "User/Auth/QR Microservice API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Authentication Endpoints
@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await users_collection.find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "role": user.role,
        "created_at": datetime.utcnow(),
        "qr_code": None
    }
    
    result = await users_collection.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    user_dict.pop("password")
    user_dict.pop("_id", None)
    
    return user_dict

@app.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Login and get access token"""
    user = await users_collection.find_one({"email": user_login.email})
    
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user["_id"]), "role": user["role"]})
    
    return {"access_token": access_token, "token_type": "bearer"}

# User Management Endpoints
@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name"),
        "role": current_user["role"],
        "created_at": current_user["created_at"],
        "qr_code": current_user.get("qr_code")
    }

@app.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Get all users (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    
    users = []
    async for user in users_collection.find():
        users.append({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "role": user["role"],
            "created_at": user["created_at"],
            "qr_code": user.get("qr_code")
        })
    
    return users

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user by ID"""
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only view their own info unless they're admin
    if str(user["_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "role": user["role"],
        "created_at": user["created_at"],
        "qr_code": user.get("qr_code")
    }

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete user (admin only or own account)"""
    if current_user["role"] != "admin" and str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    try:
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully", "user_id": user_id}

# QR Code Endpoints
@app.post("/qr/generate", response_model=QRCodeResponse)
async def generate_user_qr(current_user: dict = Depends(get_current_user)):
    """Generate QR code for current user"""
    user_id = str(current_user["_id"])
    
    # Create QR code data (you can customize this)
    qr_data = f"USER:{user_id}|EMAIL:{current_user['email']}|ROLE:{current_user['role']}"
    
    # Generate QR code
    qr_code_base64 = generate_qr_code(qr_data)
    
    # Update user with QR code
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"qr_code": qr_code_base64}}
    )
    
    return {
        "user_id": user_id,
        "qr_code_base64": qr_code_base64,
        "data": qr_data
    }

@app.get("/qr/{user_id}", response_model=QRCodeResponse)
async def get_user_qr(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get QR code for a specific user"""
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Users can only view their own QR unless they're admin
    if str(user["_id"]) != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this QR code")
    
    if not user.get("qr_code"):
        raise HTTPException(status_code=404, detail="QR code not generated for this user")
    
    qr_data = f"USER:{user_id}|EMAIL:{user['email']}|ROLE:{user['role']}"
    
    return {
        "user_id": user_id,
        "qr_code_base64": user["qr_code"],
        "data": qr_data
    }

# Startup event
@app.on_event("startup")
async def startup_db_client():
    """Create database indexes on startup"""
    try:
        # Create unique indexes
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("username", unique=True)
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connection on shutdown"""
    client.close()
    print("🔌 Database connection closed")