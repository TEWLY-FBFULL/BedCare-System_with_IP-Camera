from pydantic import BaseModel

class ProvinceResponse(BaseModel):
    province_id: int
    province_name: str
    class Config:
        from_attributes = True

class DistrictResponse(BaseModel):
    district_id: int
    district_name: str
    province_id: int
    class Config:
        from_attributes = True

class SubdistrictResponse(BaseModel):
    subdistrict_id: int
    subdistrict_name: str
    zip_code: str | None
    district_id: int
    class Config:
        from_attributes = True