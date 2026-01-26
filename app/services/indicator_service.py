# =============================
# app/services/indicator_service.py
# =============================
from sqlalchemy import select, func, desc, asc, and_, update
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple
from fastapi import HTTPException
from datetime import date

from models.metrics import IndicatorDataV2 as IndicatorData, Indicator, Major, KPIType, District, EvaluationType, Center, IndicatorCenterData
from models.metrics_schemas import (
    IndicatorDataOut,
    MajorMetricsResponse,
    IndicatorWithDistricts,
    DistrictValue,
    TypeMetricsResponse,
    IndicatorOut,
    IndicatorBase,
    IndicatorCenterDataOut,
    CenterMetricsResponse,
)


async def query_metrics(
    session: AsyncSession,
    indicator_id: Optional[int] = None,
    district_id: Optional[int] = None,
    district_ids: Optional[List[int]] = None,
    district_name: Optional[str] = None,
    circle_id: Optional[int] = None,
    start_date = None,
    end_date = None,
    page: int = 1,
    size: int = 50,
    order_by: str = "stat_date",
    desc_order: bool = True,
    major_id: Optional[int] = None,
    type_id: Optional[int] = None,
) -> Tuple[List[IndicatorDataOut], int]:
    stmt = select(IndicatorData).join(Indicator, Indicator.indicator_id == IndicatorData.indicator_id)

    filters = [Indicator.status == 1]

    if indicator_id is not None:
        filters.append(IndicatorData.indicator_id == indicator_id)
    if district_ids:
        filters.append(IndicatorData.district_id.in_(district_ids))
    elif district_id is not None:
        filters.append(IndicatorData.district_id == district_id)
    if district_name is not None:
        filters.append(IndicatorData.district_name == district_name)
    if circle_id is not None:
        filters.append(IndicatorData.circle_id == circle_id)
    if start_date is not None:
        filters.append(IndicatorData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorData.stat_date <= end_date)
    if major_id is not None:
        filters.append(Indicator.major_id == major_id)
    if type_id is not None:
        filters.append(Indicator.type_id == type_id)

    if filters:
        stmt = stmt.where(and_(*filters))

    count_subq = stmt.order_by(None).limit(None).offset(None).subquery()
    total = (await session.execute(select(func.count()).select_from(count_subq))).scalar_one()

    order_col = getattr(IndicatorData, order_by, IndicatorData.stat_date)
    stmt = stmt.order_by(desc(order_col) if desc_order else asc(order_col))

    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await session.execute(stmt)
    rows = result.scalars().all()
    return ([IndicatorDataOut.model_validate(r) for r in rows], total)

async def query_series(
    session: AsyncSession,
    indicator_id: int,
    district_id: Optional[int] = None,
    start_date = None,
    end_date = None,
    size: int = 180,
) -> Tuple[List[IndicatorDataOut], int]:
    if not indicator_id:
        raise HTTPException(400, "indicator_id is required")
    stmt = select(IndicatorData).join(Indicator, Indicator.indicator_id == IndicatorData.indicator_id)
    filters = [Indicator.status == 1, IndicatorData.indicator_id == indicator_id]
    if district_id is not None:
        filters.append(IndicatorData.district_id == district_id)
    if start_date is not None:
        filters.append(IndicatorData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorData.stat_date <= end_date)
    stmt = stmt.where(and_(*filters))
    count_subq = stmt.order_by(None).limit(None).offset(None).subquery()
    total = (await session.execute(select(func.count()).select_from(count_subq))).scalar_one()
    stmt = stmt.order_by(asc(IndicatorData.stat_date)).limit(size)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return ([IndicatorDataOut.model_validate(r) for r in rows], total)

async def get_all_centers(session: AsyncSession, district_id: Optional[int] = None):
    stmt = select(Center)
    if district_id is not None:
        stmt = stmt.where(Center.district_id == district_id)
    stmt = stmt.order_by(asc(Center.center_id))
    result = await session.execute(stmt)
    return result.scalars().all()

