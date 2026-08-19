from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date, timedelta, timezone
import hmac
import hashlib
import json
import math
import asyncio
import pandas as pd
import os
from typing import List

from app.database import get_db
from app.models import User, Classroom, Timetable, AttendanceLog
from app.schemas import ScheduleItem, VerifyAttendanceRequest, AttendanceResponse, ReportResponse
from app.config import settings
from app.auth import get_current_user, get_admin_user
from app.email_service import send_alert, send_report

router = APIRouter(prefix='/attendance', tags=['Attendance'])

@router.get('/today_schedule/{roll_no}', response_model=List[ScheduleItem])
async def get_today_schedule(roll_no: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.roll_no != roll_no and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot view schedule of another user")
    
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_end = datetime.combine(now.date(), datetime.max.time())
    
    # Query timetable for today joined with classrooms
    stmt = (
        select(Timetable, Classroom)
        .join(Classroom, Timetable.room_id == Classroom.room_id)
        .where(Timetable.start_time >= today_start, Timetable.start_time <= today_end)
        .order_by(Timetable.start_time)
    )
    result = await db.execute(stmt)
    schedules = result.all()
    
    schedule_items = []
    for tt, classroom in schedules:
        is_active = (tt.start_time <= now <= tt.end_time)
        schedule_items.append(ScheduleItem(
            timetable_id=tt.id,
            subject=tt.subject,
            room_name=classroom.room_name,
            esp32_uuid=classroom.esp32_uuid,
            start_time=tt.start_time,
            end_time=tt.end_time,
            teacher_email=tt.teacher_email,
            is_active=is_active
        ))
        
    return schedule_items

@router.post('/verify', response_model=AttendanceResponse)
async def verify_attendance(req: VerifyAttendanceRequest, db: AsyncSession = Depends(get_db)):
    # Fetch User
    user_stmt = select(User).where(User.roll_no == req.roll_no)
    user_res = await db.execute(user_stmt)
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    # Fetch Timetable and Classroom
    tt_stmt = (
        select(Timetable, Classroom)
        .join(Classroom, Timetable.room_id == Classroom.room_id)
        .where(Timetable.id == req.timetable_id)
    )
    tt_res = await db.execute(tt_stmt)
    tt_row = tt_res.first()
    if not tt_row:
        raise HTTPException(status_code=404, detail="Timetable entry not found")
    timetable, classroom = tt_row

    now = datetime.now()
    
    async def log_attendance(status_val: str, flag: str = None):
        log = AttendanceLog(
            roll_no=user.roll_no,
            timetable_id=timetable.id,
            timestamp=now,
            status=status_val,
            issue_flag=flag
        )
        db.add(log)
        await db.commit()
        return log

    # ----------------------------------------------------
    # LOCK 1: HMAC Signature Check (Crypto Tampering)
    # ----------------------------------------------------
    message = f"{req.roll_no}:{req.scanned_ble_uuid}:{req.app_timestamp}".encode('utf-8')
    computed_hmac = hmac.new(settings.SECRET_HMAC_KEY.encode('utf-8'), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hmac, req.hmac_signature):
        await log_attendance(status_val='rejected', flag='HMAC_TAMPERED')
        asyncio.create_task(
            send_alert(
                settings.ADMIN_EMAIL,
                "Intrusion Alert: HMAC Signature Mismatch",
                f"Student Roll No: {req.roll_no}\nProvided Signature: {req.hmac_signature}\nTimestamp: {req.app_timestamp}"
            )
        )
        raise HTTPException(status_code=403, detail="Security Lock 1 Failed: HMAC Signature Tampered")

    # ----------------------------------------------------
    # LOCK 2: Dynamic Room Check (ESP32 BLE UUID)
    # ----------------------------------------------------
    if req.scanned_ble_uuid.lower() != classroom.esp32_uuid.lower():
        await log_attendance(status_val='rejected', flag='Wrong Classroom/Proxy')
        asyncio.create_task(
            send_alert(
                settings.ADMIN_EMAIL,
                "Intrusion Alert: Wrong Classroom / Proxy Attempt",
                f"Student Roll No: {req.roll_no}\nExpected UUID: {classroom.esp32_uuid} ({classroom.room_name})\nScanned UUID: {req.scanned_ble_uuid}"
            )
        )
        raise HTTPException(status_code=403, detail="Security Lock 2 Failed: Wrong Classroom/Proxy detected")

    # ----------------------------------------------------
    # LOCK 3: Server Time Window Check (Start + 10 mins)
    # ----------------------------------------------------
    cutoff_time = timetable.start_time + timedelta(minutes=10)
    if now > cutoff_time:
        await log_attendance(status_val='rejected', flag='LATE_BEYOND_WINDOW')
        raise HTTPException(status_code=403, detail="Security Lock 3 Failed: Attendance window expired (past 10 min cutoff)")

    # ----------------------------------------------------
    # LOCK 4: Face Match Euclidean Distance (< 0.6)
    # ----------------------------------------------------
    if not user.face_encoding_json:
        raise HTTPException(status_code=400, detail="Security Lock 4 Failed: Student face encoding not registered in system")
    
    try:
        stored_face = json.loads(user.face_encoding_json)
    except Exception:
        raise HTTPException(status_code=500, detail="Stored face encoding is corrupted")
        
    live_face = req.live_face_encoding
    
    if len(stored_face) != len(live_face):
        raise HTTPException(status_code=400, detail=f"Face encoding dimension mismatch (expected {len(stored_face)}, got {len(live_face)})")
        
    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(stored_face, live_face)))
    if distance > 0.6:
        await log_attendance(status_val='rejected', flag='FACE_MISMATCH')
        raise HTTPException(status_code=403, detail=f"Security Lock 4 Failed: Face Euclidean distance {distance:.3f} > 0.6 threshold")

    # ----------------------------------------------------
    # ALL LOCKS PASSED - MARK ATTENDANCE
    # ----------------------------------------------------
    attendance_status = 'present'
    if now > timetable.start_time:
        attendance_status = 'late'
        
    await log_attendance(status_val=attendance_status)
    return AttendanceResponse(
        status=attendance_status,
        message=f"Attendance successfully marked as {attendance_status.upper()} for {timetable.subject}"
    )

