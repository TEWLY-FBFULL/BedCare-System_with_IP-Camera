from pydantic import BaseModel
from typing import Optional

class AddressInfo(BaseModel):
    address_id: int
    house_no: Optional[str]
    road: Optional[str]
    village: Optional[str]
    subdistrict_id: int
    subdistrict_name: str
    zip_code: Optional[str]
    district_id: int
    district_name: str
    province_id: int
    province_name: str

class AddressUpdateRequest(BaseModel):
    house_no: Optional[str] = None
    road: Optional[str] = None
    village: Optional[str] = None
    subdistrict_id: int