async def query_center_metrics(
    session: AsyncSession,
    indicator_id: Optional[int] = None,
    center_id: Optional[int] = None,
    district_id: Optional[int] = None,
    start_date=None,
    end_date=None,
    page: int = 1,
    size: int = 50,
    order_by: str = "stat_date",
    desc_order: bool = True,
    major_id: Optional[int] = None,
    type_id: Optional[int] = None,
) -> Tuple[List[IndicatorCenterDataOut], int]:
    stmt = (
        select(IndicatorCenterData, Center, District)
        .join(Center, Center.center_id == IndicatorCenterData.center_id)
        .outerjoin(District, District.district_id == Center.district_id)
        .join(Indicator, Indicator.indicator_id == IndicatorCenterData.indicator_id)
    )

    filters = [Indicator.status == 1]
    if indicator_id is not None:
        filters.append(IndicatorCenterData.indicator_id == indicator_id)
    if center_id is not None:
        filters.append(IndicatorCenterData.center_id == center_id)
    if district_id is not None:
        filters.append(Center.district_id == district_id)
    if start_date is not None:
        filters.append(IndicatorCenterData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorCenterData.stat_date <= end_date)
    if major_id is not None:
        filters.append(Indicator.major_id == major_id)
    if type_id is not None:
        filters.append(Indicator.type_id == type_id)

    if filters:
        stmt = stmt.where(and_(*filters))

    count_subq = stmt.order_by(None).limit(None).offset(None).subquery()
    total = (await session.execute(select(func.count()).select_from(count_subq))).scalar_one()

    order_map = {
        "stat_date": IndicatorCenterData.stat_date,
        "value": IndicatorCenterData.value,
        "benchmark": IndicatorCenterData.benchmark,
        "challenge": IndicatorCenterData.challenge,
        "score": IndicatorCenterData.score,
        "center_id": IndicatorCenterData.center_id,
        "indicator_id": IndicatorCenterData.indicator_id,
        "district_id": Center.district_id,
    }
    order_col = order_map.get(order_by, IndicatorCenterData.stat_date)
    stmt = stmt.order_by(desc(order_col) if desc_order else asc(order_col))
    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await session.execute(stmt)
    rows = result.all()
    out: List[IndicatorCenterDataOut] = []
    for data_obj, center_obj, district_obj in rows:
        out.append(
            IndicatorCenterDataOut.model_validate(
                {
                    "id": data_obj.id,
                    "indicator_id": data_obj.indicator_id,
                    "indicator_name": data_obj.indicator_name,
                    "type_id": data_obj.type_id,
                    "major_id": data_obj.major_id,
                    "is_positive": data_obj.is_positive,
                    "center_id": data_obj.center_id,
                    "center_name": data_obj.center_name,
                    "district_id": getattr(center_obj, "district_id", None),
                    "district_name": getattr(district_obj, "district_name", None) if district_obj else None,
                    "stat_date": data_obj.stat_date,
                    "value": data_obj.value,
                    "benchmark": data_obj.benchmark,
                    "challenge": data_obj.challenge,
                    "exemption": data_obj.exemption,
                    "zero_tolerance": data_obj.zero_tolerance,
                    "score": data_obj.score,
                }
            )
        )
    return (out, total)

async def get_indicators_by_center(
    session: AsyncSession,
    center_id: int | None,
    center_name: str | None,
    stat_date: str | None,
) -> CenterMetricsResponse:
    center_query = select(Center)
    if center_id:
        center_query = center_query.where(Center.center_id == center_id)
    elif center_name:
        center_query = center_query.where(Center.center_name == center_name)
    else:
        raise HTTPException(400, "center_id or center_name must be provided")
    center = (await session.execute(center_query)).scalar_one_or_none()
    if not center:
        raise HTTPException(404, "Center not found")

    if stat_date:
        final_date = stat_date
    else:
        latest_q = await session.execute(
            select(func.max(IndicatorCenterData.stat_date)).where(IndicatorCenterData.center_id == center.center_id)
        )
        final_date = latest_q.scalar()
    if not final_date:
        raise HTTPException(404, "No data available for this center")

    dist_name = None
    if center.district_id is not None:
        dist_name = (
            await session.execute(select(District.district_name).where(District.district_id == center.district_id))
        ).scalar_one_or_none()

    data_q = await session.execute(
        select(IndicatorCenterData)
        .where(IndicatorCenterData.center_id == center.center_id, IndicatorCenterData.stat_date == final_date)
        .order_by(IndicatorCenterData.indicator_name)
    )
    data_list = data_q.scalars().all()

    return {
        "center_id": center.center_id,
        "center_name": center.center_name,
        "district_id": center.district_id,
        "district_name": dist_name,
        "stat_date": str(final_date),
        "indicators": [
            {
                "indicator_name": d.indicator_name,
                "value": d.value,
                "benchmark": d.benchmark,
                "challenge": d.challenge,
                "score": d.score,
            }
            for d in data_list
        ],
    }