@router.post('/trigger_reports', response_model=ReportResponse)
async def trigger_reports(db: AsyncSession = Depends(get_db), admin: User = Depends(get_admin_user)):
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    
    # Query completed classes today
    stmt = select(Timetable).where(Timetable.start_time >= today_start, Timetable.end_time <= now)
    result = await db.execute(stmt)
    completed_classes = result.scalars().all()
    
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    report_count = 0
    for tt in completed_classes:
        log_stmt = (
            select(AttendanceLog, User)
            .join(User, AttendanceLog.roll_no == User.roll_no)
            .where(AttendanceLog.timetable_id == tt.id)
            .order_by(AttendanceLog.timestamp)
        )
        log_res = await db.execute(log_stmt)
        logs = log_res.all()
        
        data = []
        for log, user in logs:
            data.append({
                "Roll No": user.roll_no,
                "Student Name": user.name,
                "Email": user.email,
                "Status": log.status,
                "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Issue Flag": log.issue_flag or "None"
            })
            
        df = pd.DataFrame(data)
        file_name = f"attendance_class_{tt.id}_{now.strftime('%Y%m%d')}.xlsx"
        file_path = os.path.join(reports_dir, file_name)
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        # Asynchronously send report to teacher
        asyncio.create_task(
            send_report(
                recipient=tt.teacher_email,
                file_path=file_path,
                subject=f"Daily Attendance Report - {tt.subject} ({now.strftime('%Y-%m-%d')})"
            )
        )
        report_count += 1
        
    return ReportResponse(
        message=f"Attendance reports generated and scheduled for email delivery for {report_count} class(es)",
        reports_generated=report_count
    )
