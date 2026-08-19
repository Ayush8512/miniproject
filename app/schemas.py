from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    roll_no: str
    password: str
    device_id: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    roll_no: str
    name: str
    email: str
    role: str
    device_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class OTPResponse(BaseModel):
    message: str
    otp: str

class ScheduleItem(BaseModel):
    timetable_id: int
    subject: str
    room_name: str
    esp32_uuid: str
    start_time: datetime
    end_time: datetime
    teacher_email: str
    is_active: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class VerifyAttendanceRequest(BaseModel):
    roll_no: str
    timetable_id: int
    live_face_encoding: List[float]
    scanned_ble_uuid: str
    app_timestamp: str
    hmac_signature: str

class AttendanceResponse(BaseModel):
    status: str
    message: str
    issue_flag: Optional[str] = None

class ClassroomCreate(BaseModel):
    room_id: str
    room_name: str
    esp32_uuid: str

class ClassroomResponse(BaseModel):
    room_id: str
    room_name: str
    esp32_uuid: str
    
    model_config = ConfigDict(from_attributes=True)

class TimetableCreate(BaseModel):
    room_id: str
    subject: str
    start_time: datetime
    end_time: datetime
    teacher_email: str

class TimetableResponse(BaseModel):
    id: int
    room_id: str
    subject: str
    start_time: datetime
    end_time: datetime
    teacher_email: str
    
    model_config = ConfigDict(from_attributes=True)

class AttendanceLogResponse(BaseModel):
    id: int
    roll_no: str
    timetable_id: int
    timestamp: datetime
    status: str
    issue_flag: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class StudentUpload(BaseModel):
    roll_no: str
    name: str
    email: EmailStr
    password: str

class FaceRegistration(BaseModel):
    face_encoding: List[float]

class ReportResponse(BaseModel):
    message: str
    reports_generated: int

class DashboardStats(BaseModel):
    total_students: int
    total_classrooms: int
    today_attendance_percent: float
    active_alerts: int
