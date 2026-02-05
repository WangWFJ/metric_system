# =============================
# app/api/endpoints/indicators.py
# =============================
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import io
from datetime import date

from models.common import PageResponse
from models.metrics_schemas import MajorMetricsResponse, TypeMetricsResponse, DistrictMetricsResponse, CenterMetricsResponse, DistrictOut, MajorOut, CenterOut, EvaluationTypeOut, IndicatorSimpleOut, IndicatorDataCreate, IndicatorCenterDataCreate, IndicatorCenterDataDelete, CenterLatestQueryOut
from models.metrics_schemas import IndicatorOut, IndicatorBase
from models.metrics_schemas import IndicatorDataDelete
from models.metrics_schemas import IndicatorDataOut, IndicatorCenterDataOut, IndicatorCenterDataResponse, IndicatorDataQuery, IndicatorLatestQueryOut, IndicatorDataResponse, IndicatorDashboardOut  
from models.database import get_session
from core.security import require_permission
from models.metrics import IndicatorDataV2 as IndicatorData, Indicator, District, EvaluationType, Major, Center, IndicatorCenterData
from sqlalchemy import select
from utils.threadpool import run_pandas
from utils.excel_utils import (
    build_template_xlsx,
    parse_indicator_upload_records,
    parse_center_upload_records,
    parse_indicator_manage_upload_records,
    build_export_xlsx,
    build_center_pivot_xlsx,
    build_district_pivot_xlsx,
)
from services.indicator_service import (
    query_metrics,
    latest_metrics,
    query_series,
    delete_metrics,
    get_indicators_by_district, 
    get_latest_indicator_data, 
    get_metrics_by_major, 
    get_metrics_by_type, 
    get_all_districts,
    get_all_majors,
    get_all_evaluation_types,
    get_all_indicators_simple,
    get_indicators_simple_by_type,
    search_indicators,
    create_indicator_data,
    get_all_circles,
    get_all_centers,
    get_indicators_by_center,
    query_center_metrics,
    create_center_data,
    update_center_data,
    delete_center_metrics,
    get_latest_center_indicator_data,
    query_center_series
)
from services.indicator_service import update_indicator_data

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@router.get("/districts", response_model=list[DistrictOut])
async def get_districts(session: AsyncSession = Depends(get_session)):
    """
    获取所有区县列表
    """
    return await get_all_districts(session)

@router.get("/majors", response_model=list[MajorOut])
async def get_majors(session: AsyncSession = Depends(get_session)):
    """
    获取所有专业列表
    """
    return await get_all_majors(session)

@router.get("/evaluation_types", response_model=list[EvaluationTypeOut])
async def get_evaluation_types(session: AsyncSession = Depends(get_session)):
    """
    获取所有考核类型列表
    """
    return await get_all_evaluation_types(session)

@router.get("/circles", response_model=list[int])
async def get_circles(session: AsyncSession = Depends(get_session)):
    """
    获取所有圈层ID列表（来自区县表去重）
    """
    return await get_all_circles(session)

