from pydantic import BaseModel
from typing import List, Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    items: List[T]

class PageResponse(GenericModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    size: int
