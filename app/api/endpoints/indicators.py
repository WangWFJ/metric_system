# =============================
# app/api/endpoints/indicators.py
# =============================
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import pandas as pd
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
    import pandas as pd
    import io
    # 使用中文表头
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
    df = pd.DataFrame([desc_row, sample_row], columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="模板")
    buf.seek(0)
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
        df = pd.read_excel(io.BytesIO(contents))
        # 支持中文表头，进行列名映射
        rename_map = {
            '指标名称': 'indicator_name',
            '区县': 'district_name',
            '统计日期': 'stat_date',
            '完成值': 'value',
            '基准值': 'benchmark',
            '挑战值': 'challenge',
            '豁免值': 'exemption',
            '零容忍值': 'zero_tolerance',
            '得分': 'score',
            '类型ID': 'type_id',
            '类型名称': 'type_name',
        }
        df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
        # Check required columns (英文键）
        required_cols = ['indicator_name', 'district_name', 'stat_date', 'value']
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

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
        
        for index, row in df.iterrows():
            ind_name = row['indicator_name']
            dist_name = row['district_name']
            
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
            if 'type_id' in df.columns and pd.notna(row.get('type_id')):
                try:
                    provided_type_id = int(row.get('type_id'))
                except Exception:
                    errors.append(f"Row {index+1}: Invalid type_id value")
                    continue
            elif 'type_name' in df.columns and pd.notna(row.get('type_name')):
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
            existing_stmt = select(IndicatorData).where(
                IndicatorData.indicator_id == ind.indicator_id,
                IndicatorData.district_id == dist.district_id,
                IndicatorData.stat_date == pd.to_datetime(row['stat_date']).date()
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing.value = row['value'] if pd.notna(row['value']) else None
                existing.benchmark = row['benchmark'] if 'benchmark' in df.columns and pd.notna(row['benchmark']) else None
                existing.challenge = row['challenge'] if 'challenge' in df.columns and pd.notna(row['challenge']) else None
                existing.exemption = row['exemption'] if 'exemption' in df.columns and pd.notna(row['exemption']) else existing.exemption
                existing.zero_tolerance = row['zero_tolerance'] if 'zero_tolerance' in df.columns and pd.notna(row['zero_tolerance']) else existing.zero_tolerance
                existing.score = row['score'] if 'score' in df.columns and pd.notna(row['score']) else existing.score
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
                    stat_date=pd.to_datetime(row['stat_date']).date(),
                    value=row['value'] if pd.notna(row['value']) else None,
                    benchmark=row['benchmark'] if 'benchmark' in df.columns and pd.notna(row['benchmark']) else None,
                    challenge=row['challenge'] if 'challenge' in df.columns and pd.notna(row['challenge']) else None,
                    exemption=row['exemption'] if 'exemption' in df.columns and pd.notna(row['exemption']) else None,
                    zero_tolerance=row['zero_tolerance'] if 'zero_tolerance' in df.columns and pd.notna(row['zero_tolerance']) else None,
                    score=row['score'] if 'score' in df.columns and pd.notna(row['score']) else None,
                    # ... other fields
                )
                session.add(data_obj)
            
        if errors:
            await session.rollback()
            raise HTTPException(status_code=400, detail={"message": "Data validation failed", "errors": errors[:10]}) # Return first 10 errors
            
        await session.commit()
        return {"message": "Data uploaded successfully", "count": len(df)}
        
    except Exception as e:
        await session.rollback()
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
    df = pd.DataFrame([desc_row, sample_row], columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="模板")
    buf.seek(0)
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
        df = pd.read_excel(io.BytesIO(contents))
        rename_map = {
            "指标名称": "indicator_name",
            "支撑中心": "center_name",
            "统计日期": "stat_date",
            "完成值": "value",
            "基准值": "benchmark",
            "挑战值": "challenge",
            "得分": "score",
            "类型ID": "type_id",
            "类型名称": "type_name",
        }
        df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
        required_cols = ["indicator_name", "center_name", "stat_date", "value"]
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

        indicators = (await session.execute(select(Indicator))).scalars().all()
        ind_map = {i.indicator_name: i for i in indicators}
        centers = (await session.execute(select(Center))).scalars().all()
        center_map = {c.center_name: c for c in centers}
        eval_types = (await session.execute(select(EvaluationType))).scalars().all()
        type_name_map = {t.type_name: t.type_id for t in eval_types}

        errors = []
        for index, row in df.iterrows():
            ind_name = row["indicator_name"]
            center_name = row["center_name"]
            if ind_name not in ind_map:
                errors.append(f"Row {index+1}: Indicator '{ind_name}' not found")
                continue
            center = center_map.get(center_name)
            if not center:
                errors.append(f"Row {index+1}: Center '{center_name}' not found")
                continue

            ind = ind_map[ind_name]
            provided_type_id = None
            if "type_id" in df.columns and pd.notna(row.get("type_id")):
                try:
                    provided_type_id = int(row.get("type_id"))
                except Exception:
                    errors.append(f"Row {index+1}: Invalid type_id value")
                    continue
            elif "type_name" in df.columns and pd.notna(row.get("type_name")):
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

            stat_date = pd.to_datetime(row["stat_date"]).date()
            existing_stmt = select(IndicatorCenterData).where(
                IndicatorCenterData.indicator_id == ind.indicator_id,
                IndicatorCenterData.center_id == center.center_id,
                IndicatorCenterData.stat_date == stat_date,
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()

            if existing:
                existing.value = row["value"] if pd.notna(row.get("value")) else None
                existing.benchmark = row["benchmark"] if "benchmark" in df.columns and pd.notna(row.get("benchmark")) else None
                existing.challenge = row["challenge"] if "challenge" in df.columns and pd.notna(row.get("challenge")) else None
                existing.score = row["score"] if "score" in df.columns and pd.notna(row.get("score")) else existing.score
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
                    value=row["value"] if pd.notna(row.get("value")) else None,
                    benchmark=row["benchmark"] if "benchmark" in df.columns and pd.notna(row.get("benchmark")) else None,
                    challenge=row["challenge"] if "challenge" in df.columns and pd.notna(row.get("challenge")) else None,
                    score=row["score"] if "score" in df.columns and pd.notna(row.get("score")) else None,
                )
                session.add(data_obj)

        if errors:
            await session.rollback()
            raise HTTPException(status_code=400, detail={"message": "Data validation failed", "errors": errors[:10]})

        await session.commit()
        return {"message": "Data uploaded successfully", "count": len(df)}
    except Exception as e:
        await session.rollback()
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
    df = pd.DataFrame(all_items)
    df = df.rename(columns={
        "indicator_name": "指标名称",
        "district_name": "区县",
        "stat_date": "统计日期",
        "value": "完成值",
        "score": "得分",
        "benchmark": "基准值",
        "challenge": "挑战值",
        "exemption": "豁免值",
        "zero_tolerance": "零容忍值",
    })
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="导出")
    buf.seek(0)
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
    df = pd.DataFrame(all_items)
    df = df.rename(
        columns={
            "indicator_name": "指标名称",
            "district_name": "区县",
            "center_name": "支撑中心",
            "stat_date": "统计日期",
            "value": "完成值",
            "benchmark": "基准值",
            "challenge": "挑战值",
            "score": "得分",
        }
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="导出")
    buf.seek(0)
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
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"提示": ["无数据"]}).to_excel(writer, index=False, sheet_name="空")
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=center_metrics_export.xlsx"},
        )

    pos_map: dict[int, int] = {}
    name_map: dict[int, str] = {}
    ordered_ind_ids: list[int] = []
    seen = set()
    for r in all_rows:
        iid = getattr(r, "indicator_id")
        if iid not in seen:
            ordered_ind_ids.append(iid)
            seen.add(iid)
        name_map[iid] = getattr(r, "indicator_name", f"指标{iid}")
        pos_map[iid] = getattr(r, "is_positive", 1)

    from collections import defaultdict
    group_by_date = defaultdict(list)
    for r in all_rows:
        group_by_date[str(getattr(r, "stat_date"))].append(r)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for stat_date, rows in sorted(group_by_date.items()):
            agg = defaultdict(dict)  # center_id -> indicator_id -> {value,score}
            extra_cols = {}  # center_id -> (district_name, center_name)
            for r in rows:
                cid = getattr(r, "center_id")
                iid = getattr(r, "indicator_id")
                val = getattr(r, "value")
                sc = getattr(r, "score", None)
                agg[cid][iid] = {
                    "value": float(val) if val is not None else None,
                    "score": float(sc) if sc is not None else None,
                }
                extra_cols[cid] = (getattr(r, "district_name", ""), getattr(r, "center_name", ""))

            data = []
            for cid, vals in agg.items():
                dname, cname = extra_cols.get(cid, ("", ""))
                row = {"中心ID": cid, "区县": dname, "支撑中心": cname}
                for iid in ordered_ind_ids:
                    col_name = name_map.get(iid, f"指标{iid}")
                    v = vals.get(iid) or {}
                    row[col_name] = v.get("value")
                    row[f"{col_name}-得分"] = v.get("score")
                data.append(row)

            df = pd.DataFrame(data)
            df = df.sort_values(by=["中心ID"]).reset_index(drop=True)
            if "中心ID" in df.columns:
                df = df.drop(columns=["中心ID"])

            if not df.empty:
                total_row = {"区县": "", "支撑中心": "成都总计"}
                best_row = {"区县": "", "支撑中心": "全市最优值"}
                for iid in ordered_ind_ids:
                    col_v = name_map.get(iid, f"指标{iid}")
                    col_s = f"{col_v}-得分"
                    series_v = pd.to_numeric(df[col_v], errors="coerce")
                    series_s = pd.to_numeric(df[col_s], errors="coerce")
                    total_row[col_v] = float(series_v.mean(skipna=True)) if series_v.size else None
                    total_row[col_s] = float(series_s.mean(skipna=True)) if series_s.size else None
                    if pos_map.get(iid, 1) == 1:
                        best_row[col_v] = float(series_v.max(skipna=True)) if series_v.size else None
                    else:
                        best_row[col_v] = float(series_v.min(skipna=True)) if series_v.size else None
                    best_row[col_s] = float(series_s.max(skipna=True)) if series_s.size else None
                df = pd.concat([df, pd.DataFrame([total_row, best_row])], ignore_index=True)

            df.to_excel(writer, index=False, sheet_name=str(stat_date))
            ws = writer.sheets[str(stat_date)]
            from openpyxl.styles import Font
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold

    buf.seek(0)
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
    import pandas as pd
    import io
    # 1) 拉取所有满足条件的数据
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
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame({"提示": ["无数据"]}).to_excel(writer, index=False, sheet_name="空")
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=metrics_export.xlsx"})
    # 2) 辅助映射：区县圈层、指标正向性
    districts = (await session.execute(select(District))).scalars().all()
    dist_map = {d.district_id: (d.circle_id or 0, d.district_name) for d in districts}
    # 指标正向性
    ind_ids = list({getattr(r, "indicator_id") for r in all_rows})
    inds = (await session.execute(select(Indicator).where(Indicator.indicator_id.in_(ind_ids)))).scalars().all()
    pos_map = {i.indicator_id: i.is_positive for i in inds}
    name_map = {i.indicator_id: i.indicator_name for i in inds}
    # 列顺序：按出现顺序
    ordered_ind_ids: list[int] = []
    seen = set()
    for r in all_rows:
        iid = getattr(r, "indicator_id")
        if iid not in seen:
            ordered_ind_ids.append(iid)
            seen.add(iid)
    # 3) 分统计时间构建Sheet
    from collections import defaultdict
    group_by_date: dict[str, list[IndicatorData]] = defaultdict(list)
    for r in all_rows:
        dt = str(getattr(r, "stat_date"))
        group_by_date[dt].append(r)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for stat_date, rows in sorted(group_by_date.items()):
            # 行：区县；列：各指标
            # 先聚合为 {district_id: {indicator_id: value}}
            agg: dict[int, dict[int, dict[str, float | None]]] = defaultdict(dict)
            extra_cols: dict[int, tuple[int, str]] = {}  # district_id -> (circle_id, district_name)
            for r in rows:
                did = getattr(r, "district_id")
                iid = getattr(r, "indicator_id")
                val = getattr(r, "value")
                sc = getattr(r, "score", None)
                agg[did][iid] = {
                    "value": float(val) if val is not None else None,
                    "score": float(sc) if sc is not None else None,
                }
                extra_cols[did] = (dist_map.get(did, (0, getattr(r, "district_name")))[0], dist_map.get(did, (0, getattr(r, "district_name")))[1])
            # 构建DataFrame
            data = []
            for did, vals in agg.items():
                circle_id, dname = extra_cols.get(did, (0, ""))
                row = {"区县ID": did, "圈层": circle_id, "区县": dname}
                for iid in ordered_ind_ids:
                    col_name = name_map.get(iid, f"指标{iid}")
                    v = vals.get(iid) or {}
                    row[col_name] = v.get("value")
                    row[f"{col_name}-得分"] = v.get("score")
                data.append(row)
            # 按圈层、区县排序
            df = pd.DataFrame(data)
            # 改为按数据库区县ID顺序排列
            df = df.sort_values(by=["区县ID"]).reset_index(drop=True)
            # 导出时不显示内部排序字段
            if "区县ID" in df.columns:
                df = df.drop(columns=["区县ID"]) 
            # 汇总行：总计（均值）与最优值
            if not df.empty:
                total_row = {"圈层": "", "区县": "成都总计"}
                best_row = {"圈层": "", "区县": "全市最优值"}
                for iid in ordered_ind_ids:
                    col_v = name_map.get(iid, f"指标{iid}")
                    col_s = f"{col_v}-得分"
                    series_v = pd.to_numeric(df[col_v], errors="coerce")
                    series_s = pd.to_numeric(df[col_s], errors="coerce")
                    total_row[col_v] = float(series_v.mean(skipna=True)) if series_v.size else None
                    total_row[col_s] = float(series_s.mean(skipna=True)) if series_s.size else None
                    if pos_map.get(iid, 1) == 1:
                        best_row[col_v] = float(series_v.max(skipna=True)) if series_v.size else None
                    else:
                        best_row[col_v] = float(series_v.min(skipna=True)) if series_v.size else None
                    # 得分最优默认取最大
                    best_row[col_s] = float(series_s.max(skipna=True)) if series_s.size else None
                df = pd.concat([df, pd.DataFrame([total_row, best_row])], ignore_index=True)
            # 写Sheet
            df.to_excel(writer, index=False, sheet_name=str(stat_date))
            # 简样式：加粗表头
            ws = writer.sheets[str(stat_date)]
            from openpyxl.styles import Font
            bold = Font(bold=True)
            for cell in ws[1]:
                cell.font = bold
    buf.seek(0)
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
    import pandas as pd
    import io
    # 使用中文表头
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
    df = pd.DataFrame([desc_row, sample_row], columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="模板")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=indicator_manage_template.xlsx"})