@router.get("/centers", response_model=list[CenterOut], dependencies=[Depends(require_permission("indicator_data:view"))])
async def get_centers(
    district_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    return await get_all_centers(session, district_id=district_id)

@router.get("/center", response_model=CenterMetricsResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def query_center_indicators(
    center_id: int | None = None,
    center_name: str | None = None,
    date: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    data = await get_indicators_by_center(
        session=session,
        center_id=center_id,
        center_name=center_name,
        stat_date=date,
    )
    return data

@router.get("/center/query", response_model=IndicatorCenterDataResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def center_metrics_query(
    indicator_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await query_center_metrics(
        session=session,
        indicator_id=indicator_id,
        center_id=center_id,
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
        major_id=major_id,
        type_id=type_id,
        page=page,
        size=size,
        order_by=order_by,
        desc_order=desc,
    )
    return {"items": rows, "total": total}

@router.get("/center/by_name_or_id", response_model=list[CenterLatestQueryOut], dependencies=[Depends(require_permission("indicator_data:view"))])
async def get_centers_by_name_or_id(
    indicator_id: int | None = None,
    indicator_name: str | None = None,
    stat_date: str | None = None,
    district_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await get_latest_center_indicator_data(
        session=session,
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        stat_date=stat_date,
        district_id=district_id,
    )

@router.get("/center/series", response_model=IndicatorCenterDataResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def center_metrics_series(
    indicator_id: int = Query(...),
    center_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    size: int = Query(180, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await query_center_series(
        session=session,
        indicator_id=indicator_id,
        center_id=center_id,
        start_date=start_date,
        end_date=end_date,
        size=size,
    )
    return {"items": rows, "total": total}


@router.get("/list", response_model=list[IndicatorSimpleOut])
async def get_indicators_list(session: AsyncSession = Depends(get_session)):
    """
    获取所有指标简单列表（用于下拉选择）
    """
    return await get_all_indicators_simple(session)

@router.get("/indicators_by_type", response_model=list[IndicatorSimpleOut])
async def get_indicators_by_type(type_id: int = Query(...), session: AsyncSession = Depends(get_session)):
    return await get_indicators_simple_by_type(session, type_id)

@router.get("/indicators/search", response_model=list[IndicatorSimpleOut])
async def indicators_search(
    q: str = Query(..., min_length=1),
    type_id: Optional[int] = Query(None),
    size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    return await search_indicators(session, q=q, type_id=type_id, size=size)
@router.post("/data", response_model=IndicatorDataOut, status_code=201, dependencies=[Depends(require_permission("indicator_data:add"))])
async def create_data(
    data: IndicatorDataCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    创建指标数据
    """
    return await create_indicator_data(session, data)

@router.post("/data/update", response_model=IndicatorDataOut, dependencies=[Depends(require_permission("indicator_data:edit"))])
async def update_data(
    data: IndicatorDataCreate,
    session: AsyncSession = Depends(get_session)
):
    return await update_indicator_data(session, data)

@router.delete("/data", dependencies=[Depends(require_permission("indicator_data:delete"))])
async def delete_data(
    payload: IndicatorDataDelete,
    session: AsyncSession = Depends(get_session)
):
    deleted = await delete_metrics(
        session=session,
        ids=payload.ids,
        indicator_id=payload.indicator_id,
        district_id=payload.district_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    return {"deleted": deleted}

# @router.get(
#     "/dashboard",
#     response_model=PageResponse[IndicatorDashboardOut],
#     summary="指标看板查询（按区县）"
# )
# async def indicator_dashboard(
#     indicator_id: Optional[int] = Query(None, description="指标ID"),
#     indicator_name: Optional[str] = Query(None, description="指标名称（模糊）"),
#     district_id: Optional[int] = Query(None, description="区县ID"),
#     circle_id: Optional[int] = Query(None, description="圈层ID"),
#     major_id: Optional[int] = Query(None, description="专业ID"),
#     type_id: Optional[int] = Query(None, description="指标类型ID"),
#     stat_date: Optional[date] = Query(None, description="统计日期，不传则查询最新一期"),
#     page: int = Query(1, ge=1),
#     size: int = Query(50, ge=1, le=500),
#     session: AsyncSession = Depends(get_session),
# ):
#     data, total = await query_indicator_dashboard(
#         session=session,
#         indicator_id=indicator_id,
#         indicator_name=indicator_name,
#         district_id=district_id,
#         circle_id=circle_id,
#         major_id=major_id,
#         type_id=type_id,
#         stat_date=stat_date,
#         page=page,
#         size=size,
#     )

#     return PageResponse(
#         data=data,
#         total=total,
#         page=page,
#         size=size
#     )


@router.get("/query", response_model=IndicatorDataResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def metrics_query(
    indicator_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    district_ids: Optional[list[int]] = Query(None),
    district_name: Optional[str] = Query(None),
    circle_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await query_metrics(
        session=session,
        indicator_id=indicator_id,
        district_id=district_id,
        district_ids=district_ids,
        district_name=district_name,
        circle_id=circle_id,
        start_date=start_date,
        end_date=end_date,
        major_id=major_id,
        type_id=type_id,
        page=page,
        size=size,
        order_by=order_by,
        desc_order=desc,
    )
    return {"items": rows, "total": total}

@router.get("/series", response_model=IndicatorDataResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def metrics_series(
    indicator_id: int = Query(...),
    district_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    size: int = Query(180, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await query_series(
        session=session,
        indicator_id=indicator_id,
        district_id=district_id,
        start_date=start_date,
        end_date=end_date,
        size=size,
    )
    return {"items": rows, "total": total}
@router.get("/snapshot", response_model=IndicatorDataResponse, dependencies=[Depends(require_permission("indicator_data:view"))])
async def metrics_snapshot(
    indicator_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    district_name: Optional[str] = Query(None),
    circle_id: Optional[int] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    rows, total = await latest_metrics(
        session=session,
        indicator_id=indicator_id,
        district_id=district_id,
        district_name=district_name,
        circle_id=circle_id,
        major_id=major_id,
        type_id=type_id,
        page=page,
        size=size,
        order_by=order_by,
        desc_order=desc,
    )
    return {"items": rows, "total": total}

@router.get("/upload/template", dependencies=[Depends(require_permission("indicator_data:add"))])
async def download_upload_template(session: AsyncSession = Depends(get_session)):
    columns = [
        "指标名称",
        "区县",
        "统计日期",
        "完成值",
        "基准值",
        "挑战值",
        "豁免值",
        "零容忍值",
        "得分",
    ]
    desc_row = {
        "指标名称": "必填，示例：线退服率",
        "区县": "必填，区县中文名或简称，例如：浦东新区/浦东",
        "统计日期": "必填，YYYY-MM-DD",
        "完成值": "必填，数值如 0.1234",
        "基准值": "选填",
        "挑战值": "选填",
        "豁免值": "选填",
        "零容忍值": "选填",
        "得分": "选填",
    }
    sample_row = {
        "指标名称": "示例指标A",
        "区县": "示例区县A",
        "统计日期": "2026-01-13",
        "完成值": 123.45,
        "基准值": 100,
        "挑战值": 150,
        "豁免值": 0,
        "零容忍值": 0,
        "得分": 95.5,
    }
    xlsx = await run_pandas(build_template_xlsx, columns, desc_row, sample_row, "模板")
    buf = io.BytesIO(xlsx)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=indicator_import_template.xlsx"})
@router.post("/upload", status_code=201, dependencies=[Depends(require_permission("indicator_data:add"))])
async def upload_indicator_data(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """
    上传指标数据 Excel 文件
    文件格式要求: indicator_name, district_name, stat_date, value, (optional: benchmark, challenge, etc.)
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")

    try:
        contents = await file.read()
        records, row_count = await run_pandas(parse_indicator_upload_records, contents)

        # Process each row
        # To optimize, we should cache indicators and districts
        indicators = (await session.execute(select(Indicator))).scalars().all()
        ind_map = {i.indicator_name: i for i in indicators}
        
        districts = (await session.execute(select(District))).scalars().all()
        dist_map = {d.district_name: d for d in districts}
        dist_simple_map = {d.simple_name: d for d in districts}
        eval_types = (await session.execute(select(EvaluationType))).scalars().all()
        type_name_map = {t.type_name: t.type_id for t in eval_types}
        
        new_data = []
        errors = []
        
        for index, row in enumerate(records):
            ind_name = row.get("indicator_name")
            dist_name = row.get("district_name")
            
            if ind_name not in ind_map:
                errors.append(f"Row {index+1}: Indicator '{ind_name}' not found")
                continue
            dist = dist_map.get(dist_name) or dist_simple_map.get(dist_name)
            if not dist:
                errors.append(f"Row {index+1}: District '{dist_name}' not found")
                continue
                
            ind = ind_map[ind_name]
            
            # Determine type_id from excel or indicator default
            provided_type_id = None
            if "type_id" in row and row.get("type_id") is not None:
                try:
                    provided_type_id = int(row.get('type_id'))
                except Exception:
                    errors.append(f"Row {index+1}: Invalid type_id value")
                    continue
            elif "type_name" in row and row.get("type_name") is not None:
                tname = str(row.get('type_name')).strip()
                if tname in type_name_map:
                    provided_type_id = type_name_map[tname]
                else:
                    errors.append(f"Row {index+1}: Evaluation type '{tname}' not found")
                    continue

            # Validate provided type if any
            if provided_type_id is not None and ind.type_id is not None and provided_type_id != ind.type_id:
                errors.append(f"Row {index+1}: type_id mismatch with indicator definition")
                continue

            final_type_id = provided_type_id or ind.type_id

            # Check for existing data
            stat_date = row.get("stat_date")
            if not stat_date:
                errors.append(f"Row {index+1}: Invalid stat_date value")
                continue
            existing_stmt = select(IndicatorData).where(
                IndicatorData.indicator_id == ind.indicator_id,
                IndicatorData.district_id == dist.district_id,
                IndicatorData.stat_date == stat_date
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing.value = row.get("value")
                existing.benchmark = row.get("benchmark")
                existing.challenge = row.get("challenge")
                if row.get("exemption") is not None:
                    existing.exemption = row.get("exemption")
                if row.get("zero_tolerance") is not None:
                    existing.zero_tolerance = row.get("zero_tolerance")
                if row.get("score") is not None:
                    existing.score = row.get("score")
                if existing.type_id is None:
                    existing.type_id = final_type_id
                if existing.major_id is None:
                    existing.major_id = ind.major_id
                # ...
            else:
                # Create IndicatorData object
                data_obj = IndicatorData(
                    indicator_id=ind.indicator_id,
                    indicator_name=ind.indicator_name,
                    type_id=final_type_id,
                    major_id=ind.major_id,
                    is_positive=ind.is_positive,
                    circle_id=dist.circle_id or 0, # Default to 0 if None
                    district_id=dist.district_id,
                    district_name=dist.district_name,
                    stat_date=stat_date,
                    value=row.get("value"),
                    benchmark=row.get("benchmark"),
                    challenge=row.get("challenge"),
                    exemption=row.get("exemption"),
                    zero_tolerance=row.get("zero_tolerance"),
                    score=row.get("score"),
                    # ... other fields
                )
                session.add(data_obj)
            
        if errors:
            await session.rollback()
            raise HTTPException(status_code=400, detail={"message": "Data validation failed", "errors": errors[:10]}) # Return first 10 errors
            
        await session.commit()
        return {"message": "Data uploaded successfully", "count": row_count}
        
    except Exception as e:
        await session.rollback()
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/center/upload/template", dependencies=[Depends(require_permission("indicator_data:add"))])
async def download_center_upload_template(session: AsyncSession = Depends(get_session)):
    columns = [
        "指标名称",
        "支撑中心",
        "统计日期",
        "完成值",
        "基准值",
        "挑战值",
        "得分",
    ]
    desc_row = {
        "指标名称": "必填，示例：线退服率",
        "支撑中心": "必填，支撑中心名字（centers.center_name）",
        "统计日期": "必填，YYYY-MM-DD",
        "完成值": "必填，数值如 0.1234",
        "基准值": "选填",
        "挑战值": "选填",
        "得分": "选填",
    }
    sample_row = {
        "指标名称": "示例指标A",
        "支撑中心": "示例支撑中心A",
        "统计日期": "2026-01-13",
        "完成值": 123.45,
        "基准值": 100,
        "挑战值": 150,
        "得分": 95.5,
    }
    xlsx = await run_pandas(build_template_xlsx, columns, desc_row, sample_row, "模板")
    buf = io.BytesIO(xlsx)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=center_indicator_import_template.xlsx"},
    )

@router.post("/center/upload", status_code=201, dependencies=[Depends(require_permission("indicator_data:add"))])
async def upload_center_indicator_data(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")

    try:
        contents = await file.read()
        records, row_count = await run_pandas(parse_center_upload_records, contents)

        indicators = (await session.execute(select(Indicator))).scalars().all()
        ind_map = {i.indicator_name: i for i in indicators}
        centers = (await session.execute(select(Center))).scalars().all()
        center_map = {c.center_name: c for c in centers}
        eval_types = (await session.execute(select(EvaluationType))).scalars().all()
        type_name_map = {t.type_name: t.type_id for t in eval_types}

        errors = []
        for index, row in enumerate(records):
            ind_name = row.get("indicator_name")
            center_name = row.get("center_name")
            if ind_name not in ind_map:
                errors.append(f"Row {index+1}: Indicator '{ind_name}' not found")
                continue
            center = center_map.get(center_name)
            if not center:
                errors.append(f"Row {index+1}: Center '{center_name}' not found")
                continue

            ind = ind_map[ind_name]
            provided_type_id = None
            if "type_id" in row and row.get("type_id") is not None:
                try:
                    provided_type_id = int(row.get("type_id"))
                except Exception:
                    errors.append(f"Row {index+1}: Invalid type_id value")
                    continue
            elif "type_name" in row and row.get("type_name") is not None:
                tname = str(row.get("type_name")).strip()
                if tname in type_name_map:
                    provided_type_id = type_name_map[tname]
                else:
                    errors.append(f"Row {index+1}: Evaluation type '{tname}' not found")
                    continue

            if provided_type_id is not None and ind.type_id is not None and provided_type_id != ind.type_id:
                errors.append(f"Row {index+1}: type_id mismatch with indicator definition")
                continue
            final_type_id = provided_type_id or ind.type_id

            stat_date = row.get("stat_date")
            if not stat_date:
                errors.append(f"Row {index+1}: Invalid stat_date value")
                continue
            existing_stmt = select(IndicatorCenterData).where(
                IndicatorCenterData.indicator_id == ind.indicator_id,
                IndicatorCenterData.center_id == center.center_id,
                IndicatorCenterData.stat_date == stat_date,
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing.value = row.get("value")
                existing.benchmark = row.get("benchmark")
                existing.challenge = row.get("challenge")
                if row.get("score") is not None:
                    existing.score = row.get("score")
                if existing.type_id is None:
                    existing.type_id = final_type_id
                if existing.major_id is None:
                    existing.major_id = ind.major_id
            else:
                data_obj = IndicatorCenterData(
                    indicator_id=ind.indicator_id,
                    indicator_name=ind.indicator_name,
                    type_id=final_type_id,
                    major_id=ind.major_id,
                    is_positive=ind.is_positive,
                    center_id=center.center_id,
                    center_name=center.center_name,
                    stat_date=stat_date,
                    value=row.get("value"),
                    benchmark=row.get("benchmark"),
                    challenge=row.get("challenge"),
                    score=row.get("score"),
                )
                session.add(data_obj)

        if errors:
            await session.rollback()
            raise HTTPException(status_code=400, detail={"message": "Data validation failed", "errors": errors[:10]})

        await session.commit()
        return {"message": "Data uploaded successfully", "count": row_count}
    except Exception as e:
        await session.rollback()
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/center/data", response_model=IndicatorCenterDataOut, status_code=201, dependencies=[Depends(require_permission("indicator_data:add"))])
async def create_center_metrics_data(
    data: IndicatorCenterDataCreate,
    session: AsyncSession = Depends(get_session),
):
    obj = await create_center_data(session, data)
    return IndicatorCenterDataOut.model_validate(obj)

@router.post("/center/data/update", response_model=IndicatorCenterDataOut, dependencies=[Depends(require_permission("indicator_data:edit"))])
async def update_center_metrics_data(
    data: IndicatorCenterDataCreate,
    session: AsyncSession = Depends(get_session),
):
    return await update_center_data(session, data)

@router.delete("/center/data", dependencies=[Depends(require_permission("indicator_data:delete"))])
async def delete_center_metrics_data(
    payload: IndicatorCenterDataDelete,
    session: AsyncSession = Depends(get_session),
):
    deleted = await delete_center_metrics(
        session=session,
        ids=payload.ids,
        indicator_id=payload.indicator_id,
        center_id=payload.center_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    return {"deleted": deleted}

@router.get("/export", summary="导出当前筛选指标数据为Excel", dependencies=[Depends(require_permission("indicator_data:view"))])
async def export_metrics(
    indicator_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    district_name: Optional[str] = Query(None),
    circle_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    all_items: list[dict] = []
    page = 1
    size = 1000
    while True:
        rows, total = await query_metrics(
            session=session,
            indicator_id=indicator_id,
            district_id=district_id,
            district_name=district_name,
            circle_id=circle_id,
            start_date=start_date,
            end_date=end_date,
            major_id=major_id,
            type_id=type_id,
            page=page,
            size=size,
            order_by=order_by,
            desc_order=desc,
        )
        for r in rows:
            all_items.append({
                "indicator_name": getattr(r, "indicator_name", ""),
                "district_name": getattr(r, "district_name", ""),
                "stat_date": getattr(r, "stat_date", ""),
                "value": getattr(r, "value", None),
                "score": getattr(r, "score", None),
                "benchmark": getattr(r, "benchmark", None),
                "challenge": getattr(r, "challenge", None),
                "exemption": getattr(r, "exemption", None),
                "zero_tolerance": getattr(r, "zero_tolerance", None),
            })
        if page * size >= total or not rows:
            break
        page += 1
    if not all_items:
        all_items = [{"indicator_name": "", "district_name": "", "stat_date": "", "value": None}]
    xlsx = await run_pandas(
        build_export_xlsx,
        all_items,
        {
            "indicator_name": "指标名称",
            "district_name": "区县",
            "stat_date": "统计日期",
            "value": "完成值",
            "score": "得分",
            "benchmark": "基准值",
            "challenge": "挑战值",
            "exemption": "豁免值",
            "zero_tolerance": "零容忍值",
        },
        "导出",
    )
    buf = io.BytesIO(xlsx)
    fname = "metrics_export.xlsx"
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={fname}"})

@router.get("/center/export", summary="导出当前筛选支撑中心指标数据为Excel", dependencies=[Depends(require_permission("indicator_data:view"))])
async def export_center_metrics(
    indicator_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    all_items: list[dict] = []
    page = 1
    size = 2000
    while True:
        rows, total = await query_center_metrics(
            session=session,
            indicator_id=indicator_id,
            center_id=center_id,
            district_id=district_id,
            start_date=start_date,
            end_date=end_date,
            major_id=major_id,
            type_id=type_id,
            page=page,
            size=size,
            order_by=order_by,
            desc_order=desc,
        )
        for r in rows:
            all_items.append(
                {
                    "indicator_name": getattr(r, "indicator_name", ""),
                    "district_name": getattr(r, "district_name", ""),
                    "center_name": getattr(r, "center_name", ""),
                    "stat_date": getattr(r, "stat_date", ""),
                    "value": getattr(r, "value", None),
                    "benchmark": getattr(r, "benchmark", None),
                    "challenge": getattr(r, "challenge", None),
                    "score": getattr(r, "score", None),
                }
            )
        if page * size >= total or not rows:
            break
        page += 1
    if not all_items:
        all_items = [{"indicator_name": "", "district_name": "", "center_name": "", "stat_date": "", "value": None}]
    xlsx = await run_pandas(
        build_export_xlsx,
        all_items,
        {
            "indicator_name": "指标名称",
            "district_name": "区县",
            "center_name": "支撑中心",
            "stat_date": "统计日期",
            "value": "完成值",
            "benchmark": "基准值",
            "challenge": "挑战值",
            "score": "得分",
        },
        "导出",
    )
    buf = io.BytesIO(xlsx)
    fname = "center_metrics_export.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )

@router.get("/center/export_v2", summary="汇总导出（支撑中心×指标，按统计时间分Sheet）", dependencies=[Depends(require_permission("indicator_data:view"))])
async def export_center_metrics_v2(
    indicator_id: Optional[int] = Query(None),
    center_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    page = 1
    size = 3000
    all_rows = []
    while True:
        rows, total = await query_center_metrics(
            session=session,
            indicator_id=indicator_id,
            center_id=center_id,
            district_id=district_id,
            start_date=start_date,
            end_date=end_date,
            major_id=major_id,
            type_id=type_id,
            page=page,
            size=size,
            order_by=order_by,
            desc_order=desc,
        )
        all_rows.extend(rows)
        if page * size >= total or not rows:
            break
        page += 1
    if not all_rows:
        xlsx = await run_pandas(build_center_pivot_xlsx, [])
        buf = io.BytesIO(xlsx)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=center_metrics_export.xlsx"},
        )
    pivot_rows = [
        {
            "indicator_id": getattr(r, "indicator_id", None),
            "indicator_name": getattr(r, "indicator_name", None),
            "is_positive": getattr(r, "is_positive", None),
            "center_id": getattr(r, "center_id", None),
            "center_name": getattr(r, "center_name", None),
            "district_name": getattr(r, "district_name", None),
            "stat_date": getattr(r, "stat_date", None),
            "value": getattr(r, "value", None),
            "score": getattr(r, "score", None),
        }
        for r in all_rows
    ]
    xlsx = await run_pandas(build_center_pivot_xlsx, pivot_rows)
    buf = io.BytesIO(xlsx)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=center_metrics_export.xlsx"},
    )

@router.get("/export_v2", summary="导出为按统计时间分Sheet的透视表（区县×指标）", dependencies=[Depends(require_permission("indicator_data:view"))])
async def export_metrics_v2(
    indicator_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    district_ids: Optional[list[int]] = Query(None),
    district_name: Optional[str] = Query(None),
    circle_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    major_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    order_by: str = Query("stat_date"),
    desc: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    page = 1
    size = 2000
    all_rows: list[IndicatorData] = []
    while True:
        rows, total = await query_metrics(
            session=session,
            indicator_id=indicator_id,
            district_id=district_id,
            district_ids=district_ids,
            district_name=district_name,
            circle_id=circle_id,
            start_date=start_date,
            end_date=end_date,
            major_id=major_id,
            type_id=type_id,
            page=page,
            size=size,
            order_by=order_by,
            desc_order=desc,
        )
        all_rows.extend(rows)
        if page * size >= total or not rows:
            break
        page += 1
    if not all_rows:
        xlsx = await run_pandas(build_district_pivot_xlsx, [])
        buf = io.BytesIO(xlsx)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=metrics_export.xlsx"})
    districts = (await session.execute(select(District))).scalars().all()
    dist_map = {d.district_id: (d.circle_id or 0, d.district_name) for d in districts}
    ind_ids = list({getattr(r, "indicator_id") for r in all_rows})
    inds = (await session.execute(select(Indicator).where(Indicator.indicator_id.in_(ind_ids)))).scalars().all()
    pos_map = {i.indicator_id: i.is_positive for i in inds}
    name_map = {i.indicator_id: i.indicator_name for i in inds}
    pivot_rows = []
    for r in all_rows:
        iid = getattr(r, "indicator_id")
        did = getattr(r, "district_id")
        circle_id, dname = dist_map.get(did, (0, getattr(r, "district_name")))
        pivot_rows.append(
            {
                "district_id": did,
                "district_name": dname,
                "circle_id": circle_id,
                "indicator_id": iid,
                "indicator_name": name_map.get(iid, getattr(r, "indicator_name")),
                "is_positive": pos_map.get(iid, 1),
                "stat_date": getattr(r, "stat_date"),
                "value": getattr(r, "value"),
                "score": getattr(r, "score", None),
            }
        )
    xlsx = await run_pandas(build_district_pivot_xlsx, pivot_rows)
    buf = io.BytesIO(xlsx)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=metrics_export.xlsx"})

@router.get(
    "/district",
    response_model=DistrictMetricsResponse
)
async def query_district_indicators(
    district_id: int | None = None,
    district_name: str | None = None,
    date: str | None = None,
    session: AsyncSession = Depends(get_session)
):
    """
    查询某个区县在某一天的所有指标数据
    """
    data = await get_indicators_by_district(
        district_id=district_id,
        district_name=district_name,
        stat_date=date,
        session=session
    )

    if not data:
        raise HTTPException(status_code=404, detail="No indicator data found")

    return data

@router.get("/by_name_or_id", response_model=list[IndicatorLatestQueryOut])
async def get_indicators_by_name_or_id(
    indicator_id: int | None = None,
    indicator_name: str | None = None,
    stat_date: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    通过指标ID或指标名称查询所有区县最新数据（不分页）
    适用于机器人推送
    """
    results = await get_latest_indicator_data(
        session=session,
        indicator_id=indicator_id,
        indicator_name=indicator_name,
        stat_date=stat_date
    )
    return results

# -------- Indicator management (CRUD) --------
@router.get("/indicators", response_model=PageResponse[IndicatorOut], dependencies=[Depends(require_permission("indicator:view"))])
async def indicators_all(
    q: Optional[str] = Query(None),
    type_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_session)
):
    from services.indicator_service import list_indicators
    items, total = await list_indicators(session, q=q, type_id=type_id, page=page, size=size)
    return PageResponse(data=items, total=total, page=page, size=size)

@router.post("/indicators", response_model=IndicatorOut, status_code=201, dependencies=[Depends(require_permission("indicator:add"))])
async def indicators_create(payload: IndicatorBase, session: AsyncSession = Depends(get_session)):
    from services.indicator_service import create_indicator
    return await create_indicator(session, payload)

@router.put("/indicators/{indicator_id}", response_model=IndicatorOut, dependencies=[Depends(require_permission("indicator:edit"))])
async def indicators_update(indicator_id: int, payload: IndicatorBase, session: AsyncSession = Depends(get_session)):
    from services.indicator_service import update_indicator
    return await update_indicator(session, indicator_id, payload)

@router.delete("/indicators/{indicator_id}", dependencies=[Depends(require_permission("indicator:delete"))])
async def indicators_delete(indicator_id: int, session: AsyncSession = Depends(get_session)):
    from services.indicator_service import delete_indicator
    return await delete_indicator(session, indicator_id)

# -------- Indicator bulk upload --------
@router.get("/indicators/upload/template", dependencies=[Depends(require_permission("indicator:add"))])
async def indicators_upload_template(session: AsyncSession = Depends(get_session)):
    columns = [
        "指标名称",
        "单位",
        "专业中文名",
        "类型中文名",
        "是否正向",
        "状态",
        "版本",
        "说明",
    ]
    desc_row = {
        "指标名称": "必填",
        "单位": "选填",
        "专业中文名": "必填，或提供 major_id 列",
        "类型中文名": "必填，或提供 type_id 列",
        "是否正向": "必填：1为正向，0为负向，2为其他",
        "状态": "选填，默认1：启用；0：停用",
        "版本": "选填，默认1",
        "说明": "选填",
    }
    sample_row = {
        "指标名称": "示例指标A",
        "单位": "%",
        "专业中文名": "无线",
        "类型中文名": "运营考核",
        "是否正向": 1,
        "状态": 1,
        "版本": 1,
        "说明": "示例说明",
    }
    xlsx = await run_pandas(build_template_xlsx, columns, desc_row, sample_row, "模板")
    buf = io.BytesIO(xlsx)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=indicator_manage_template.xlsx"})

@router.post("/indicators/upload", status_code=201, dependencies=[Depends(require_permission("indicator:add"))])
async def indicators_upload(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    contents = await file.read()
    try:
        records, _row_count = await run_pandas(parse_indicator_manage_upload_records, contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    majors = (await session.execute(select(Major))).scalars().all()
    types = (await session.execute(select(EvaluationType))).scalars().all()
    major_name_map = {m.major_name: m.major_id for m in majors}
    type_name_map = {t.type_name: t.type_id for t in types}

    from models.metrics import Indicator

    errors = []
    created = 0
    updated = 0
    for idx, row in enumerate(records):
        name = str(row.get("indicator_name") or "").strip()
        if not name:
            errors.append(f"Row {idx+1}: indicator_name is required")
            continue
        unit = str(row.get("unit") or "").strip() or None
        is_positive = row.get("is_positive")
        status = row.get("status")
        version = row.get("version") if row.get("version") is not None else 1
        desc = str(row.get("description") or "").strip() or None

        # resolve major_id/type_id from name or explicit id
        maj_id = None
        typ_id = None
        if row.get("major_id") is not None:
            try:
                maj_id = int(row.get("major_id"))
            except Exception:
                errors.append(f"Row {idx+1}: invalid major_id")
                continue
        elif row.get("major_name") is not None:
            maj_id = major_name_map.get(str(row.get("major_name")).strip())
        if row.get("type_id") is not None:
            try:
                typ_id = int(row.get("type_id"))
            except Exception:
                errors.append(f"Row {idx+1}: invalid type_id")
                continue
        elif row.get("type_name") is not None:
            typ_id = type_name_map.get(str(row.get("type_name")).strip())

        if maj_id is None:
            errors.append(f"Row {idx+1}: major not resolved")
            continue
        if typ_id is None:
            errors.append(f"Row {idx+1}: type not resolved")
            continue
        if is_positive is None:
            errors.append(f"Row {idx+1}: is_positive required")
            continue
        if status is None:
            status = 1

        # upsert by indicator_name + major_id + type_id
        existing = (await session.execute(
            select(Indicator).where(
                Indicator.indicator_name == name,
                Indicator.major_id == maj_id,
                Indicator.type_id == typ_id
            )
        )).scalar_one_or_none()

        if existing:
            existing.unit = unit
            existing.is_positive = int(is_positive)
            existing.status = int(status)
            existing.version = int(version)
            existing.description = desc
            updated += 1
        else:
            obj = Indicator(
                indicator_name=name,
                unit=unit,
                major_id=maj_id,
                type_id=typ_id,
                is_positive=int(is_positive),
                status=int(status),
                version=int(version),
                description=desc,
            )
            session.add(obj)
            created += 1

    if errors:
        await session.rollback()
        raise HTTPException(status_code=400, detail={"message": "Validation failed", "errors": errors[:10]})
    await session.commit()
    return {"created": created, "updated": updated}

@router.get("/by_majors", response_model=MajorMetricsResponse)
async def get_indicators_by_major(
    major_id: int | None = None,
    major_name: str | None = None,
    district_id: Optional[int] = Query(None),
    districts_name: str | None = None,
    stat_date: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    通过专业ID或专业名称查询所有区县数据（不分页）
    """
    results = await get_metrics_by_major(
        session=session,
        major_id=major_id,
        major_name=major_name,
        district_id=district_id,
        districts_name=districts_name,
        stat_date=stat_date
    )
    return results

@router.get("/by-type", response_model=TypeMetricsResponse)
async def get_metrics_by_type_api(
    type_id: int | None = None,
    type_name: str | None = None,
    district_id: int | None = None,
    districts_name: str | None = None,
    stat_date: str | None = None,
    session: AsyncSession = Depends(get_session)
):
    results = await get_metrics_by_type(
        session=session,
        type_id=type_id,
        type_name=type_name,
        district_id=district_id,
        districts_name=districts_name,
        stat_date=stat_date
    )
    return results
