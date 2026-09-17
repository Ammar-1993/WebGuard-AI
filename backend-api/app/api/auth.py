"""
WebGuard AI — Authentication API Routes
=========================================
مسارات تسجيل المستخدمين وتسجيل الدخول وإصدار JWT tokens.

ملاحظة أمنية (Security Review — البند 3):
  /login و /register محميان بـ Rate Limiting (slowapi) لمنع هجمات
  Brute Force / Credential Stuffing على /login، وإنشاء حسابات مزيفة
  بالجملة على /register. القيم قابلة للضبط عبر app/core/rate_limit.py
  أو متغيرات البيئة LOGIN_RATE_LIMIT / REGISTER_RATE_LIMIT.
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.database import get_collection
from app.core.rate_limit import limiter, LOGIN_RATE_LIMIT, REGISTER_RATE_LIMIT
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["🔐 Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Creates a new user account and issues a JWT Token.",
)
@limiter.limit(REGISTER_RATE_LIMIT)
async def register(request: Request, user_data: UserCreate):
    """تسجيل مستخدم جديد في النظام."""
    users = get_collection("users")

    # ─── التحقق من عدم وجود بريد إلكتروني مُسجل مسبقاً ───
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    # ─── التحقق من عدم وجود اسم مستخدم مُسجل مسبقاً ───
    existing_username = await users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered",
        )

    # ─── إنشاء المستخدم ───
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # ─── إصدار JWT Token ───
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email}
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            created_at=user_doc["created_at"],
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Verifies user credentials and issues a new JWT Token.",
)
@limiter.limit(LOGIN_RATE_LIMIT)
async def login(request: Request, credentials: UserLogin):
    """تسجيل دخول المستخدم وإصدار token جديد."""
    users = get_collection("users")

    # ─── البحث عن المستخدم ───
    user = await users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # ─── التحقق من كلمة المرور ───
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # ─── إصدار JWT Token ───
    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": user["email"]}
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns profile information for the currently authenticated user.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """يجلب بيانات الملف الشخصي للمستخدم الحالي."""
    users = get_collection("users")
    try:
        user = await users.find_one({"_id": ObjectId(current_user["user_id"])})
    except Exception:
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
    )