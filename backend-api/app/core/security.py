"""
WebGuard AI — Security & Authentication (JWT + Password Hashing)
=================================================================
يوفر دوال إنشاء والتحقق من JWT tokens وتشفير كلمات المرور.
يتضمن Dependency لحماية الـ Endpoints التي تتطلب مصادقة.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# ─── إعدادات تشفير كلمات المرور ───
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── نظام استخراج الـ Token من الـ Header ───
security_scheme = HTTPBearer()


# ═══════════════════════════════════════════
#  دوال كلمات المرور
# ═══════════════════════════════════════════

def hash_password(password: str) -> str:
    """يُشفّر كلمة المرور باستخدام خوارزمية bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """يتحقق من تطابق كلمة المرور المُدخلة مع النسخة المُشفّرة."""
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════
#  دوال JWT Token
# ═══════════════════════════════════════════

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    يُنشئ JWT Token يحتوي على بيانات المستخدم.
    
    Args:
        data: البيانات المُراد تضمينها في الـ Token (مثل user_id, email)
        expires_delta: مدة الصلاحية (اختياري، الافتراضي من الإعدادات)
    
    Returns:
        JWT Token كنص مُشفّر
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    يفكّ تشفير JWT Token ويُرجع البيانات المُخزّنة فيه.
    
    Raises:
        HTTPException 401: إذا كان الـ Token منتهي الصلاحية أو غير صالح
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ═══════════════════════════════════════════
#  FastAPI Dependency — حماية الـ Endpoints
# ═══════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    Dependency يُستخدم لحماية الـ Endpoints.
    يستخرج الـ Token من الـ Header ويتحقق من صلاحيته.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data not found in Token",
        )
    return {"user_id": user_id, "email": payload.get("email", "")}