@router.post("/indicators/upload", status_code=201, dependencies=[Depends(require_permission("indicator:add"))])
async def indicators_upload(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    import pandas as pd
    import io
    from sqlalchemy import select
    if not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    # 支持中文表头，进行列名映射
    rename_map = {
        "指标名称": "indicator_name",
        "单位": "unit",
        "专业中文名": "major_name",
        "类型中文名": "type_name",
        "是否正向": "is_positive",
        "状态": "status",
        "版本": "version",
        "说明": "description",
        "专业ID": "major_id",
        "类型ID": "type_id",
    }
    df.rename(columns={c: rename_map.get(str(c).strip(), c) for c in df.columns}, inplace=True)
    required = ["indicator_name"]
    for col in required:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
    majors = (await session.execute(select(Major))).scalars().all()
    types = (await session.execute(select(EvaluationType))).scalars().all()
    major_name_map = {m.major_name: m.major_id for m in majors}
    type_name_map = {t.type_name: t.type_id for t in types}

    from models.metrics import Indicator

    errors = []
    created = 0
    updated = 0
    for idx, row in df.iterrows():
        name = str(row.get("indicator_name") or "").strip()
        if not name:
            errors.append(f"Row {idx+1}: indicator_name is required")
            continue
        unit = str(row.get("unit") or "").strip() or None
        is_positive = row.get("is_positive")
        status = row.get("status")
        version = row.get("version") if pd.notna(row.get("version")) else 1
        desc = str(row.get("description") or "").strip() or None

        # resolve major_id/type_id from name or explicit id
        maj_id = None
        typ_id = None
        if "major_id" in df.columns and pd.notna(row.get("major_id")):
            try:
                maj_id = int(row.get("major_id"))
            except Exception:
                errors.append(f"Row {idx+1}: invalid major_id")
                continue
        elif "major_name" in df.columns and pd.notna(row.get("major_name")):
            maj_id = major_name_map.get(str(row.get("major_name")).strip())
        if "type_id" in df.columns and pd.notna(row.get("type_id")):
            try:
                typ_id = int(row.get("type_id"))
            except Exception:
                errors.append(f"Row {idx+1}: invalid type_id")
                continue
        elif "type_name" in df.columns and pd.notna(row.get("type_name")):
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
