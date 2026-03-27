from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.master_data_service import MasterDataService
from app.schemas.master_data.professional_level import ( ProfessionalLevelResponse )
from app.schemas.master_data.nurse import ( NurseTypeResponse )
from app.schemas.master_data.doctor import ( DoctorSpecialtyResponse )
from app.schemas.master_data.address import ProvinceResponse,  DistrictResponse, SubdistrictResponse

router = APIRouter(prefix="/master-data", tags=["Master Data"])

@router.get(
    "/professional-levels", 
    summary="Get professional levels",
    description="""
    ใช้สำหรับดึงรายการระดับวิชาชีพทางการแพทย์ทั้งหมด
    """,
    response_model=list[ProfessionalLevelResponse]
)
def get_professional_levels(db: Session = Depends(get_db)):
    return MasterDataService.get_professional_levels(db)


@router.get(
    "/nurse-types", 
    summary="Get nurse types",
    description="""
    ใช้สำหรับดึงรายการประเภทพยาบาลทั้งหมด
    """,
    response_model=list[NurseTypeResponse]
)
def get_nurse_types(db: Session = Depends(get_db)):
    return MasterDataService.get_nurse_types(db)


@router.get(
    "/doctor-specialties", 
    summary="Get doctor specialties",
    description="""
    ใช้สำหรับดึงรายการสาขาแพทย์เฉพาะทางทั้งหมด
    """,
    response_model=list[DoctorSpecialtyResponse]
)
def get_doctor_specialties(db: Session = Depends(get_db)):
    return MasterDataService.get_doctor_specialties(db)


@router.get(
    "/provinces",
    summary="Get provinces",
    response_model=list[ProvinceResponse],
)
def get_provinces(db: Session = Depends(get_db)):
    return MasterDataService.get_provinces(db)


@router.get(
    "/provinces/{province_id}/districts",
    summary="Get districts by province",
    response_model=list[DistrictResponse],
)
def get_districts(
    province_id: int,
    db: Session = Depends(get_db),
):
    return MasterDataService.get_districts_by_province(db, province_id)


@router.get(
    "/districts/{district_id}/subdistricts",
    summary="Get subdistricts by district",
    response_model=list[SubdistrictResponse],
)
def get_subdistricts(
    district_id: int,
    db: Session = Depends(get_db),
):
    return MasterDataService.get_subdistricts_by_district(db, district_id)


@router.get(
    "/subdistricts/{subdistrict_id}",
    summary="Get subdistrict detail",
    response_model=SubdistrictResponse,
)
def get_subdistrict_detail(
    subdistrict_id: int,
    db: Session = Depends(get_db),
):
    result = MasterDataService.get_subdistrict_detail(db, subdistrict_id)
    if not result:
        raise HTTPException(status_code=404, detail="Subdistrict not found")
    return result