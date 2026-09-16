"""
WebGuard AI — Reports API Routes
==================================
مسارات إدارة التقارير الأمنية: جلب جميع التقارير، جلب تقرير واحد، حذف تقرير.
"""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_collection
from app.core.security import get_current_user

router = APIRouter(prefix="/api/reports", tags=["📊 Reports"])


@router.get(
    "",
    summary="Get all reports",
    description="Returns a brief list of all security reports for the authenticated user, sorted from newest.",
)
async def get_all_reports(
    current_user: dict = Depends(get_current_user),
):
    """يجلب جميع التقارير الأمنية الخاصة بالمستخدم الحالي مرتبة تنازلياً حسب التاريخ."""
    reports = get_collection("reports")
    user_id = current_user["user_id"]

    cursor = reports.find(
        {"user_id": user_id},
        {
            "scan_id": 1,
            "target_url": 1,
            "scan_date": 1,
            "security_score.score": 1,
            "security_score.grade": 1,
            "total_vulnerabilities": 1,
            "false_positives_count": 1,
        },
    ).sort("scan_date", -1)

    results = []
    async for report in cursor:
        score_data = report.get("security_score", {})
        results.append({
            "id": str(report["_id"]),
            "scan_id": report.get("scan_id", ""),
            "target_url": report.get("target_url", ""),
            "scan_date": report.get("scan_date"),
            "score": score_data.get("score", 0),
            "grade": score_data.get("grade", "F"),
            "total_vulnerabilities": report.get("total_vulnerabilities", 0),
            "false_positives_count": report.get("false_positives_count", 0),
        })

    return {"reports": results, "total": len(results)}


@router.get(
    "/{report_id}",
    summary="Get single report details",
    description="Returns the full security report with AI analysis and security score.",
)
async def get_report_detail(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """يجلب تقرير أمني مُفصّل بمعرّفه للمستخدم المصرح له فقط."""
    reports = get_collection("reports")

    try:
        report = await reports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        report = None

    if not report:
        # ─── محاولة البحث بـ scan_id ───
        report = await reports.find_one({"scan_id": report_id})

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # ─── التحقق من ملكية التقرير (Authorization Check) ───
    report_user_id = report.get("user_id")
    if report_user_id and report_user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this report",
        )

    # ─── تحويل ObjectId لنص ───
    report["id"] = str(report.pop("_id"))

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report",
    description="Deletes a security report by ID if owned by the current user.",
)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """يحذف تقرير أمني بمعرّفه للمستخدم المالك فقط."""
    reports = get_collection("reports")
    scans = get_collection("scans")
    user_id = current_user["user_id"]

    try:
        report = await reports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        report = None

    if not report:
        report = await reports.find_one({"scan_id": report_id})

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # ─── التحقق من صلاحية الحذف (Authorization Check) ───
    if report.get("user_id") and report.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this report",
        )

    # ─── حذف التقرير ───
    await reports.delete_one({"_id": report["_id"]})

    # ─── حذف سجل الفحص المرتبط أيضاً ───
    scan_id = report.get("scan_id")
    if scan_id:
        try:
            await scans.delete_one({"_id": ObjectId(scan_id), "user_id": user_id})
        except Exception:
            pass
