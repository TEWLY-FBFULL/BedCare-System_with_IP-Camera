from app.schemas.auth.base import BaseRegister

class DoctorRegister(BaseRegister):
    specialty_id: int
    level_id: int | None = None
    license_no: str
