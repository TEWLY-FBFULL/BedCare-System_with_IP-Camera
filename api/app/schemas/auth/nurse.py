from app.schemas.auth.base import BaseRegister

class NurseRegister(BaseRegister):
    nurse_type_id: int
    level_id: int | None = None
    license_no: str | None = None
