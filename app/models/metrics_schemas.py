# =============================
# app/models/metrics_schemas.py
# =============================
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

class IndicatorBase(BaseModel):
    indicator_name: str
    unit: Optional[str] = None
    category_id: Optional[int] = None
    major_id: Optional[int] = None
    type_id: Optional[int] = None
    kpi_type_id: Optional[int] = None
    is_positive: int = Field(..., ge=0, le=2)
    data_owner: Optional[str] = None
    data_dept: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = 1
    version: Optional[int] = 1

class IndicatorOut(IndicatorBase):
    indicator_id: int

    class Config:
        from_attributes = True

class IndicatorDataBase(BaseModel):
    indicator_id: int
    indicator_name: str
    type_id: Optional[int] = None
    major_id: Optional[int] = None
    is_positive: int
    circle_id: int
    district_id: int
    district_name: str
    stat_date: date
    value: Optional[float] = None
    benchmark: Optional[float] = None
    challenge: Optional[float] = None
    exemption: Optional[float] = None
    zero_tolerance: Optional[float] = None
    score: Optional[float] = None

class IndicatorDataOut(IndicatorDataBase):
    id: int

    class Config:
        from_attributes = True

class IndicatorDataResponse(BaseModel):
    items: List[IndicatorDataOut]
    total: int

class IndicatorDataDelete(BaseModel):
    ids: Optional[List[int]] = None
    indicator_id: Optional[int] = None
    district_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Query params model (helpful for documentation)
class IndicatorDataQuery(BaseModel):
    indicator_id: Optional[int] = None
    indicator_code: Optional[str] = None
    district_id: Optional[int] = None
    circle_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = 1
    size: int = 50
    order_by: str = "stat_date"
    desc: bool = True

class DistrictIndicatorValue(BaseModel):
    indicator_name: str
    value: Optional[float]
    benchmark: Optional[float]
    challenge: Optional[float]
    exemption: Optional[float]
    zero_tolerance: Optional[float]
    score: Optional[float]

class IndicatorLatestQueryOut(BaseModel):
    indicator_id: int
    indicator_name: str
    district_id: int
    district_name: str
    circle_id: int
    stat_date: date
    value: Optional[float]
    score: Optional[float]

    class Config:
        from_attributes = True


class DistrictValue(BaseModel):
    district_id: int
    district_name: str
    value: Optional[float]

class IndicatorWithDistricts(BaseModel):
    indicator_id: int
    indicator_name: str
    districts: List[DistrictValue]

class MajorMetricsResponse(BaseModel):
    major_id: int
    major_name: str
    stat_date: str
    indicators: List[IndicatorWithDistricts]

class TypeMetricsResponse(BaseModel):
    type_id: int
    type_name: str
    stat_date: str
    indicators: List[IndicatorWithDistricts]

class DistrictMetricsResponse(BaseModel):
    district_id: int
    district_name: str
    stat_date: str
    indicators: list[DistrictIndicatorValue]

class CenterOut(BaseModel):
    center_id: int
    district_id: int | None = None
    center_name: str

    class Config:
        from_attributes = True

class CenterIndicatorValue(BaseModel):
    indicator_name: str
    value: Optional[float]
    benchmark: Optional[float]
    challenge: Optional[float]
    score: Optional[float]

class CenterMetricsResponse(BaseModel):
    center_id: int
    center_name: str
    district_id: int | None = None
    district_name: str | None = None
    stat_date: str
    indicators: list[CenterIndicatorValue]

class IndicatorCenterDataBase(BaseModel):
    indicator_id: int
    indicator_name: str
    type_id: Optional[int] = None
    major_id: Optional[int] = None
    is_positive: int
    center_id: int
    center_name: str
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    stat_date: date
    value: Optional[float] = None
    benchmark: Optional[float] = None
    challenge: Optional[float] = None
    exemption: Optional[float] = None
    zero_tolerance: Optional[float] = None
    score: Optional[float] = None

class IndicatorCenterDataOut(IndicatorCenterDataBase):
    id: int

    class Config:
        from_attributes = True

class IndicatorCenterDataResponse(BaseModel):
    items: List[IndicatorCenterDataOut]
    total: int

class IndicatorCenterDataCreate(BaseModel):
    indicator_id: int
    center_id: int
    stat_date: date
    value: float
    type_id: Optional[int] = None
    benchmark: Optional[float] = None
    challenge: Optional[float] = None
    score: Optional[float] = None

class IndicatorCenterDataDelete(BaseModel):
    ids: Optional[List[int]] = None
    indicator_id: Optional[int] = None
    center_id: Optional[int] = None
    district_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class CenterLatestQueryOut(BaseModel):
    indicator_id: int
    indicator_name: str
    center_id: int
    center_name: str
    district_id: int | None = None
    district_name: str | None = None
    stat_date: date
    value: Optional[float]
    score: Optional[float]

    class Config:
        from_attributes = True


class DistrictOut(BaseModel):
    district_id: int
    district_name: str
    simple_name: str

    class Config:
        from_attributes = True


class MajorOut(BaseModel):
    major_id: int
    major_name: str
    major_code: str

    class Config:
        from_attributes = True

class MajorBase(BaseModel):
    major_name: str
    major_code: str


class EvaluationTypeOut(BaseModel):
    type_id: int
    type_name: str

    class Config:
        from_attributes = True

class CategoryOut(BaseModel):
    category_id: int
    category_name: str

    class Config:
        from_attributes = True


class IndicatorSimpleOut(BaseModel):
    indicator_id: int
    indicator_name: str

    class Config:
        from_attributes = True


class IndicatorDataCreate(BaseModel):
    indicator_id: int
    district_id: int
    stat_date: date
    value: float
    type_id: Optional[int] = None
    benchmark: Optional[float] = None
    challenge: Optional[float] = None
    exemption: Optional[float] = None
    zero_tolerance: Optional[float] = None
    score: Optional[float] = None


class IndicatorDashboardOut(BaseModel):
    district_name: str
    stat_date: date
    indicator_name: str
    value: float | None
    benchmark: float | None
    challenge: float | None
    exemption: float | None
    zero_tolerance: float | None
    score: float | None
