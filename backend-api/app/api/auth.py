"""
WebGuard AI — Authentication API Routes
=========================================
مسارات تسجيل المستخدمين وتسجيل الدخول وإصدار JWT tokens.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.core.database import get_collection
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["🔐 المصادقة"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="تسجيل مستخدم جديد",
    description="يُنشئ حساب مستخدم جديد ويُصدر JWT Token.",
)
async def register(user_data: UserCreate):
    """تسجيل مستخدم جديد في النظام."""
    users = get_collection("users")

    # ─── التحقق من عدم وجود بريد إلكتروني مُسجل مسبقاً ───
    existing_user = await users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="البريد الإلكتروني مُسجل مسبقاً",
        )

    # ─── التحقق من عدم وجود اسم مستخدم مُسجل مسبقاً ───
    existing_username = await users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="اسم المستخدم مُسجل مسبقاً",
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
    summary="تسجيل الدخول",
    description="يتحقق من بيانات المستخدم ويُصدر JWT Token جديد.",
)
async def login(credentials: UserLogin):
    """تسجيل دخول المستخدم وإصدار token جديد."""
    users = get_collection("users")

    # ─── البحث عن المستخدم ───
    user = await users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
        )

    # ─── التحقق من كلمة المرور ───
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
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
