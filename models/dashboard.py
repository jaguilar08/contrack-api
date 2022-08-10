from pydantic import BaseModel


class DashboardGroup(BaseModel):
    quantity: int = 0
    total_value: float = 0.0
    average_value: float = 0.0


class DashboardOut(BaseModel):
    quantity: int = 0
    total_value: float = 0.0
    average_value: float = 0.0
    by_category: dict[str, DashboardGroup] = {}
    by_responsible: dict[str, DashboardGroup] = {}
    by_periodicity: dict[str, DashboardGroup] = {}
    inactive_quantity: int = 0
    inactive_total_value: float = 0.0
