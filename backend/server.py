from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt

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
    location: Optional[str] = None
    notes: Optional[str] = None

class AttendanceCheckOut(BaseModel):
    notes: Optional[str] = None

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

@api_router.post("/attendance/check-in")
async def check_in(data: AttendanceCheckIn, user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    existing = await db.attendance.find_one(
        {"employee_id": user["id"], "date": today},
        {"_id": 0}
    )
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    attendance_id = str(uuid.uuid4())
    attendance = {
        "id": attendance_id,
        "employee_id": user["id"],
        "employee_name": user["full_name"],
        "date": today,
        "check_in": datetime.now(timezone.utc).isoformat(),
        "check_out": None,
        "location": data.location,
        "notes": data.notes,
        "status": "present",
        "total_hours": 0
    }
    await db.attendance.insert_one(attendance)
    return serialize_doc(attendance)

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
    
    check_out_time = datetime.now(timezone.utc)
    check_in_time = datetime.fromisoformat(attendance["check_in"])
    total_hours = (check_out_time - check_in_time).total_seconds() / 3600
    
    update = {
        "check_out": check_out_time.isoformat(),
        "total_hours": round(total_hours, 2),
        "notes": data.notes or attendance.get("notes")
    }
    await db.attendance.update_one({"id": attendance["id"]}, {"$set": update})
    
    attendance.update(update)
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
        "is_ai_generated": False
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
        ).with_model("openai", "gpt-5.2")
        
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

# ============== DASHBOARD STATS ==============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    today = datetime.now(timezone.utc).date().isoformat()
    
    total_employees = await db.users.count_documents({})
    present_today = await db.attendance.count_documents({"date": today, "check_in": {"$ne": None}})
    pending_leaves = await db.leaves.count_documents({"status": "pending"})
    pending_claims = await db.claims.count_documents({"status": "pending"})
    pending_overtime = await db.overtime.count_documents({"status": "pending"})
    
    # Recent activities
    recent_leaves = await db.leaves.find({}, {"_id": 0}).sort("created_at", -1).to_list(5)
    recent_announcements = await db.announcements.find({}, {"_id": 0}).sort("created_at", -1).to_list(3)
    
    return {
        "total_employees": total_employees,
        "present_today": present_today,
        "pending_leaves": pending_leaves,
        "pending_claims": pending_claims,
        "pending_overtime": pending_overtime,
        "recent_leaves": recent_leaves,
        "recent_announcements": recent_announcements
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
