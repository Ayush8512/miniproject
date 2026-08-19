import asyncio
import json
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, create_tables
from app.models import User, Classroom, Timetable, AttendanceLog
from app.auth import hash_password
from sqlalchemy import select

async def seed():
    print("Creating tables if they don't exist...")
    await create_tables()

    async with AsyncSessionLocal() as session:
        # 1. Admin User
        admin_res = await session.execute(select(User).where(User.roll_no == 'admin'))
        if not admin_res.scalar_one_or_none():
            admin = User(
                roll_no='admin',
                name='System Administrator',
                email='admin@college.edu',
                hashed_password=hash_password('admin123'),
                role='admin',
                device_id=None,
                face_encoding_json=None
            )
            session.add(admin)
            print("[+] Created Admin: admin / admin123")

        # 2. Demo Students
        dummy_face = json.dumps([0.1] * 128)
        students = [
            ('2026CS101', 'Aarav Sharma', 'aarav@college.edu', 'pass123', 'MAC-AARAV-01', dummy_face),
            ('2026CS102', 'Bhavya Patel', 'bhavya@college.edu', 'pass123', None, dummy_face),
            ('2026CS103', 'Chirag Rao', 'chirag@college.edu', 'pass123', None, dummy_face)
        ]
        for roll, name, email, pwd, dev_id, face in students:
            st_res = await session.execute(select(User).where(User.roll_no == roll))
            if not st_res.scalar_one_or_none():
                st = User(
                    roll_no=roll,
                    name=name,
                    email=email,
                    hashed_password=hash_password(pwd),
                    role='student',
                    device_id=dev_id,
                    face_encoding_json=face
                )
                session.add(st)
                print(f"[+] Created Student: {roll} ({name})")

        # 3. Classrooms
        classrooms = [
            ('ROOM_301', 'Advanced AI & ML Lab', 'e2c56db5-dffb-48d2-b060-d0f5a71096e0'),
            ('ROOM_302', 'Cloud Computing Center', 'f7826da6-4fa2-4e98-8024-bc5b71e0893e'),
            ('ROOM_303', 'Cybersecurity Auditorium', 'a495bb10-c5b1-4b44-b512-1370f02d74de')
        ]
        for rid, rname, uuid in classrooms:
            cr_res = await session.execute(select(Classroom).where(Classroom.room_id == rid))
            if not cr_res.scalar_one_or_none():
                cr = Classroom(room_id=rid, room_name=rname, esp32_uuid=uuid)
                session.add(cr)
                print(f"[+] Created Classroom: {rid} ({rname}) - BLE UUID: {uuid}")

        # 4. Today's Timetable
        now = datetime.now()
        start1 = now.replace(minute=0, second=0, microsecond=0)
        end1 = start1 + timedelta(hours=1)
        start2 = end1 + timedelta(minutes=15)
        end2 = start2 + timedelta(hours=1)

        timetables = [
            ('ROOM_301', 'Deep Learning & Edge AI', start1, end1, 'prof.kumar@college.edu'),
            ('ROOM_302', 'Distributed Systems', start2, end2, 'prof.sharma@college.edu')
        ]
        for rid, subj, st_t, end_t, teach in timetables:
            tt_res = await session.execute(select(Timetable).where(Timetable.room_id == rid, Timetable.subject == subj))
            if not tt_res.scalar_one_or_none():
                tt = Timetable(
                    room_id=rid,
                    subject=subj,
                    start_time=st_t,
                    end_time=end_t,
                    teacher_email=teach
                )
                session.add(tt)
                print(f"[+] Created Timetable: {subj} in {rid} ({st_t.strftime('%H:%M')} - {end_t.strftime('%H:%M')})")

        await session.commit()
        print("\n[SUCCESS] All initial seed data populated successfully!")

if __name__ == '__main__':
    asyncio.run(seed())
