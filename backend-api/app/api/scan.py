"""
WebGuard AI — Scan API Routes
===============================
مسارات إدارة الفحوصات الأمنية: بدء فحص جديد، متابعة الحالة.
هنا يتم تنسيق خط الأنابيب الكامل:
  المستخدم ← Backend ← Scanner (ZAP) ← AI Analyzer ← حساب Score ← حفظ MongoDB
"""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.core.database import get_collection
from app.core.security import get_current_user
from app.models.scan import ScanRequest, ScanStatus, ScanStatusResponse
from app.services import scanner_client, ai_client
from app.services.scoring import calculate_security_score

router = APIRouter(prefix="/api/scan", tags=["🔍 Security Scan"])


async def _run_scan_pipeline(scan_id: str, target_url: str, user_id: str = None):
    """
    خط أنابيب الفحص الكامل — يعمل في الخلفية (Background Task).
    
    الخطوات:
    1. تحديث الحالة → scanning
    2. إرسال الرابط لخدمة Scanner (ZAP)
    3. تحديث الحالة → analyzing
    4. إرسال نتائج ZAP لخدمة AI Analyzer
    5. حساب Security Score
    6. حفظ التقرير النهائي في MongoDB
    7. تحديث الحالة → completed
    """
    scans = get_collection("scans")
    reports = get_collection("reports")

    # إذا لم يُمرر user_id مباشرة، يتم استخراجه من سجل الفحص
    if not user_id:
        try:
            scan_record = await scans.find_one({"_id": ObjectId(scan_id)})
            if scan_record:
                user_id = scan_record.get("user_id")
        except Exception:
            user_id = None

    try:
        # ─── المرحلة 1: فحص ZAP ───
        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {
                "status": ScanStatus.SCANNING,
                "progress": 10,
                "message": "Sending URL to OWASP ZAP scanning engine...",
            }},
        )

        scan_results = await scanner_client.start_scan(target_url)
        raw_alerts = scan_results.get("alerts", [])

        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {
                "progress": 50,
                "message": f"Scan completed — discovered {len(raw_alerts)} alerts. Starting AI analysis...",
            }},
        )

        # ─── المرحلة 2: تحليل الذكاء الاصطناعي ───
        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {"status": ScanStatus.ANALYZING, "progress": 60}},
        )

        ai_results = await ai_client.analyze_vulnerabilities(raw_alerts)
        ai_analysis = ai_results.get("analysis", [])
        summary = ai_results.get("summary", "")

        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {
                "progress": 85,
                "message": "Analysis completed — calculating security score...",
            }},
        )

        # ─── المرحلة 3: حساب Security Score ───
        # نستبعد الإنذارات الخاطئة التي حددها الذكاء الاصطناعي
        confirmed_vulns = []
        false_positives_count = 0

        for i, alert in enumerate(raw_alerts):
            if i < len(ai_analysis) and ai_analysis[i].get("is_false_positive", False):
                false_positives_count += 1
            else:
                confirmed_vulns.append(alert)

        security_score = calculate_security_score(confirmed_vulns)

        # ─── المرحلة 4: حفظ التقرير النهائي ───
        report_doc = {
            "scan_id": scan_id,
            "target_url": target_url,
            "user_id": user_id,
            "scan_date": datetime.now(timezone.utc),
            "security_score": security_score.model_dump(),
            "total_vulnerabilities": len(raw_alerts),
            "confirmed_vulnerabilities": len(confirmed_vulns),
            "false_positives_count": false_positives_count,
            "vulnerabilities": raw_alerts,
            "ai_analysis": ai_analysis,
            "summary": summary,
        }
        await reports.insert_one(report_doc)

        # ─── المرحلة 5: تحديث حالة الفحص → مكتمل ───
        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {
                "status": ScanStatus.COMPLETED,
                "progress": 100,
                "message": "Scan and analysis completed successfully ✅",
                "completed_at": datetime.now(timezone.utc),
                "score": security_score.score,
                "grade": security_score.grade,
            }},
        )

    except Exception as e:
        # ─── في حالة فشل أي مرحلة ───
        await scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": {
                "status": ScanStatus.FAILED,
                "message": f"Scan failed: {str(e)}",
                "completed_at": datetime.now(timezone.utc),
            }},
        )


@router.post(
    "",
    response_model=ScanStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start new security scan",
    description="Receives target URL and starts scan pipeline in the background.",
)
async def start_new_scan(
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """يبدأ فحصاً أمنياً جديداً ويُعيد معرّف الفحص فوراً."""
    scans = get_collection("scans")

    # ─── إنشاء سجل الفحص في قاعدة البيانات ───
    scan_doc = {
        "target_url": str(scan_request.target_url),
        "status": ScanStatus.PENDING,
        "progress": 0,
        "message": "Request received — waiting to start...",
        "user_id": current_user["user_id"],
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    result = await scans.insert_one(scan_doc)
    scan_id = str(result.inserted_id)

    # ─── بدء خط الأنابيب في الخلفية ───
    background_tasks.add_task(
        _run_scan_pipeline,
        scan_id,
        str(scan_request.target_url),
        current_user["user_id"],
    )

    return ScanStatusResponse(
        scan_id=scan_id,
        status=ScanStatus.PENDING,
        target_url=str(scan_request.target_url),
        progress=0,
        message="Request received — scan will start shortly...",
        created_at=scan_doc["created_at"],
    )


@router.get(
    "/{scan_id}",
    response_model=ScanStatusResponse,
    summary="Query scan status",
    description="Returns current status and progress for a specific scan.",
)
async def get_scan_status(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
):
    """يجلب حالة فحص محدد بمعرّفه."""
    scans = get_collection("scans")

    try:
        scan = await scans.find_one({"_id": ObjectId(scan_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scan ID",
        )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    # ─── التحقق من صلاحية الوصول للفحص (Authorization Check) ───
    scan_user_id = scan.get("user_id")
    if scan_user_id and scan_user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this scan",
        )

    return ScanStatusResponse(
        scan_id=str(scan["_id"]),
        status=scan["status"],
        target_url=scan["target_url"],
        progress=scan.get("progress", 0),
        message=scan.get("message", ""),
        created_at=scan["created_at"],
        completed_at=scan.get("completed_at"),
    )
