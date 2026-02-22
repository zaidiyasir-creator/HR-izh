from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import base64
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import math
import aiofiles
from webdav3.client import Client as WebDAVClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'vantage_hr_secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="VANTAGE HR API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== GEOLOCATION HELPERS ==============

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# ============== MODELS ==============

# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "employee"  # employee, manager, hr, admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    avatar: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Employee Models
class EmployeeCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: Optional[str] = None
    role: str = "employee"
    department: str
    position: str
    phone: Optional[str] = None
    address: Optional[str] = None
    salary: float = 0.0
    join_date: Optional[str] = None
    avatar: Optional[str] = None

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    salary: Optional[float] = None
    avatar: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None  # admin, hr, manager, employee
    geofence_category: Optional[str] = None  # office, campus, field, remote

# Leave Models
class LeaveRequest(BaseModel):
    leave_type: str  # annual, sick, personal, maternity, paternity
    start_date: str
    end_date: str
    reason: str

class LeaveUpdate(BaseModel):
    status: str  # pending, approved, rejected

# Attendance Models
class AttendanceCheckIn(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class AttendanceCheckOut(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

# Office Location Models
class OfficeLocationCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    default_radius: int = 500  # meters

class OfficeLocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    default_radius: Optional[int] = None
    is_active: Optional[bool] = None

# Geofence Category Models
class GeofenceCategoryCreate(BaseModel):
    name: str  # office, campus, field, remote
    display_name: str
    radius: int  # meters
    description: Optional[str] = None

class GeofenceCategoryUpdate(BaseModel):
    display_name: Optional[str] = None
    radius: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

# Menu Configuration Models
class MenuItemConfig(BaseModel):
    menu_key: str
    hidden_globally: bool = False
    hidden_for_roles: List[str] = []

class MenuConfigUpdate(BaseModel):
    menu_items: List[MenuItemConfig]

# Department Models
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    geofence_category: str = "office"

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    geofence_category: Optional[str] = None
    is_active: Optional[bool] = None

# Department Geofence Override
class DepartmentGeofenceUpdate(BaseModel):
    department: str
    geofence_category: str

# Claims Models
class ClaimCreate(BaseModel):
    claim_type: str  # travel, meal, medical, equipment, other
    amount: float
    description: str
    receipt_url: Optional[str] = None
    date: str

class ClaimUpdate(BaseModel):
    status: str  # pending, approved, rejected
    remarks: Optional[str] = None

# Overtime Models
class OvertimeCreate(BaseModel):
    date: str
    hours: float
    reason: str

class OvertimeUpdate(BaseModel):
    status: str  # pending, approved, rejected

# Announcement Models
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    priority: str = "normal"  # low, normal, high, urgent
    target_departments: Optional[List[str]] = None
    is_ai_generated: bool = False

class AnnouncementAIGenerate(BaseModel):
    topic: str
    tone: str = "professional"  # professional, friendly, urgent, celebratory
    target_audience: Optional[str] = None

# Performance Models
class PerformanceReviewCreate(BaseModel):
    employee_id: str
    period: str  # Q1 2024, Annual 2024
    goals_achieved: int
    goals_total: int
    strengths: List[str]
    improvements: List[str]
    rating: float  # 1-5
    comments: Optional[str] = None

class PerformanceInsightRequest(BaseModel):
    employee_id: str

# Payroll Models
class PayrollCreate(BaseModel):
    employee_id: str
    period: str  # January 2024
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    overtime_pay: float = 0.0
    bonus: float = 0.0

class AdvanceSalaryRequest(BaseModel):
    amount: float
    reason: str
    repayment_months: int = 1

# Settings Models
class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    theme: Optional[str] = None  # light, dark
    primary_color: Optional[str] = None
    leave_policies: Optional[Dict[str, int]] = None

# Remote Storage Models
class RemoteStorageConfig(BaseModel):
    storage_type: str  # 'nextcloud', 'nas', 'local'
    nextcloud_url: Optional[str] = None
    nextcloud_username: Optional[str] = None
    nextcloud_password: Optional[str] = None
    nextcloud_folder: Optional[str] = "/VantageHR"
    nas_path: Optional[str] = None  # Network path like /mnt/nas or //server/share
    enabled: bool = False

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def serialize_doc(doc):
    """Remove MongoDB _id and convert datetime objects"""
    if doc is None:
        return None
    if '_id' in doc:
        del doc['_id']
    return doc

# ============== REMOTE STORAGE HELPERS ==============

async def get_remote_storage_config():
    """Get remote storage configuration from database"""
    config = await db.settings.find_one({}, {"_id": 0, "remote_storage": 1})
    return config.get("remote_storage") if config else None

async def upload_to_nextcloud(file_content: bytes, filename: str, folder: str = "receipts") -> str:
    """Upload file to Nextcloud via WebDAV"""
    config = await get_remote_storage_config()
    if not config or config.get("storage_type") != "nextcloud":
        raise Exception("Nextcloud not configured")
    
    webdav_url = config["nextcloud_url"].rstrip("/") + "/remote.php/dav/files/" + config["nextcloud_username"]
    
    options = {
        'webdav_hostname': webdav_url,
        'webdav_login': config["nextcloud_username"],
        'webdav_password': config["nextcloud_password"],
        'disable_check': True
    }
    
    client = WebDAVClient(options)
    
    # Create folder structure if needed
    base_folder = config.get("nextcloud_folder", "/VantageHR").strip("/")
    target_folder = f"{base_folder}/{folder}"
    
    # Ensure folders exist
    try:
        if not client.check(base_folder):
            client.mkdir(base_folder)
        if not client.check(target_folder):
            client.mkdir(target_folder)
    except Exception:
        pass  # Folders might already exist
    
    # Upload file
    remote_path = f"{target_folder}/{filename}"
    
    # Write to temp file and upload
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
    
    try:
        client.upload_sync(remote_path=remote_path, local_path=tmp_path)
    finally:
        os.unlink(tmp_path)
    
    # Return the share URL or path
    return f"nextcloud://{target_folder}/{filename}"

async def upload_to_nas(file_content: bytes, filename: str, folder: str = "receipts") -> str:
    """Upload file to local NAS/filesystem"""
    config = await get_remote_storage_config()
    if not config or config.get("storage_type") != "nas":
        raise Exception("NAS not configured")
    
    nas_path = Path(config["nas_path"])
    target_folder = nas_path / folder
    
    # Ensure folder exists
    target_folder.mkdir(parents=True, exist_ok=True)
    
    # Write file
    file_path = target_folder / filename
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return f"nas://{folder}/{filename}"

async def upload_to_remote_storage(file_content: bytes, filename: str, folder: str = "receipts") -> Optional[str]:
    """Upload file to configured remote storage"""
    config = await get_remote_storage_config()
    
    if not config or not config.get("enabled"):
        return None  # Remote storage not enabled, use local MongoDB storage
    
    storage_type = config.get("storage_type")
    
    try:
        if storage_type == "nextcloud":
            return await upload_to_nextcloud(file_content, filename, folder)
        elif storage_type == "nas":
            return await upload_to_nas(file_content, filename, folder)
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to upload to remote storage: {e}")
        return None  # Fall back to local storage

async def get_file_from_nextcloud(remote_path: str) -> bytes:
    """Download file from Nextcloud"""
    config = await get_remote_storage_config()
    if not config or config.get("storage_type") != "nextcloud":
        raise Exception("Nextcloud not configured")
    
    webdav_url = config["nextcloud_url"].rstrip("/") + "/remote.php/dav/files/" + config["nextcloud_username"]
    
    options = {
        'webdav_hostname': webdav_url,
        'webdav_login': config["nextcloud_username"],
        'webdav_password': config["nextcloud_password"],
        'disable_check': True
    }
    
    client = WebDAVClient(options)
    
    # Parse the path from nextcloud://folder/filename format
    path = remote_path.replace("nextcloud://", "")
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        client.download_sync(remote_path=path, local_path=tmp_path)
        async with aiofiles.open(tmp_path, 'rb') as f:
            content = await f.read()
        return content
    finally:
        os.unlink(tmp_path)

async def get_file_from_nas(remote_path: str) -> bytes:
    """Read file from NAS"""
    config = await get_remote_storage_config()
    if not config or config.get("storage_type") != "nas":
        raise Exception("NAS not configured")
    
    # Parse the path from nas://folder/filename format
    path = remote_path.replace("nas://", "")
    nas_path = Path(config["nas_path"])
    file_path = nas_path / path
    
    async with aiofiles.open(file_path, 'rb') as f:
        return await f.read()

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "full_name": data.full_name,
        "role": data.role,
        "department": None,
        "avatar": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active"
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id, data.email, data.role)
    user_response = UserResponse(
        id=user_id,
        email=data.email,
        full_name=data.full_name,
        role=data.role,
        department=None,
        avatar=None,
        created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"])
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        department=user.get("department"),
        avatar=user.get("avatar"),
        created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        department=user.get("department"),
        avatar=user.get("avatar"),
        created_at=user["created_at"]
    )

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@api_router.post("/auth/change-password")
async def change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    # Get full user with password
    db_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(data.current_password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    # Update password
    new_hashed = hash_password(data.new_password)
    await db.users.update_one({"id": user["id"]}, {"$set": {"password": new_hashed}})
    
    return {"message": "Password changed successfully"}

class AdminResetPasswordRequest(BaseModel):
    employee_id: str
    new_password: str

@api_router.post("/auth/reset-password")
async def admin_reset_password(data: AdminResetPasswordRequest, user: dict = Depends(get_current_user)):
    # Only admin and HR can reset passwords
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if employee exists
    employee = await db.users.find_one({"id": data.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update password
    new_hashed = hash_password(data.new_password)
    await db.users.update_one({"id": data.employee_id}, {"$set": {"password": new_hashed}})
    
    return {"message": f"Password reset successfully for {employee['full_name']}"}

# ============== EMPLOYEE ROUTES ==============

@api_router.post("/employees")
async def create_employee(data: EmployeeCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    emp_id = str(uuid.uuid4())
    # Use provided password or default
    password = hash_password(data.password) if data.password else hash_password("Welcome123!")
    
    employee = {
        "id": emp_id,
        "email": data.email,
        "password": password,
        "full_name": data.full_name,
        "role": data.role,
        "department": data.department,
        "position": data.position,
        "phone": data.phone,
        "address": data.address,
        "salary": data.salary,
        "join_date": data.join_date or datetime.now(timezone.utc).date().isoformat(),
        "avatar": data.avatar,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "leave_balance": {"annual": 14, "sick": 14, "personal": 5}
    }
    await db.users.insert_one(employee)
    return serialize_doc({k: v for k, v in employee.items() if k != "password"})

@api_router.get("/employees")
async def get_employees(user: dict = Depends(get_current_user)):
    employees = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return employees

@api_router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, user: dict = Depends(get_current_user)):
    employee = await db.users.find_one({"id": employee_id}, {"_id": 0, "password": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@api_router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"] and user["id"] != employee_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.users.update_one({"id": employee_id}, {"$set": update_data})
    employee = await db.users.find_one({"id": employee_id}, {"_id": 0, "password": 0})
    return employee

@api_router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.users.delete_one({"id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

# ============== LEAVE ROUTES ==============

@api_router.post("/leaves")
async def create_leave(data: LeaveRequest, user: dict = Depends(get_current_user)):
    # Validate dates - end date must be >= start date
    start = datetime.fromisoformat(data.start_date)
    end = datetime.fromisoformat(data.end_date)
    if end < start:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")
    
    leave_id = str(uuid.uuid4())
    leave = {
        "id": leave_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "department": user.get("department", "N/A"),
        "leave_type": data.leave_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "reason": data.reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leaves.insert_one(leave)
    return serialize_doc(leave)

@api_router.get("/leaves")
async def get_leaves(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr", "manager"]:
        leaves = await db.leaves.find({}, {"_id": 0}).to_list(1000)
    else:
        leaves = await db.leaves.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return leaves

@api_router.put("/leaves/{leave_id}")
async def update_leave(leave_id: str, data: LeaveUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    leave = await db.leaves.find_one({"id": leave_id}, {"_id": 0})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    
    update = {
        "status": data.status,
        "approved_by": user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    await db.leaves.update_one({"id": leave_id}, {"$set": update})
    
    # Update leave balance if approved
    if data.status == "approved":
        start = datetime.fromisoformat(leave["start_date"])
        end = datetime.fromisoformat(leave["end_date"])
        days = (end - start).days + 1
        leave_type = leave["leave_type"]
        await db.users.update_one(
            {"id": leave["employee_id"]},
            {"$inc": {f"leave_balance.{leave_type}": -days}}
        )
    
    return {"message": f"Leave {data.status}"}

@api_router.get("/leaves/balance")
async def get_leave_balance(user: dict = Depends(get_current_user)):
    emp = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    return emp.get("leave_balance", {"annual": 14, "sick": 14, "personal": 5})

# ============== ATTENDANCE ROUTES ==============

async def get_employee_geofence_radius(user: dict) -> tuple:
    """Get the applicable geofence radius for an employee"""
    # Priority: Employee override > Department > Default category
    
    # 1. Check employee-specific geofence category
    emp_category = user.get("geofence_category")
    
    # 2. Check department override
    if not emp_category and user.get("department"):
        dept_override = await db.department_geofence.find_one(
            {"department": user.get("department")}, {"_id": 0}
        )
        if dept_override:
            emp_category = dept_override.get("geofence_category")
    
    # 3. Default to "office" category
    if not emp_category:
        emp_category = "office"
    
    # Get the category configuration
    category = await db.geofence_categories.find_one(
        {"name": emp_category, "is_active": {"$ne": False}}, {"_id": 0}
    )
    
    if category:
        return category.get("radius", 500), category.get("display_name", emp_category)
    
    # Default fallback
    return 500, "Office (Default)"

async def validate_geolocation(latitude: float, longitude: float, user: dict) -> dict:
    """Validate if user is within allowed geofence radius"""
    # Get active office locations
    offices = await db.office_locations.find(
        {"is_active": {"$ne": False}}, {"_id": 0}
    ).to_list(100)
    
    if not offices:
        # No offices configured, allow check-in
        return {"valid": True, "message": "No office locations configured", "distance": 0}
    
    # Get employee's allowed radius
    allowed_radius, category_name = await get_employee_geofence_radius(user)
    
    # Check if "remote" category (unlimited)
    if allowed_radius == -1 or allowed_radius > 50000:  # -1 or >50km = unlimited
        return {"valid": True, "message": f"Remote worker - no location restriction", "distance": 0}
    
    # Find nearest office
    nearest_office = None
    min_distance = float('inf')
    
    for office in offices:
        distance = haversine_distance(
            latitude, longitude,
            office["latitude"], office["longitude"]
        )
        if distance < min_distance:
            min_distance = distance
            nearest_office = office
    
    # Check if within radius
    if min_distance <= allowed_radius:
        return {
            "valid": True,
            "message": f"Within {category_name} range of {nearest_office['name']}",
            "distance": round(min_distance),
            "office": nearest_office["name"],
            "allowed_radius": allowed_radius
        }
    else:
        return {
            "valid": False,
            "message": f"Too far from office. You are {round(min_distance)}m away, but must be within {allowed_radius}m ({category_name})",
            "distance": round(min_distance),
            "office": nearest_office["name"],
            "allowed_radius": allowed_radius
        }

@api_router.post("/attendance/check-in")
async def check_in(data: AttendanceCheckIn, user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    existing = await db.attendance.find_one(
        {"employee_id": user["id"], "date": today},
        {"_id": 0}
    )
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Validate geolocation if provided
    geo_result = None
    if data.latitude is not None and data.longitude is not None:
        geo_result = await validate_geolocation(data.latitude, data.longitude, user)
        if not geo_result["valid"]:
            raise HTTPException(status_code=400, detail=geo_result["message"])
    
    attendance_id = str(uuid.uuid4())
    attendance = {
        "id": attendance_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "date": today,
        "check_in": datetime.now(timezone.utc).isoformat(),
        "check_in_latitude": data.latitude,
        "check_in_longitude": data.longitude,
        "check_in_distance": geo_result["distance"] if geo_result else None,
        "check_in_office": geo_result.get("office") if geo_result else None,
        "check_out": None,
        "location": data.location,
        "notes": data.notes,
        "status": "present",
        "total_hours": 0
    }
    await db.attendance.insert_one(attendance)
    
    result = serialize_doc(attendance)
    if geo_result:
        result["geo_message"] = geo_result["message"]
    return result

@api_router.post("/attendance/check-out")
async def check_out(data: AttendanceCheckOut, user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    attendance = await db.attendance.find_one(
        {"employee_id": user["id"], "date": today},
        {"_id": 0}
    )
    if not attendance:
        raise HTTPException(status_code=400, detail="No check-in found for today")
    if attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="Already checked out today")
    
    # Validate geolocation if provided
    geo_result = None
    if data.latitude is not None and data.longitude is not None:
        geo_result = await validate_geolocation(data.latitude, data.longitude, user)
        if not geo_result["valid"]:
            raise HTTPException(status_code=400, detail=geo_result["message"])
    
    check_out_time = datetime.now(timezone.utc)
    check_in_time = datetime.fromisoformat(attendance["check_in"])
    total_hours = (check_out_time - check_in_time).total_seconds() / 3600
    
    update = {
        "check_out": check_out_time.isoformat(),
        "check_out_latitude": data.latitude,
        "check_out_longitude": data.longitude,
        "check_out_distance": geo_result["distance"] if geo_result else None,
        "check_out_office": geo_result.get("office") if geo_result else None,
        "total_hours": round(total_hours, 2),
        "notes": data.notes or attendance.get("notes")
    }
    await db.attendance.update_one({"id": attendance["id"]}, {"$set": update})
    
    attendance.update(update)
    if geo_result:
        attendance["geo_message"] = geo_result["message"]
    return attendance

@api_router.get("/attendance")
async def get_attendance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    query = {}
    if user["role"] not in ["admin", "hr", "manager"]:
        query["employee_id"] = user["id"]
    
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    attendance = await db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return attendance

@api_router.get("/attendance/today")
async def get_today_attendance(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    attendance = await db.attendance.find_one(
        {"employee_id": user["id"], "date": today},
        {"_id": 0}
    )
    return attendance

# ============== CLAIMS ROUTES ==============

@api_router.post("/claims/upload-receipt")
async def upload_receipt(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload receipt for claims - accepts PNG, JPG, PDF. Max 5MB."""
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PNG, JPG, WebP, PDF")
    
    # Read file content
    content = await file.read()
    
    # Check file size (max 5MB)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB allowed")
    
    # Generate unique filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    unique_filename = f"receipt_{uuid.uuid4()}.{file_ext}"
    
    # Try to upload to remote storage first
    remote_url = await upload_to_remote_storage(content, unique_filename, "receipts")
    
    receipt_doc = {
        "id": str(uuid.uuid4()),
        "filename": unique_filename,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "uploaded_by": user["id"],
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    if remote_url:
        # Stored remotely - save reference only
        receipt_doc["remote_url"] = remote_url
        receipt_doc["storage_type"] = "remote"
    else:
        # Store locally in MongoDB as base64
        base64_content = base64.b64encode(content).decode('utf-8')
        receipt_doc["data"] = f"data:{file.content_type};base64,{base64_content}"
        receipt_doc["storage_type"] = "local"
    
    await db.receipts.insert_one(receipt_doc)
    
    return {
        "message": "Receipt uploaded successfully",
        "receipt_id": receipt_doc["id"],
        "filename": file.filename,
        "content_type": file.content_type,
        "storage_type": receipt_doc["storage_type"]
    }

@api_router.get("/claims/receipt/{receipt_id}")
async def get_receipt(receipt_id: str, user: dict = Depends(get_current_user)):
    """Get receipt data by ID"""
    receipt = await db.receipts.find_one({"id": receipt_id}, {"_id": 0})
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # If stored remotely, fetch the content
    if receipt.get("storage_type") == "remote" and receipt.get("remote_url"):
        try:
            remote_url = receipt["remote_url"]
            if remote_url.startswith("nextcloud://"):
                content = await get_file_from_nextcloud(remote_url)
            elif remote_url.startswith("nas://"):
                content = await get_file_from_nas(remote_url)
            else:
                raise HTTPException(status_code=500, detail="Unknown storage type")
            
            # Convert to base64 for response
            base64_content = base64.b64encode(content).decode('utf-8')
            receipt["data"] = f"data:{receipt['content_type']};base64,{base64_content}"
        except Exception as e:
            logger.error(f"Failed to fetch remote receipt: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch receipt from remote storage")
    
    return receipt

@api_router.post("/claims")
async def create_claim(data: ClaimCreate, user: dict = Depends(get_current_user)):
    claim_id = str(uuid.uuid4())
    claim = {
        "id": claim_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "claim_type": data.claim_type,
        "amount": data.amount,
        "description": data.description,
        "receipt_url": data.receipt_url,
        "date": data.date,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.claims.insert_one(claim)
    return serialize_doc(claim)

@api_router.get("/claims")
async def get_claims(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr", "manager"]:
        claims = await db.claims.find({}, {"_id": 0}).to_list(1000)
    else:
        claims = await db.claims.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return claims

@api_router.put("/claims/{claim_id}")
async def update_claim(claim_id: str, data: ClaimUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update = {
        "status": data.status,
        "remarks": data.remarks,
        "approved_by": user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    await db.claims.update_one({"id": claim_id}, {"$set": update})
    return {"message": f"Claim {data.status}"}

# ============== OVERTIME ROUTES ==============

@api_router.post("/overtime")
async def create_overtime(data: OvertimeCreate, user: dict = Depends(get_current_user)):
    ot_id = str(uuid.uuid4())
    overtime = {
        "id": ot_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "date": data.date,
        "hours": data.hours,
        "reason": data.reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.overtime.insert_one(overtime)
    return serialize_doc(overtime)

@api_router.get("/overtime")
async def get_overtime(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr", "manager"]:
        records = await db.overtime.find({}, {"_id": 0}).to_list(1000)
    else:
        records = await db.overtime.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return records

@api_router.put("/overtime/{overtime_id}")
async def update_overtime(overtime_id: str, data: OvertimeUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update = {
        "status": data.status,
        "approved_by": user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    await db.overtime.update_one({"id": overtime_id}, {"$set": update})
    return {"message": f"Overtime {data.status}"}

# ============== ANNOUNCEMENTS ROUTES ==============

@api_router.post("/announcements")
async def create_announcement(data: AnnouncementCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    ann_id = str(uuid.uuid4())
    announcement = {
        "id": ann_id,
        "title": data.title,
        "content": data.content,
        "priority": data.priority,
        "target_departments": data.target_departments,
        "author_id": user["id"],
        "author_name": user["full_name"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_ai_generated": data.is_ai_generated
    }
    await db.announcements.insert_one(announcement)
    return serialize_doc(announcement)

@api_router.post("/announcements/generate")
async def generate_announcement(data: AnnouncementAIGenerate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"announcement-{uuid.uuid4()}",
            system_message="You are an HR communications expert. Generate professional company announcements."
        ).with_model("gemini", "gemini-3-flash-preview")
        
        prompt = f"""Generate a company announcement about: {data.topic}
        
Tone: {data.tone}
Target audience: {data.target_audience or 'All employees'}

Please provide:
1. A catchy title (max 60 characters)
2. The announcement content (2-3 paragraphs, professional but engaging)

Format your response as JSON:
{{"title": "...", "content": "..."}}"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Parse the response
        import json
        try:
            # Try to extract JSON from the response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
            else:
                result = {"title": data.topic, "content": response}
        except:
            result = {"title": data.topic, "content": response}
        
        return {
            "title": result.get("title", data.topic),
            "content": result.get("content", response),
            "is_ai_generated": True
        }
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@api_router.get("/announcements")
async def get_announcements(user: dict = Depends(get_current_user)):
    announcements = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return announcements

# ============== PERFORMANCE ROUTES ==============

@api_router.post("/performance/reviews")
async def create_performance_review(data: PerformanceReviewCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = await db.users.find_one({"id": data.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    review_id = str(uuid.uuid4())
    review = {
        "id": review_id,
        "employee_id": data.employee_id,
        "employee_name": employee["full_name"],
        "reviewer_id": user["id"],
        "reviewer_name": user["full_name"],
        "period": data.period,
        "goals_achieved": data.goals_achieved,
        "goals_total": data.goals_total,
        "strengths": data.strengths,
        "improvements": data.improvements,
        "rating": data.rating,
        "comments": data.comments,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.performance_reviews.insert_one(review)
    return serialize_doc(review)

@api_router.get("/performance/reviews")
async def get_performance_reviews(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr", "manager"]:
        reviews = await db.performance_reviews.find({}, {"_id": 0}).to_list(1000)
    else:
        reviews = await db.performance_reviews.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return reviews

@api_router.post("/performance/insights")
async def generate_performance_insights(data: PerformanceInsightRequest, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = await db.users.find_one({"id": data.employee_id}, {"_id": 0, "password": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get performance reviews
    reviews = await db.performance_reviews.find({"employee_id": data.employee_id}, {"_id": 0}).to_list(10)
    
    # Get attendance data
    attendance = await db.attendance.find({"employee_id": data.employee_id}, {"_id": 0}).to_list(100)
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"insights-{uuid.uuid4()}",
            system_message="You are an HR analytics expert. Provide actionable insights based on employee data."
        ).with_model("openai", "gpt-5.2")
        
        prompt = f"""Analyze this employee's performance data and provide insights:

Employee: {employee.get('full_name')}
Position: {employee.get('position', 'N/A')}
Department: {employee.get('department', 'N/A')}

Performance Reviews: {len(reviews)} reviews
{reviews if reviews else 'No reviews yet'}

Attendance Records: {len(attendance)} records

Please provide:
1. Overall performance summary (2-3 sentences)
2. Key strengths (3 bullet points)
3. Areas for improvement (3 bullet points)
4. Recommended actions (3 bullet points)
5. Predicted trajectory (growth potential)

Format as JSON with keys: summary, strengths, improvements, actions, trajectory"""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        import json
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
            else:
                result = {"summary": response}
        except:
            result = {"summary": response}
        
        return {
            "employee_id": data.employee_id,
            "employee_name": employee.get("full_name"),
            "insights": result,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        raise HTTPException(status_code=500, detail=f"AI insights failed: {str(e)}")

# ============== PAYROLL ROUTES ==============

@api_router.post("/payroll")
async def create_payroll(data: PayrollCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employee = await db.users.find_one({"id": data.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    net_salary = data.basic_salary + data.allowances + data.overtime_pay + data.bonus - data.deductions
    
    payroll_id = str(uuid.uuid4())
    payroll = {
        "id": payroll_id,
        "employee_id": data.employee_id,
        "employee_name": employee["full_name"],
        "period": data.period,
        "basic_salary": data.basic_salary,
        "allowances": data.allowances,
        "deductions": data.deductions,
        "overtime_pay": data.overtime_pay,
        "bonus": data.bonus,
        "net_salary": net_salary,
        "status": "pending",
        "payment_status": "unpaid",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payroll.insert_one(payroll)
    return serialize_doc(payroll)

@api_router.get("/payroll")
async def get_payroll(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr"]:
        records = await db.payroll.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    else:
        records = await db.payroll.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return records

@api_router.post("/payroll/{payroll_id}/pay")
async def process_payment(payroll_id: str, request: Request, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payroll = await db.payroll.find_one({"id": payroll_id}, {"_id": 0})
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    if payroll["payment_status"] == "paid":
        raise HTTPException(status_code=400, detail="Already paid")
    
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
        
        api_key = os.environ.get('STRIPE_API_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="Payment service not configured")
        
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        
        # Get origin from request
        origin = request.headers.get('origin', host_url)
        success_url = f"{origin}/payroll?session_id={{CHECKOUT_SESSION_ID}}&status=success"
        cancel_url = f"{origin}/payroll?status=cancelled"
        
        checkout_request = CheckoutSessionRequest(
            amount=float(payroll["net_salary"]),
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "payroll_id": payroll_id,
                "employee_id": payroll["employee_id"],
                "period": payroll["period"]
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "payroll_id": payroll_id,
            "employee_id": payroll["employee_id"],
            "amount": payroll["net_salary"],
            "currency": "usd",
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        return {"checkout_url": session.url, "session_id": session.session_id}
    except Exception as e:
        logger.error(f"Payment error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")

@api_router.get("/payroll/payment-status/{session_id}")
async def get_payment_status(session_id: str, user: dict = Depends(get_current_user)):
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        api_key = os.environ.get('STRIPE_API_KEY')
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
        
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction and payroll if paid
        if status.payment_status == "paid":
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if transaction and transaction["payment_status"] != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                await db.payroll.update_one(
                    {"id": transaction["payroll_id"]},
                    {"$set": {"payment_status": "paid", "status": "completed", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,
            "currency": status.currency
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        api_key = os.environ.get('STRIPE_API_KEY')
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
        
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if transaction and transaction["payment_status"] != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                await db.payroll.update_one(
                    {"id": transaction["payroll_id"]},
                    {"$set": {"payment_status": "paid", "status": "completed"}}
                )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}

# ============== ADVANCE SALARY ROUTES ==============

@api_router.post("/advance-salary")
async def request_advance_salary(data: AdvanceSalaryRequest, user: dict = Depends(get_current_user)):
    request_id = str(uuid.uuid4())
    advance = {
        "id": request_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "amount": data.amount,
        "reason": data.reason,
        "repayment_months": data.repayment_months,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.advance_salary.insert_one(advance)
    return serialize_doc(advance)

@api_router.get("/advance-salary")
async def get_advance_salary(user: dict = Depends(get_current_user)):
    if user["role"] in ["admin", "hr"]:
        records = await db.advance_salary.find({}, {"_id": 0}).to_list(1000)
    else:
        records = await db.advance_salary.find({"employee_id": user["id"]}, {"_id": 0}).to_list(1000)
    return records

@api_router.put("/advance-salary/{request_id}")
async def update_advance_salary(request_id: str, status: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update = {
        "status": status,
        "approved_by": user["id"],
        "approved_at": datetime.now(timezone.utc).isoformat()
    }
    await db.advance_salary.update_one({"id": request_id}, {"$set": update})
    return {"message": f"Request {status}"}

# ============== CALENDAR/EVENTS ROUTES ==============

@api_router.post("/events")
async def create_event(
    title: str,
    description: str,
    start_date: str,
    end_date: str,
    event_type: str = "meeting",
    user: dict = Depends(get_current_user)
):
    event_id = str(uuid.uuid4())
    event = {
        "id": event_id,
        "title": title,
        "description": description,
        "start_date": start_date,
        "end_date": end_date,
        "event_type": event_type,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.events.insert_one(event)
    return serialize_doc(event)

@api_router.get("/events")
async def get_events(user: dict = Depends(get_current_user)):
    events = await db.events.find({}, {"_id": 0}).to_list(1000)
    
    # Also get approved leaves as calendar events
    leaves = await db.leaves.find({"status": "approved"}, {"_id": 0}).to_list(1000)
    leave_events = [
        {
            "id": f"leave-{l['id']}",
            "title": f"{l['employee_name']} - {l['leave_type'].title()} Leave",
            "description": l["reason"],
            "start_date": l["start_date"],
            "end_date": l["end_date"],
            "event_type": "leave",
            "created_by": l["employee_id"]
        }
        for l in leaves
    ]
    
    return events + leave_events

@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"message": "Event deleted"}

# ============== SETTINGS ROUTES ==============

@api_router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({}, {"_id": 0})
    if not settings:
        settings = {
            "company_name": "VANTAGE HR",
            "company_logo": None,
            "theme": "light",
            "primary_color": "#0F172A",
            "leave_policies": {"annual": 14, "sick": 14, "personal": 5}
        }
    return settings

@api_router.put("/settings")
async def update_settings(data: SettingsUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.settings.update_one({}, {"$set": update_data}, upsert=True)
    settings = await db.settings.find_one({}, {"_id": 0})
    return settings

@api_router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload company logo - admin only. Accepts PNG, JPG, SVG. Max 2MB."""
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/svg+xml", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PNG, JPG, SVG, WebP")
    
    # Read file content
    content = await file.read()
    
    # Check file size (max 2MB)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 2MB allowed")
    
    # Convert to base64 for storage
    base64_content = base64.b64encode(content).decode('utf-8')
    logo_data = f"data:{file.content_type};base64,{base64_content}"
    
    # Save to settings
    await db.settings.update_one(
        {},
        {"$set": {"company_logo": logo_data, "logo_filename": file.filename}},
        upsert=True
    )
    
    return {"message": "Logo uploaded successfully", "filename": file.filename}

@api_router.delete("/settings/logo")
async def delete_logo(user: dict = Depends(get_current_user)):
    """Delete company logo - admin only"""
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.settings.update_one(
        {},
        {"$set": {"company_logo": None, "logo_filename": None}}
    )
    
    return {"message": "Logo deleted"}

# Remote Storage Configuration
@api_router.get("/settings/remote-storage")
async def get_remote_storage_settings(user: dict = Depends(get_current_user)):
    """Get remote storage configuration - admin only"""
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    config = await get_remote_storage_config()
    if config:
        # Mask password for security
        if config.get("nextcloud_password"):
            config["nextcloud_password"] = "********"
    return config or {
        "storage_type": "local",
        "enabled": False,
        "nextcloud_url": "",
        "nextcloud_username": "",
        "nextcloud_password": "",
        "nextcloud_folder": "/VantageHR",
        "nas_path": ""
    }

@api_router.put("/settings/remote-storage")
async def update_remote_storage_settings(data: RemoteStorageConfig, user: dict = Depends(get_current_user)):
    """Update remote storage configuration - admin only"""
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get existing config to preserve password if not changed
    existing = await get_remote_storage_config()
    
    update_data = data.model_dump()
    
    # If password is masked, keep the existing one
    if update_data.get("nextcloud_password") == "********" and existing:
        update_data["nextcloud_password"] = existing.get("nextcloud_password")
    
    await db.settings.update_one(
        {},
        {"$set": {"remote_storage": update_data}},
        upsert=True
    )
    
    # Return config with masked password
    result = update_data.copy()
    if result.get("nextcloud_password"):
        result["nextcloud_password"] = "********"
    
    return {"message": "Remote storage settings updated", "config": result}

@api_router.post("/settings/remote-storage/test")
async def test_remote_storage_connection(user: dict = Depends(get_current_user)):
    """Test remote storage connection - admin only"""
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    config = await get_remote_storage_config()
    
    if not config or not config.get("enabled"):
        return {"success": False, "message": "Remote storage not enabled"}
    
    storage_type = config.get("storage_type")
    
    try:
        if storage_type == "nextcloud":
            # Test Nextcloud connection
            webdav_url = config["nextcloud_url"].rstrip("/") + "/remote.php/dav/files/" + config["nextcloud_username"]
            
            options = {
                'webdav_hostname': webdav_url,
                'webdav_login': config["nextcloud_username"],
                'webdav_password': config["nextcloud_password"],
                'disable_check': True
            }
            
            client = WebDAVClient(options)
            # Try to list root directory
            client.list("/")
            
            return {"success": True, "message": "Nextcloud connection successful"}
            
        elif storage_type == "nas":
            # Test NAS path exists and is writable
            nas_path = Path(config["nas_path"])
            if not nas_path.exists():
                return {"success": False, "message": f"NAS path does not exist: {config['nas_path']}"}
            
            # Test write permission
            test_file = nas_path / ".vantage_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                return {"success": True, "message": "NAS connection successful"}
            except Exception as e:
                return {"success": False, "message": f"NAS not writable: {str(e)}"}
        else:
            return {"success": False, "message": f"Unknown storage type: {storage_type}"}
            
    except Exception as e:
        return {"success": False, "message": str(e)}

# ============== GEOFENCE MANAGEMENT ROUTES ==============

# Office Locations
@api_router.get("/office-locations")
async def get_office_locations(user: dict = Depends(get_current_user)):
    locations = await db.office_locations.find({}, {"_id": 0}).to_list(100)
    return locations

@api_router.post("/office-locations")
async def create_office_location(data: OfficeLocationCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    location_id = str(uuid.uuid4())
    location = {
        "id": location_id,
        "name": data.name,
        "address": data.address,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "default_radius": data.default_radius,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.office_locations.insert_one(location)
    return serialize_doc(location)

@api_router.put("/office-locations/{location_id}")
async def update_office_location(location_id: str, data: OfficeLocationUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.office_locations.update_one({"id": location_id}, {"$set": update_data})
    location = await db.office_locations.find_one({"id": location_id}, {"_id": 0})
    return location

@api_router.delete("/office-locations/{location_id}")
async def delete_office_location(location_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.office_locations.delete_one({"id": location_id})
    return {"message": "Office location deleted"}

# Geofence Categories
@api_router.get("/geofence-categories")
async def get_geofence_categories(user: dict = Depends(get_current_user)):
    categories = await db.geofence_categories.find({}, {"_id": 0}).to_list(100)
    
    # Return defaults if none exist
    if not categories:
        defaults = [
            {"name": "office", "display_name": "Office Staff", "radius": 500, "description": "Standard office workers", "is_active": True},
            {"name": "campus", "display_name": "Campus/Complex", "radius": 1000, "description": "Large campus or multiple buildings", "is_active": True},
            {"name": "field", "display_name": "Field Workers", "radius": 5000, "description": "Sales, service, or site workers", "is_active": True},
            {"name": "remote", "display_name": "Remote Workers", "radius": -1, "description": "No location restriction", "is_active": True}
        ]
        return defaults
    
    return categories

@api_router.post("/geofence-categories")
async def create_geofence_category(data: GeofenceCategoryCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    existing = await db.geofence_categories.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = {
        "name": data.name,
        "display_name": data.display_name,
        "radius": data.radius,
        "description": data.description,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.geofence_categories.insert_one(category)
    return serialize_doc(category)

@api_router.put("/geofence-categories/{category_name}")
async def update_geofence_category(category_name: str, data: GeofenceCategoryUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.geofence_categories.update_one({"name": category_name}, {"$set": update_data}, upsert=True)
    category = await db.geofence_categories.find_one({"name": category_name}, {"_id": 0})
    return category

# Department Geofence Assignment
@api_router.get("/department-geofence")
async def get_department_geofence(user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    assignments = await db.department_geofence.find({}, {"_id": 0}).to_list(100)
    return assignments

@api_router.post("/department-geofence")
async def set_department_geofence(data: DepartmentGeofenceUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.department_geofence.update_one(
        {"department": data.department},
        {"$set": {"department": data.department, "geofence_category": data.geofence_category}},
        upsert=True
    )
    return {"message": f"Department {data.department} assigned to {data.geofence_category} category"}

@api_router.delete("/department-geofence/{department}")
async def delete_department_geofence(department: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.department_geofence.delete_one({"department": department})
    return {"message": f"Geofence assignment removed for {department}"}

# ============== DEPARTMENTS CRUD ==============

@api_router.get("/departments")
async def get_departments(user: dict = Depends(get_current_user)):
    departments = await db.departments.find({}, {"_id": 0}).to_list(100)
    return departments

@api_router.post("/departments")
async def create_department(data: DepartmentCreate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if department already exists
    existing = await db.departments.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Department already exists")
    
    department = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "description": data.description,
        "geofence_category": data.geofence_category,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.departments.insert_one(department)
    
    # Also create department-geofence assignment
    await db.department_geofence.update_one(
        {"department": data.name},
        {"$set": {"department": data.name, "geofence_category": data.geofence_category}},
        upsert=True
    )
    
    return {k: v for k, v in department.items() if k != "_id"}

@api_router.put("/departments/{dept_id}")
async def update_department(dept_id: str, data: DepartmentUpdate, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get existing department
    existing = await db.departments.find_one({"id": dept_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")
    
    old_name = existing.get("name")
    update_data = {}
    
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.geofence_category is not None:
        update_data["geofence_category"] = data.geofence_category
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    if update_data:
        await db.departments.update_one({"id": dept_id}, {"$set": update_data})
        
        # Update department-geofence assignment if geofence category changed
        new_name = update_data.get("name", old_name)
        new_category = update_data.get("geofence_category", existing.get("geofence_category"))
        
        # If name changed, update all employees and geofence assignment
        if data.name is not None and data.name != old_name:
            await db.users.update_many(
                {"department": old_name},
                {"$set": {"department": data.name}}
            )
            await db.department_geofence.delete_one({"department": old_name})
        
        await db.department_geofence.update_one(
            {"department": new_name},
            {"$set": {"department": new_name, "geofence_category": new_category}},
            upsert=True
        )
    
    updated = await db.departments.find_one({"id": dept_id}, {"_id": 0})
    return updated

@api_router.delete("/departments/{dept_id}")
async def delete_department(dept_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get department name before deletion
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if any employees are in this department
    employee_count = await db.users.count_documents({"department": dept["name"]})
    if employee_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete department with {employee_count} employee(s). Reassign employees first."
        )
    
    await db.departments.delete_one({"id": dept_id})
    await db.department_geofence.delete_one({"department": dept["name"]})
    
    return {"message": f"Department '{dept['name']}' deleted"}

# ============== MENU CONFIGURATION ==============

# Default menu items configuration
DEFAULT_MENU_ITEMS = [
    {"menu_key": "dashboard", "name": "Dashboard", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "employees", "name": "Employees", "hidden_globally": False, "hidden_for_roles": ["employee"]},
    {"menu_key": "leaves", "name": "Leaves", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "attendance", "name": "Attendance", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "announcements", "name": "Announcements", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "calendar", "name": "Calendar", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "claims", "name": "Claims", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "overtime", "name": "Overtime", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "payroll", "name": "Payroll", "hidden_globally": False, "hidden_for_roles": ["employee", "manager"]},
    {"menu_key": "performance", "name": "Performance", "hidden_globally": False, "hidden_for_roles": ["employee"]},
    {"menu_key": "geofence", "name": "Geofence", "hidden_globally": False, "hidden_for_roles": ["employee", "manager"]},
    {"menu_key": "settings", "name": "Settings", "hidden_globally": False, "hidden_for_roles": []},
    {"menu_key": "menu-config", "name": "Menu Config", "hidden_globally": False, "hidden_for_roles": ["employee", "manager", "hr"]},
]

@api_router.get("/menu-config")
async def get_menu_config(user: dict = Depends(get_current_user)):
    """Get menu configuration - returns visibility settings for all menu items"""
    config = await db.menu_config.find_one({"config_id": "main"}, {"_id": 0})
    
    if not config:
        # Return default configuration
        return {"menu_items": DEFAULT_MENU_ITEMS}
    
    return {"menu_items": config.get("menu_items", DEFAULT_MENU_ITEMS)}

@api_router.put("/menu-config")
async def update_menu_config(data: MenuConfigUpdate, user: dict = Depends(get_current_user)):
    """Update menu configuration - admin only"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can configure menu visibility")
    
    # Merge with default to ensure all menu items exist
    menu_items_dict = {item.menu_key: item.dict() for item in data.menu_items}
    
    merged_items = []
    for default_item in DEFAULT_MENU_ITEMS:
        if default_item["menu_key"] in menu_items_dict:
            merged = {**default_item, **menu_items_dict[default_item["menu_key"]]}
            merged_items.append(merged)
        else:
            merged_items.append(default_item)
    
    await db.menu_config.update_one(
        {"config_id": "main"},
        {"$set": {"config_id": "main", "menu_items": merged_items, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"message": "Menu configuration updated", "menu_items": merged_items}

@api_router.post("/menu-config/reset")
async def reset_menu_config(user: dict = Depends(get_current_user)):
    """Reset menu configuration to defaults - admin only"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can reset menu configuration")
    
    await db.menu_config.delete_one({"config_id": "main"})
    return {"message": "Menu configuration reset to defaults", "menu_items": DEFAULT_MENU_ITEMS}

# ============== DASHBOARD STATS ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    user_role = user.get("role", "employee")
    user_id = user.get("id")
    user_department = user.get("department")
    
    # Role-based stats
    if user_role in ["admin", "hr"]:
        # Admin/HR see all stats
        total_employees = await db.users.count_documents({})
        present_today = await db.attendance.count_documents({"date": today, "check_in": {"$ne": None}})
        pending_leaves = await db.leaves.count_documents({"status": "pending"})
        pending_claims = await db.claims.count_documents({"status": "pending"})
        pending_overtime = await db.overtime.count_documents({"status": "pending"})
        recent_leaves = await db.leaves.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(5)
        recent_claims = await db.claims.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(5)
        
    elif user_role == "manager":
        # Manager sees their department's stats only
        dept_employees = await db.users.find({"department": user_department}, {"id": 1}).to_list(100)
        dept_employee_ids = [e["id"] for e in dept_employees]
        
        total_employees = len(dept_employee_ids)
        present_today = await db.attendance.count_documents({
            "date": today, 
            "check_in": {"$ne": None},
            "user_id": {"$in": dept_employee_ids}
        })
        pending_leaves = await db.leaves.count_documents({
            "status": "pending",
            "employee_id": {"$in": dept_employee_ids}
        })
        pending_claims = await db.claims.count_documents({
            "status": "pending",
            "employee_id": {"$in": dept_employee_ids}
        })
        pending_overtime = await db.overtime.count_documents({
            "status": "pending",
            "employee_id": {"$in": dept_employee_ids}
        })
        recent_leaves = await db.leaves.find({
            "status": "pending",
            "employee_id": {"$in": dept_employee_ids}
        }, {"_id": 0}).sort("created_at", -1).to_list(5)
        recent_claims = await db.claims.find({
            "status": "pending",
            "employee_id": {"$in": dept_employee_ids}
        }, {"_id": 0}).sort("created_at", -1).to_list(5)
        
    else:
        # Employee sees only their own stats - NO total employees, NO present today
        total_employees = None  # Hidden from employees
        present_today = None    # Hidden from employees
        pending_leaves = await db.leaves.count_documents({
            "status": "pending",
            "employee_id": user_id
        })
        pending_claims = await db.claims.count_documents({
            "status": "pending",
            "employee_id": user_id
        })
        pending_overtime = await db.overtime.count_documents({
            "status": "pending",
            "employee_id": user_id
        })
        recent_leaves = await db.leaves.find({
            "status": "pending",
            "employee_id": user_id
        }, {"_id": 0}).sort("created_at", -1).to_list(5)
        recent_claims = await db.claims.find({
            "status": "pending",
            "employee_id": user_id
        }, {"_id": 0}).sort("created_at", -1).to_list(5)
    
    # Announcements visible to all
    recent_announcements = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(3)
    
    return {
        "total_employees": total_employees,
        "present_today": present_today,
        "pending_leaves": pending_leaves,
        "pending_claims": pending_claims,
        "pending_overtime": pending_overtime,
        "recent_leaves": recent_leaves,
        "recent_claims": recent_claims,
        "recent_announcements": recent_announcements,
        "user_role": user_role,
        "user_department": user_department
    }

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "VANTAGE HR API", "version": "1.0.0"}

# Include the router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
