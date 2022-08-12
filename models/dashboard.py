from pydantic import BaseModel


class MonthlyDashboardGroup(BaseModel):
    key: str
    quantity: int = 0
    total_value: float = 0.0
    average_value: float = 0.0


class MonthlyDashboardOut(BaseModel):
    quantity: int = 0
    total_value: float = 0.0
    average_value: float = 0.0
    by_category: list[MonthlyDashboardGroup] = []
    by_responsible: list[MonthlyDashboardGroup] = []
    by_periodicity: list[MonthlyDashboardGroup] = []
    inactive_quantity: int = 0
    inactive_total_value: float = 0.0


class AnnualDashboardGroup(BaseModel):
    quantity: int = 0
    total_value: float = 0.0


class AnnualDashboardOut(BaseModel):
    by_month: dict[str, AnnualDashboardGroup] = {}
    by_periodicity: dict[str, AnnualDashboardGroup] = {}
    by_value_range_qty: dict[str, int] = {}


class OldestDateOut(BaseModel):
    year: int
    month: int
