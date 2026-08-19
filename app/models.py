from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    roll_no = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    device_id = Column(String, nullable=True)
    face_encoding_json = Column(Text, nullable=True)
    role = Column(String, default='student')
    
    attendance_logs = relationship("AttendanceLog", back_populates="user")
    
class Classroom(Base):
    __tablename__ = "classrooms"
    
    room_id = Column(String, primary_key=True, index=True)
    room_name = Column(String, nullable=False)
    esp32_uuid = Column(String, unique=True, index=True, nullable=False)

    timetables = relationship("Timetable", back_populates="classroom")

class Timetable(Base):
    __tablename__ = "timetable"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String, ForeignKey("classrooms.room_id"))
    subject = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    teacher_email = Column(String, nullable=False)
    
    classroom = relationship("Classroom", back_populates="timetables")
    attendance_logs = relationship("AttendanceLog", back_populates="timetable")

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    roll_no = Column(String, ForeignKey("users.roll_no"))
    timetable_id = Column(Integer, ForeignKey("timetable.id"))
    timestamp = Column(DateTime, server_default=func.now())
    status = Column(String, nullable=False)
    issue_flag = Column(String, nullable=True)
    
    user = relationship("User", back_populates="attendance_logs")
    timetable = relationship("Timetable", back_populates="attendance_logs")
