"""
WebGuard AI — Reports API Routes
==================================
مسارات إدارة التقارير الأمنية: جلب جميع التقارير، جلب تقرير واحد، حذف تقرير.
"""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_collection
from app.core.security import get_current_user

router = APIRouter(prefix="/api/reports", tags=["📊 التقارير"])


@router.get(
    "",
    summary="جلب جميع التقارير",
    description="يُرجع قائمة مختصرة بجميع التقارير الأمنية مرتبة من الأحدث.",
)
async def get_all_reports(
    current_user: dict = Depends(get_current_user),
):
    """يجلب جميع التقارير الأمنية مرتبة تنازلياً حسب التاريخ."""
    reports = get_collection("reports")

    cursor = reports.find(
        {},
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
    summary="جلب تقرير واحد بالتفصيل",
    description="يُرجع التقرير الأمني الكامل مع تحليل الذكاء الاصطناعي ومؤشر الأمان.",
)
async def get_report_detail(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """يجلب تقرير أمني مُفصّل بمعرّفه."""
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
            detail="التقرير غير موجود",
        )

    # ─── تحويل ObjectId لنص ───
    report["id"] = str(report.pop("_id"))

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="حذف تقرير",
    description="يحذف تقرير أمني بمعرّفه.",
)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
):
    """يحذف تقرير أمني بمعرّفه."""
    reports = get_collection("reports")
    scans = get_collection("scans")

    try:
        result = await reports.delete_one({"_id": ObjectId(report_id)})
    except Exception:
        result = None

    if not result or result.deleted_count == 0:
        result = await reports.delete_one({"scan_id": report_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التقرير غير موجود",
        )

    # ─── حذف سجل الفحص المرتبط أيضاً ───
    await scans.delete_one({"_id": ObjectId(report_id)})
