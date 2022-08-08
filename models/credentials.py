from dataclasses import dataclass


@dataclass
class Credentials:
    user_id: str
    user_application: str
    user_name: str
    user_email: str | None
    roles: list[str] | None