async def get_latest_center_indicator_data(
    session: AsyncSession,
    indicator_id: int | None = None,
    indicator_name: str | None = None,
    stat_date: str | None = None,
    district_id: int | None = None,
):
    if indicator_name and not indicator_id:
        q = await session.execute(select(Indicator.indicator_id).where(Indicator.indicator_name == indicator_name))
        row = q.first()
        if not row:
            return []
        indicator_id = row[0]
    if not indicator_id:
        return []

    base_latest = select(func.max(IndicatorCenterData.stat_date)).where(IndicatorCenterData.indicator_id == indicator_id)
    if district_id is not None:
        base_latest = base_latest.select_from(IndicatorCenterData).join(Center, Center.center_id == IndicatorCenterData.center_id).where(
            Center.district_id == district_id
        )
    q_latest = await session.execute(base_latest)
    latest_date = q_latest.scalar()
    if stat_date:
        latest_date = stat_date
    if not latest_date:
        return []

    stmt = (
        select(IndicatorCenterData, Center, District)
        .join(Center, Center.center_id == IndicatorCenterData.center_id)
        .outerjoin(District, District.district_id == Center.district_id)
        .where(IndicatorCenterData.indicator_id == indicator_id, IndicatorCenterData.stat_date == latest_date)
    )
    if district_id is not None:
        stmt = stmt.where(Center.district_id == district_id)
    stmt = stmt.order_by(asc(Center.center_id))
    rows = (await session.execute(stmt)).all()
    out = []
    for d, c, dist in rows:
        out.append(
            {
                "indicator_id": d.indicator_id,
                "indicator_name": d.indicator_name,
                "center_id": c.center_id,
                "center_name": c.center_name,
                "district_id": getattr(c, "district_id", None),
                "district_name": getattr(dist, "district_name", None) if dist else None,
                "stat_date": d.stat_date,
                "value": d.value,
                "score": d.score,
            }
        )
    return out

async def query_center_series(
    session: AsyncSession,
    indicator_id: int,
    center_id: Optional[int] = None,
    start_date=None,
    end_date=None,
    size: int = 180,
) -> Tuple[List[IndicatorCenterDataOut], int]:
    if not indicator_id:
        raise HTTPException(400, "indicator_id is required")
    stmt = (
        select(IndicatorCenterData, Center, District)
        .join(Center, Center.center_id == IndicatorCenterData.center_id)
        .outerjoin(District, District.district_id == Center.district_id)
        .join(Indicator, Indicator.indicator_id == IndicatorCenterData.indicator_id)
    )
    filters = [Indicator.status == 1, IndicatorCenterData.indicator_id == indicator_id]
    if center_id is not None:
        filters.append(IndicatorCenterData.center_id == center_id)
    if start_date is not None:
        filters.append(IndicatorCenterData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorCenterData.stat_date <= end_date)
    stmt = stmt.where(and_(*filters))
    count_subq = stmt.order_by(None).limit(None).offset(None).subquery()
    total = (await session.execute(select(func.count()).select_from(count_subq))).scalar_one()
    stmt = stmt.order_by(asc(IndicatorCenterData.stat_date)).limit(size)
    result = await session.execute(stmt)
    rows = result.all()
    out: List[IndicatorCenterDataOut] = []
    for data_obj, center_obj, district_obj in rows:
        out.append(
            IndicatorCenterDataOut.model_validate(
                {
                    "id": data_obj.id,
                    "indicator_id": data_obj.indicator_id,
                    "indicator_name": data_obj.indicator_name,
                    "type_id": data_obj.type_id,
                    "major_id": data_obj.major_id,
                    "is_positive": data_obj.is_positive,
                    "center_id": data_obj.center_id,
                    "center_name": data_obj.center_name,
                    "district_id": getattr(center_obj, "district_id", None),
                    "district_name": getattr(district_obj, "district_name", None) if district_obj else None,
                    "stat_date": data_obj.stat_date,
                    "value": data_obj.value,
                    "benchmark": data_obj.benchmark,
                    "challenge": data_obj.challenge,
                    "exemption": data_obj.exemption,
                    "zero_tolerance": data_obj.zero_tolerance,
                    "score": data_obj.score,
                }
            )
        )
    return (out, total)


async def get_all_circles(session: AsyncSession) -> List[int]:
    stmt = select(District.circle_id).where(District.circle_id.is_not(None)).group_by(District.circle_id).order_by(District.circle_id)
    res = await session.execute(stmt)
    return [r[0] for r in res.all()]

