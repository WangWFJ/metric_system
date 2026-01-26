# app/models/metrics.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Date, DateTime, DECIMAL, SmallInteger, Text
from sqlalchemy import func
from datetime import date, datetime
from models.database import Base  # use your existing DeclarativeBase

class District(Base):
    __tablename__ = "districts"
    district_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    circle_id: Mapped[int | None] = mapped_column(Integer)
    district_name: Mapped[str] = mapped_column(String(32), nullable=False)
    simple_name: Mapped[str] = mapped_column(String(32), nullable=False)

class Center(Base):
    __tablename__ = "centers"
    center_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[int | None] = mapped_column(Integer)
    center_name: Mapped[str] = mapped_column(String(128), nullable=False)


class Category(Base):
    __tablename__ = "categories"
    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(32), nullable=False)


class EvaluationType(Base):
    __tablename__ = "evaluation_types"
    type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_name: Mapped[str] = mapped_column(String(64), nullable=False)


class Major(Base):
    __tablename__ = "majors"
    major_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    major_code: Mapped[str] = mapped_column(String(10), nullable=False)
    major_name: Mapped[str] = mapped_column(String(100), nullable=False)


class KPIType(Base):
    __tablename__ = "kpi_types"
    kpi_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kpi_type: Mapped[str | None] = mapped_column(String(64))


class DimDate(Base):
    __tablename__ = "dim_date"
    day: Mapped[date] = mapped_column(Date, primary_key=True)  # SQLAlchemy Date maps to python date


class Indicator(Base):
    __tablename__ = "indicator"
    indicator_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    category_id: Mapped[int | None] = mapped_column(Integer)
    major_id: Mapped[int | None] = mapped_column(Integer)
    type_id: Mapped[int | None] = mapped_column(Integer)
    is_positive: Mapped[int] = mapped_column(SmallInteger)
    data_owner: Mapped[str | None] = mapped_column(String(50))
    data_dept: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    version: Mapped[int] = mapped_column(SmallInteger, default=1)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IndicatorData(Base):
    __tablename__ = "indicator_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # note: original table used BIGINT with composite PK (id, stat_date). Here primary key on id for ORM simplicity.
    indicator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_positive: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    circle_id: Mapped[int] = mapped_column(Integer, nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, nullable=False)
    district_name: Mapped[str] = mapped_column(String(32), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    benchmark: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    challenge: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    exemption: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    zero_tolerance: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    score: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IndicatorDataV2(Base):
    __tablename__ = "indicator_data_v2"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    type_id: Mapped[int | None] = mapped_column(Integer)
    major_id: Mapped[int | None] = mapped_column(Integer)
    is_positive: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    circle_id: Mapped[int] = mapped_column(Integer, nullable=False)
    district_id: Mapped[int] = mapped_column(Integer, nullable=False)
    district_name: Mapped[str] = mapped_column(String(32), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    benchmark: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    challenge: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    exemption: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    zero_tolerance: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    score: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class IndicatorCenterData(Base):
    __tablename__ = "indicator_center_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    type_id: Mapped[int | None] = mapped_column(Integer)
    major_id: Mapped[int | None] = mapped_column(Integer)
    is_positive: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    center_id: Mapped[int] = mapped_column(Integer, nullable=False)
    center_name: Mapped[str] = mapped_column(String(32), nullable=False)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    benchmark: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    challenge: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    exemption: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    zero_tolerance: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    score: Mapped[float | None] = mapped_column(DECIMAL(18,4))
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
