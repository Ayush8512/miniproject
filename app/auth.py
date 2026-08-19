from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone
import random

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, TokenResponse, ForgotPasswordRequest, OTPResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

otp_cache = {}

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        roll_no: str = payload.get("sub")
        if roll_no is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.roll_no == roll_no))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.roll_no == login_data.roll_no))
    user = result.scalars().first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect roll_no or password",
        )
        
    if user.device_id is None:
        user.device_id = login_data.device_id
        await db.commit()
        await db.refresh(user)
    elif user.device_id != login_data.device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device binding mismatch. Contact admin to reset."
        )
        
    access_token = create_access_token(data={"sub": user.roll_no, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset_device/{roll_no}")
async def reset_device(roll_no: str, current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.roll_no == roll_no))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.device_id = None
    await db.commit()
    
    return {"message": f"Device reset for {roll_no} successful."}

@router.post("/forgot_password", response_model=OTPResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found")
        
    otp = str(random.randint(100000, 999999))
    otp_cache[request.email] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    
    return {"message": "OTP sent", "otp": otp}