async def update_indicator_data(session: AsyncSession, data) -> IndicatorDataOut:
    stmt = select(IndicatorData).where(
        IndicatorData.indicator_id == data.indicator_id,
        IndicatorData.district_id == data.district_id,
        IndicatorData.stat_date == data.stat_date
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Indicator data not found")
    existing.value = data.value
    existing.benchmark = data.benchmark
    existing.challenge = data.challenge
    existing.exemption = data.exemption
    existing.zero_tolerance = data.zero_tolerance
    if hasattr(data, "score"):
        existing.score = data.score
    await session.commit()
    await session.refresh(existing)
    return IndicatorDataOut.model_validate(existing)

async def delete_metrics(
    session: AsyncSession,
    ids: Optional[List[int]] = None,
    indicator_id: Optional[int] = None,
    district_id: Optional[int] = None,
    start_date = None,
    end_date = None,
):
    stmt = delete(IndicatorData)
    filters = []
    if ids:
        filters.append(IndicatorData.id.in_(ids))
    if indicator_id is not None:
        filters.append(IndicatorData.indicator_id == indicator_id)
    if district_id is not None:
        filters.append(IndicatorData.district_id == district_id)
    if start_date is not None:
        filters.append(IndicatorData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorData.stat_date <= end_date)
    if not filters:
        raise HTTPException(400, "delete requires ids or filters")
    stmt = stmt.where(and_(*filters))
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0

async def create_center_data(session: AsyncSession, data):
    ind = await session.get(Indicator, data.indicator_id)
    if not ind:
        raise HTTPException(404, "Indicator not found")
    center = await session.get(Center, data.center_id)
    if not center:
        raise HTTPException(404, "Center not found")

    if data.type_id is not None and ind.type_id is not None and data.type_id != ind.type_id:
        raise HTTPException(400, "Provided type_id does not match indicator's type")

    existing_stmt = select(IndicatorCenterData).where(
        IndicatorCenterData.indicator_id == ind.indicator_id,
        IndicatorCenterData.center_id == center.center_id,
        IndicatorCenterData.stat_date == data.stat_date,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()

    final_type_id = data.type_id or ind.type_id
    if existing:
        existing.value = data.value
        existing.benchmark = data.benchmark
        existing.challenge = data.challenge
        existing.score = data.score if hasattr(data, "score") else existing.score
        if existing.type_id is None:
            existing.type_id = final_type_id
        if existing.major_id is None:
            existing.major_id = ind.major_id
        data_obj = existing
    else:
        data_obj = IndicatorCenterData(
            indicator_id=ind.indicator_id,
            indicator_name=ind.indicator_name,
            type_id=final_type_id,
            major_id=ind.major_id,
            is_positive=ind.is_positive,
            center_id=center.center_id,
            center_name=center.center_name,
            stat_date=data.stat_date,
            value=data.value,
            benchmark=data.benchmark,
            challenge=data.challenge,
            score=(data.score if hasattr(data, "score") else None),
        )
        session.add(data_obj)
    await session.commit()
    await session.refresh(data_obj)
    return data_obj

async def update_center_data(session: AsyncSession, data) -> IndicatorCenterDataOut:
    stmt = select(IndicatorCenterData).where(
        IndicatorCenterData.indicator_id == data.indicator_id,
        IndicatorCenterData.center_id == data.center_id,
        IndicatorCenterData.stat_date == data.stat_date,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Indicator center data not found")
    existing.value = data.value
    existing.benchmark = data.benchmark
    existing.challenge = data.challenge
    if hasattr(data, "score"):
        existing.score = data.score
    await session.commit()
    await session.refresh(existing)
    return IndicatorCenterDataOut.model_validate(existing)

async def delete_center_metrics(
    session: AsyncSession,
    ids: Optional[List[int]] = None,
    indicator_id: Optional[int] = None,
    center_id: Optional[int] = None,
    start_date=None,
    end_date=None,
):
    stmt = delete(IndicatorCenterData)
    filters = []
    if ids:
        filters.append(IndicatorCenterData.id.in_(ids))
    if indicator_id is not None:
        filters.append(IndicatorCenterData.indicator_id == indicator_id)
    if center_id is not None:
        filters.append(IndicatorCenterData.center_id == center_id)
    if start_date is not None:
        filters.append(IndicatorCenterData.stat_date >= start_date)
    if end_date is not None:
        filters.append(IndicatorCenterData.stat_date <= end_date)
    if not filters:
        raise HTTPException(400, "delete requires ids or filters")
    stmt = stmt.where(and_(*filters))
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount or 0

async def search_indicators(
    session: AsyncSession,
    q: str,
    type_id: Optional[int] = None,
    size: int = 20,
):
    if not q or len(q.strip()) < 1:
        return []
    stmt = select(Indicator).where(Indicator.status == 1, Indicator.indicator_name.like(f"%{q.strip()}%"))
    if type_id is not None:
        stmt = stmt.where(Indicator.type_id == type_id)
    stmt = stmt.order_by(desc(Indicator.update_time), asc(Indicator.indicator_name)).limit(size)
    result = await session.execute(stmt)
    return result.scalars().all()
async def get_indicators_by_district(
    session: AsyncSession,
    district_id: int | None,
    district_name: str | None,
    stat_date: str | None
):
    """
    按区县查询指标数据（支持 id / 名称，支持最新日期）
    """

    # -----------------------------
    # 1. 查询区县
    # -----------------------------
    district_query = select(District)

    if district_id:
        district_query = district_query.where(District.district_id == district_id)
    elif district_name:
        district_query = district_query.where(
            (District.district_name == district_name) |
            (District.simple_name == district_name)
        )
    else:
        raise HTTPException(400, "district_id or district_name must be provided")

    district = (await session.execute(district_query)).scalar_one_or_none()
    if not district:
        raise HTTPException(404, "District not found")

    # -----------------------------
    # 2. 确定日期（最新 or 指定）
    # -----------------------------
    if stat_date:
        final_date = stat_date
    else:
        latest_q = await session.execute(
            select(func.max(IndicatorData.stat_date)).where(
                IndicatorData.district_id == district.district_id
            )
        )
        final_date = latest_q.scalar()

    if not final_date:
        raise HTTPException(404, "No data available for this district")

    # -----------------------------
    # 3. 查询该区县该日期下的指标数据
    # -----------------------------
    data_q = await session.execute(
        select(IndicatorData).where(
            IndicatorData.district_id == district.district_id,
            IndicatorData.stat_date == final_date
        ).order_by(IndicatorData.indicator_name)
    )
    data_list = data_q.scalars().all()

    # -----------------------------
    # 4. 组装返回（精简字段，机器人友好）
    # -----------------------------
    return {
        "district_id": district.district_id,
        "district_name": district.district_name,
        "stat_date": str(final_date),
        "indicators": [
            {
                "indicator_name": d.indicator_name,
                "value": d.value,
                "benchmark": d.benchmark,
                "challenge": d.challenge,
                "exemption": d.exemption,
                "zero_tolerance": d.zero_tolerance,
                "score": d.score,
            }
            for d in data_list
        ]
    }



async def get_latest_indicator_data(
    session: AsyncSession,
    indicator_id: int | None = None,
    indicator_name: str | None = None,
    stat_date: str | None = None,
):
    """
    查询某个指标的所有区县的指定日期或最新数据
    """

    # ① 若传入的是指标名称 → 换成指标ID
    if indicator_name and not indicator_id:
        q = await session.execute(
            select(Indicator.indicator_id).where(Indicator.indicator_name == indicator_name)
        )
        row = q.first()
        if not row:
            return []
        indicator_id = row[0]

    # 必须有 indicator_id
    if not indicator_id:
        return []

    # ② 查询该指标最新一天（按 stat_date）
    q_latest = await session.execute(
        select(func.max(IndicatorData.stat_date)).where(IndicatorData.indicator_id == indicator_id)
    )
    latest_date = q_latest.scalar()

    if stat_date:
        latest_date = stat_date

    if not latest_date:
        return []
    
    
    # ③ 查询该最新日期下所有区县的数据
    q_data = await session.execute(
        select(IndicatorData)
        .where(
            IndicatorData.indicator_id == indicator_id,
            IndicatorData.stat_date == latest_date
        )
        .order_by(IndicatorData.district_id)
    )

    return q_data.scalars().all()

async def latest_metrics(
    session: AsyncSession,
    indicator_id: Optional[int] = None,
    district_id: Optional[int] = None,
    district_name: Optional[str] = None,
    circle_id: Optional[int] = None,
    major_id: Optional[int] = None,
    type_id: Optional[int] = None,
    page: int = 1,
    size: int = 50,
    order_by: str = "stat_date",
    desc_order: bool = True,
) -> Tuple[List[IndicatorDataOut], int]:
    base = select(IndicatorData).join(Indicator, Indicator.indicator_id == IndicatorData.indicator_id)

    filters = [Indicator.status == 1]
    if indicator_id is not None:
        filters.append(IndicatorData.indicator_id == indicator_id)
    if district_id is not None:
        filters.append(IndicatorData.district_id == district_id)
    if district_name is not None:
        filters.append(IndicatorData.district_name == district_name)
    if circle_id is not None:
        filters.append(IndicatorData.circle_id == circle_id)
    if major_id is not None:
        filters.append(Indicator.major_id == major_id)
    if type_id is not None:
        filters.append(Indicator.type_id == type_id)

    if filters:
        base = base.where(and_(*filters))

    latest_subq = select(
        IndicatorData,
        func.row_number().over(
            partition_by=[IndicatorData.indicator_id, IndicatorData.district_id],
            order_by=desc(IndicatorData.stat_date)
        ).label("rn")
    ).select_from(base.order_by(None).limit(None).offset(None).subquery()).subquery()

    stmt = select(latest_subq).where(latest_subq.c.rn == 1)

    count_subq = stmt.subquery()
    total = (await session.execute(select(func.count()).select_from(count_subq))).scalar_one()

    order_col = latest_subq.c.stat_date if "stat_date" in latest_subq.c else latest_subq.c.indicator_id
    stmt = stmt.order_by(desc(order_col) if desc_order else asc(order_col))

    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await session.execute(stmt)
    rows = result.all()
    items: List[IndicatorDataOut] = []
    for r in rows:
        items.append(IndicatorDataOut.model_validate({
            "indicator_id": r.indicator_id,
            "indicator_name": r.indicator_name,
            "is_positive": r.is_positive,
            "circle_id": r.circle_id,
            "district_id": r.district_id,
            "district_name": r.district_name,
            "stat_date": r.stat_date,
            "value": r.value,
            "benchmark": r.benchmark,
            "challenge": r.challenge,
            "exemption": r.exemption,
            "zero_tolerance": r.zero_tolerance,
            "score": r.score,
            "id": r.id,
        }))
    return (items, total)


async def get_metrics_by_major(
    session: AsyncSession,
    major_id: int | None,
    major_name: str | None,
    district_id: int | None,
    districts_name: str | None,
    stat_date: str | None
):
    """
    按专业查询所有区县的指标数据
    """
    # -----------------------------
    # 1. 查询专业
    # -----------------------------
    query = select(Major)

    if major_id:
        query = query.where(Major.major_id == major_id)
    elif major_name:
        query = query.where(Major.major_name.like(f"%{major_name}%"))
    else:
        raise HTTPException(400, "major_id or major_name must be provided")

    major = (await session.execute(query)).scalar_one_or_none()
    if not major:
        raise HTTPException(404, "Major not found")

    # -----------------------------
    # 2. 查询该专业下的所有指标
    # -----------------------------
    # 去重：按 indicator_id 选择最新有效版本
    dedup_major_subq = (
        select(
            Indicator.indicator_id,
            Indicator.major_id,
            func.row_number().over(
                partition_by=[Indicator.indicator_id],
                order_by=[desc(Indicator.version), desc(Indicator.update_time)]
            ).label("rn"),
        )
        .where(Indicator.status == 1)
        .subquery()
    )

    result = await session.execute(
        select(Indicator)
        .join(dedup_major_subq, dedup_major_subq.c.indicator_id == Indicator.indicator_id)
        .where(dedup_major_subq.c.rn == 1, dedup_major_subq.c.major_id == major.major_id)
    )
    indicators = result.scalars().all()

    if not indicators:
        return MajorMetricsResponse(
            major_id=major.major_id,
            major_name=major.major_name,
            stat_date="",
            indicators=[]
        )

    indicator_ids = [i.indicator_id for i in indicators]

    # -----------------------------
    # 3. 确定日期（最新或指定）
    # -----------------------------
    if stat_date:
        final_date = stat_date
    else:
        # 查询 IndicatorData 中该专业最新的日期
        latest_q = await session.execute(
            select(func.max(IndicatorData.stat_date)).where(
                IndicatorData.indicator_id.in_(indicator_ids)
            )
        )
        final_date = latest_q.scalar()

    if not final_date:
        raise HTTPException(404, "No data available for this major")

    # -----------------------------
    # 4. 确定区县
    # -----------------------------
    district_query = select(District)

    # 如果按 district_id 查询
    if district_id:
        district_query = district_query.where(District.district_id == district_id)

    # 如果按名称查询
    if districts_name:
        district_query = district_query.where(
            (District.district_name == districts_name) |
            (District.simple_name == districts_name)
        )

    # 如果两个都没传，则查全部
    districts_q = await session.execute(district_query)
    districts = districts_q.scalars().all()

    if not districts:
        raise HTTPException(404, "No matching districts found")

    # -----------------------------
    # 5. 查询指标数据（指定日期或每个指标×区县的最新记录）
    # -----------------------------
    if stat_date:
        data_q = await session.execute(
            select(IndicatorData).where(
                IndicatorData.indicator_id.in_(indicator_ids),
                IndicatorData.stat_date == stat_date
            )
        )
        data_list = data_q.scalars().all()
    else:
        latest_subq = (
            select(
                IndicatorData,
                func.row_number().over(
                    partition_by=[IndicatorData.indicator_id, IndicatorData.district_id],
                    order_by=desc(IndicatorData.stat_date)
                ).label("rn")
            )
            .where(IndicatorData.indicator_id.in_(indicator_ids))
            .subquery()
        )
        data_q = await session.execute(select(latest_subq).where(latest_subq.c.rn == 1))
        data_list = data_q.all()

    # 整理为 dict，便于快速查找
    data_map = {}
    for d in data_list:
        if isinstance(d, IndicatorData):
            data_map[(d.indicator_id, d.district_id)] = d.value
        else:
            data_map[(d.indicator_id, d.district_id)] = d.value

    # -----------------------------
    # 6. 组装返回结构
    # -----------------------------
    indicators_result = []

    for ind in indicators:
        district_values = [
            DistrictValue(
                district_id=d.district_id,
                district_name=d.district_name,
                value=data_map.get((ind.indicator_id, d.district_id))
            )
            for d in districts
        ]

        indicators_result.append(
            IndicatorWithDistricts(
                indicator_id=ind.indicator_id,
                indicator_name=ind.indicator_name,
                districts=district_values
            )
        )

    return MajorMetricsResponse(
        major_id=major.major_id,
        major_name=major.major_name,
        stat_date=str(final_date),
        indicators=indicators_result
    )

async def get_metrics_by_type(
    session: AsyncSession,
    type_id: int | None,
    type_name: str | None,
    district_id: int | None,
    districts_name: str | None,
    stat_date: str | None
):
    """
    按指标类型查询指标，并可按区县过滤。
    支持：指定日期 或 自动使用最新日期。
    """

    # -----------------------------
    # 1. 查询指标类型
    # -----------------------------
    query = select(EvaluationType)

    if type_id:
        query = query.where(EvaluationType.type_id == type_id)
    elif type_name:
        query = query.where(EvaluationType.type_name.like(f"%{type_name}%"))
    else:
        raise HTTPException(400, "type_id or type_name must be provided")

    type_obj = (await session.execute(query)).scalar_one_or_none()

    if not type_obj:
        raise HTTPException(404, "Evaluation type not found")

    # -----------------------------
    # 2. 查询该类型下所有指标
    # -----------------------------
    # 去重：按 indicator_id 选择最新有效版本
    dedup_type_subq = (
        select(
            Indicator.indicator_id,
            Indicator.type_id,
            func.row_number().over(
                partition_by=[Indicator.indicator_id],
                order_by=[desc(Indicator.version), desc(Indicator.update_time)]
            ).label("rn"),
        )
        .where(Indicator.status == 1)
        .subquery()
    )

    result = await session.execute(
        select(Indicator)
        .join(dedup_type_subq, dedup_type_subq.c.indicator_id == Indicator.indicator_id)
        .where(dedup_type_subq.c.rn == 1, dedup_type_subq.c.type_id == type_obj.type_id)
    )
    indicators = result.scalars().all()

    if not indicators:
        return TypeMetricsResponse(
            type_id=type_obj.type_id,
            type_name=type_obj.type_name,
            stat_date="",
            indicators=[]
        )

    indicator_ids = [i.indicator_id for i in indicators]

    # -----------------------------
    # 3. 决定日期（最新或指定）
    # -----------------------------
    if stat_date:
        final_date = stat_date
    else:
        latest_q = await session.execute(
            select(func.max(IndicatorData.stat_date)).where(
                IndicatorData.indicator_id.in_(indicator_ids)
            )
        )
        final_date = latest_q.scalar()

    if not final_date:
        raise HTTPException(404, "No data available for this type")

    # -----------------------------
    # 4. 处理区县（支持 id 或 名称）
    # -----------------------------
    district_query = select(District)

    if district_id:
        district_query = district_query.where(District.district_id == district_id)

    if districts_name:
        district_query = district_query.where(
            (District.district_name == districts_name) |
            (District.simple_name == districts_name)
        )

    districts_q = await session.execute(district_query)
    districts = districts_q.scalars().all()

    if not districts:
        raise HTTPException(404, "No matching districts found")

    # -----------------------------
    # 5. 查询指标数据（指定日期或每个指标×区县的最新记录）
    # -----------------------------
    if stat_date:
        data_q = await session.execute(
            select(IndicatorData).where(
                IndicatorData.indicator_id.in_(indicator_ids),
                IndicatorData.stat_date == stat_date
            )
        )
        data_list = data_q.scalars().all()
    else:
        latest_subq = (
            select(
                IndicatorData,
                func.row_number().over(
                    partition_by=[IndicatorData.indicator_id, IndicatorData.district_id],
                    order_by=desc(IndicatorData.stat_date)
                ).label("rn")
            )
            .where(IndicatorData.indicator_id.in_(indicator_ids))
            .subquery()
        )
        data_q = await session.execute(select(latest_subq).where(latest_subq.c.rn == 1))
        data_list = data_q.all()

    # 构造字典加速查找
    data_map = {}
    for d in data_list:
        if isinstance(d, IndicatorData):
            data_map[(d.indicator_id, d.district_id)] = d.value
        else:
            data_map[(d.indicator_id, d.district_id)] = d.value

    # -----------------------------
    # 6. 组装返回
    # -----------------------------
    indicators_result = []

    for ind in indicators:
        district_values = [
            DistrictValue(
                district_id=d.district_id,
                district_name=d.district_name,
                value=data_map.get((ind.indicator_id, d.district_id))
            )
            for d in districts
        ]

        indicators_result.append(
            IndicatorWithDistricts(
                indicator_id=ind.indicator_id,
                indicator_name=ind.indicator_name,
                districts=district_values
            )
        )

    return TypeMetricsResponse(
        type_id=type_obj.type_id,
        type_name=type_obj.type_name,
        stat_date=str(final_date),
        indicators=indicators_result
    )


async def get_all_districts(session: AsyncSession):
    """
    获取所有区县列表
    """
    stmt = select(District).order_by(District.district_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_majors(session: AsyncSession):
    """
    获取所有专业列表
    """
    stmt = select(Major).order_by(Major.major_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_evaluation_types(session: AsyncSession):
    """
    获取所有考核类型列表
    """
    stmt = select(EvaluationType).order_by(EvaluationType.type_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_indicators_simple(session: AsyncSession):
    """
    获取所有指标简单信息（ID和名称）
    """
    stmt = select(Indicator).order_by(Indicator.indicator_id)
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_indicators_simple_by_type(session: AsyncSession, type_id: int):
    stmt = select(Indicator).where(Indicator.type_id == type_id, Indicator.status == 1).order_by(Indicator.indicator_name)
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_indicator_data(session: AsyncSession, data):
    """
    创建指标数据
    如果数据已存在（同一指标、区县、日期），则更新数据
    """
    # 1. 验证指标是否存在
    ind = await session.get(Indicator, data.indicator_id)
    if not ind:
        raise HTTPException(404, "Indicator not found")
        
    # 2. 验证区县是否存在
    dist = await session.get(District, data.district_id)
    if not dist:
        raise HTTPException(404, "District not found")
        
    # 3. 检查是否已存在
    existing_stmt = select(IndicatorData).where(
        IndicatorData.indicator_id == ind.indicator_id,
        IndicatorData.district_id == dist.district_id,
        IndicatorData.stat_date == data.stat_date
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()

    # Validate type_id if provided
    if data.type_id is not None and ind.type_id is not None and data.type_id != ind.type_id:
        raise HTTPException(400, "Provided type_id does not match indicator's type")

    if existing:
        # Update existing
        existing.value = data.value
        existing.benchmark = data.benchmark
        existing.challenge = data.challenge
        existing.exemption = data.exemption
        existing.zero_tolerance = data.zero_tolerance
        existing.score = data.score if hasattr(data, "score") else existing.score
        # keep classification consistent; optionally update type/major if missing
        if existing.type_id is None:
            existing.type_id = data.type_id or ind.type_id
        if existing.major_id is None:
            existing.major_id = ind.major_id
        # Update other fields if necessary
        data_obj = existing
    else:
        # Create new
        data_obj = IndicatorData(
            indicator_id=ind.indicator_id,
            indicator_name=ind.indicator_name,
            type_id=data.type_id or ind.type_id,
            major_id=ind.major_id,
            is_positive=ind.is_positive,
            circle_id=dist.circle_id or 0,
            district_id=dist.district_id,
            district_name=dist.district_name,
            stat_date=data.stat_date,
            value=data.value,
            benchmark=data.benchmark,
            challenge=data.challenge,
            exemption=data.exemption,
            zero_tolerance=data.zero_tolerance,
            score=(data.score if hasattr(data, "score") else None)
        )
        session.add(data_obj)
    
    await session.commit()
    await session.refresh(data_obj)
    return data_obj

# =========================
# Indicator CRUD
# =========================
async def list_indicators(
    session: AsyncSession,
    q: Optional[str] = None,
    type_id: Optional[int] = None,
    page: int = 1,
    size: int = 50,
):
    stmt = select(Indicator)
    if q:
        stmt = stmt.where(Indicator.indicator_name.like(f"%{q}%"))
    if type_id is not None:
        stmt = stmt.where(Indicator.type_id == type_id)
    count = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(asc(Indicator.indicator_id)).offset((page - 1) * size).limit(size)
    rows = (await session.execute(stmt)).scalars().all()
    return ([IndicatorOut.model_validate(r) for r in rows], count)

async def create_indicator(session: AsyncSession, payload: IndicatorBase):
    obj = Indicator(
        indicator_name=payload.indicator_name,
        unit=payload.unit,
        category_id=payload.category_id,
        major_id=payload.major_id,
        type_id=payload.type_id,
        is_positive=payload.is_positive,
        data_owner=payload.data_owner,
        data_dept=payload.data_dept,
        description=payload.description,
        status=payload.status or 1,
        version=payload.version or 1,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return IndicatorOut.model_validate(obj)

async def update_indicator(session: AsyncSession, indicator_id: int, payload: IndicatorBase):
    obj = await session.get(Indicator, indicator_id)
    if not obj:
        raise HTTPException(404, "Indicator not found")
    before = {
        "indicator_name": obj.indicator_name,
        "type_id": obj.type_id,
        "major_id": obj.major_id,
        "is_positive": obj.is_positive,
    }
    for field in payload.model_fields_set:
        setattr(obj, field, getattr(payload, field))
    sync_fields: dict = {}
    if obj.indicator_name != before["indicator_name"]:
        sync_fields["indicator_name"] = obj.indicator_name
    if obj.type_id != before["type_id"]:
        sync_fields["type_id"] = obj.type_id
    if obj.major_id != before["major_id"]:
        sync_fields["major_id"] = obj.major_id
    if obj.is_positive != before["is_positive"]:
        sync_fields["is_positive"] = obj.is_positive
    if sync_fields:
        sync_fields["update_time"] = func.now()
        await session.execute(
            update(IndicatorData)
            .where(IndicatorData.indicator_id == indicator_id)
            .values(**sync_fields)
        )
        await session.execute(
            update(IndicatorCenterData)
            .where(IndicatorCenterData.indicator_id == indicator_id)
            .values(**sync_fields)
        )
    await session.commit()
    await session.refresh(obj)
    return IndicatorOut.model_validate(obj)

async def delete_indicator(session: AsyncSession, indicator_id: int):
    obj = await session.get(Indicator, indicator_id)
    if not obj:
        raise HTTPException(404, "Indicator not found")
    await session.delete(obj)
    await session.commit()
    return {"deleted": 1}
