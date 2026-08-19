from fastapi import FastAPI, Depends, HTTPException, Body, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from datetime import datetime, date
import uvicorn
import json
import os

from app.database import create_tables, get_db
from app.models import User, Classroom, Timetable, AttendanceLog
from app.schemas import (
    ClassroomCreate, ClassroomResponse,
    TimetableCreate, TimetableResponse,
    StudentUpload, UserResponse,
    FaceRegistration, AttendanceLogResponse,
    DashboardStats
)
from app.auth import router as auth_router, get_admin_user, hash_password
from app.attendance import router as attendance_router

app = FastAPI(
    title='Smart Attendance SaaS API',
    description='Enterprise-Scale Smart Attendance SaaS Backend with Multi-Node Edge AI, BLE dynamic classrooms, and 4-Lock verification engine.',
    version='1.0.0'
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sub-routers
app.include_router(auth_router)
app.include_router(attendance_router)

@app.on_event('startup')
async def startup():
    os.makedirs("reports", exist_ok=True)
    await create_tables()

@app.get("/", tags=['General'])
async def root():
    return {
        "message": "Enterprise Smart Attendance SaaS API is Online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/admin/dashboard_stats", response_model=DashboardStats, tags=['Admin'])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    # 1. Total students
    res_students = await db.execute(select(func.count()).select_from(User).where(User.role == 'student'))
    total_students = res_students.scalar() or 0

    # 2. Total classrooms
    res_classrooms = await db.execute(select(func.count()).select_from(Classroom))
    total_classrooms = res_classrooms.scalar() or 0

    # 3. Today's attendance logs
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    
    res_today_logs = await db.execute(
        select(AttendanceLog).where(AttendanceLog.timestamp >= today_start)
    )
    today_logs = res_today_logs.scalars().all()
    
    total_today = len(today_logs)
    present_today = len([l for l in today_logs if l.status in ['present', 'late']])
    active_alerts = len([l for l in today_logs if l.issue_flag is not None])
    
    att_percent = round((present_today / total_today * 100), 1) if total_today > 0 else 0.0

    return DashboardStats(
        total_students=total_students,
        total_classrooms=total_classrooms,
        today_attendance_percent=att_percent,
        active_alerts=active_alerts
    )

@app.post("/admin/classrooms", response_model=ClassroomResponse, tags=['Admin'])
async def create_classroom(classroom: ClassroomCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    # Check if classroom with room_id or esp32_uuid exists
    stmt = select(Classroom).where((Classroom.room_id == classroom.room_id) | (Classroom.esp32_uuid == classroom.esp32_uuid))
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Classroom with this Room ID or ESP32 UUID already exists")

    new_classroom = Classroom(
        room_id=classroom.room_id,
        room_name=classroom.room_name,
        esp32_uuid=classroom.esp32_uuid
    )
    db.add(new_classroom)
    await db.commit()
    await db.refresh(new_classroom)
    return new_classroom

@app.get("/admin/classrooms", response_model=List[ClassroomResponse], tags=['Admin'])
async def list_classrooms(db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    stmt = select(Classroom).order_by(Classroom.room_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@app.delete("/admin/classrooms/{room_id}", tags=['Admin'])
async def delete_classroom(room_id: str, db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    stmt = select(Classroom).where(Classroom.room_id == room_id)
    res = await db.execute(stmt)
    cr = res.scalar_one_or_none()
    if not cr:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    await db.delete(cr)
    await db.commit()
    return {"message": f"Classroom {room_id} deleted successfully"}

@app.post("/admin/timetable", response_model=TimetableResponse, tags=['Admin'])
async def create_timetable(tt: TimetableCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    # Verify classroom exists
    cr_res = await db.execute(select(Classroom).where(Classroom.room_id == tt.room_id))
    if not cr_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Classroom '{tt.room_id}' not found")
        
    new_tt = Timetable(
        room_id=tt.room_id,
        subject=tt.subject,
        start_time=tt.start_time,
        end_time=tt.end_time,
        teacher_email=tt.teacher_email
    )
    db.add(new_tt)
    await db.commit()
    await db.refresh(new_tt)
    return new_tt

@app.get("/admin/timetable", response_model=List[TimetableResponse], tags=['Admin'])
async def list_timetable(db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    stmt = select(Timetable).order_by(Timetable.start_time)
    result = await db.execute(stmt)
    return result.scalars().all()

@app.post("/admin/bulk_upload_students", tags=['Admin'])
async def bulk_upload_students(students: List[StudentUpload], db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    created_count = 0
    for s in students:
        # Check if user with roll_no or email exists
        res = await db.execute(select(User).where((User.roll_no == s.roll_no) | (User.email == s.email)))
        if res.scalar_one_or_none():
            continue
            
        hashed_pwd = hash_password(s.password)
        user = User(
            roll_no=s.roll_no,
            name=s.name,
            email=s.email,
            hashed_password=hashed_pwd,
            role='student',
            device_id=None,
            face_encoding_json=None
        )
        db.add(user)
        created_count += 1
        
    await db.commit()
    return {"message": f"Successfully processed. Created {created_count} new student(s).", "created_count": created_count}

@app.get("/admin/students", response_model=List[UserResponse], tags=['Admin'])
async def list_students(db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    stmt = select(User).order_by(User.roll_no)
    result = await db.execute(stmt)
    return result.scalars().all()

@app.post("/admin/register_face/{roll_no}", tags=['Admin'])
async def register_face(roll_no: str, face_data: FaceRegistration, db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    if len(face_data.face_encoding) != 128:
        raise HTTPException(status_code=400, detail="Face encoding must contain exactly 128 float values")
        
    res = await db.execute(select(User).where(User.roll_no == roll_no))
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
        
    user.face_encoding_json = json.dumps(face_data.face_encoding)
    await db.commit()
    return {"message": f"128-point face encoding successfully registered for {user.name} ({roll_no})"}

@app.get("/admin/attendance_logs", tags=['Admin'])
async def list_attendance_logs(limit: int = 50, db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    stmt = (
        select(AttendanceLog, User, Timetable)
        .join(User, AttendanceLog.roll_no == User.roll_no)
        .join(Timetable, AttendanceLog.timetable_id == Timetable.id)
        .order_by(AttendanceLog.timestamp.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    logs = []
    for log, user, tt in rows:
        logs.append({
            "id": log.id,
            "roll_no": user.roll_no,
            "student_name": user.name,
            "subject": tt.subject,
            "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "status": log.status,
            "issue_flag": log.issue_flag
        })
    return logs

if __name__ == '__main__':
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)
