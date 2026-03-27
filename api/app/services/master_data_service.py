from sqlalchemy.orm import Session
from app.models.professional_level import ProfessionalLevel
from app.models.nurse_type import NurseType
from app.models.doctor_specialty import DoctorSpecialty
from app.models.province import Province 
from app.models.district import District
from app.models.subdistrict import Subdistrict

class MasterDataService:
    @staticmethod
    def get_professional_levels(db: Session):
        items = db.query(ProfessionalLevel).order_by(ProfessionalLevel.level_id).all()
        return [
            {"level_id": i.level_id,
            "level_name": i.level_name}
            for i in items
        ]

    @staticmethod
    def get_nurse_types(db: Session):
        items = db.query(NurseType).order_by(NurseType.nurse_type_id).all()
        return [
            {"nurse_type_id": i.nurse_type_id,
            "nurse_type_name": i.nurse_type_name}
            for i in items
        ]

    @staticmethod
    def get_doctor_specialties(db: Session):
        items = db.query(DoctorSpecialty).order_by(DoctorSpecialty.specialty_id).all()
        return [
            {"specialty_id": i.specialty_id,
            "specialty_name": i.specialty_name}
            for i in items
        ]
    
    @staticmethod
    def get_provinces(db: Session):
        items = db.query(Province).order_by(Province.province_name).all()
        return [
            {
                "province_id": i.province_id,
                "province_name": i.province_name,
            }
            for i in items
        ]

    @staticmethod
    def get_districts_by_province(db: Session, province_id: int):
        items = (
            db.query(District)
            .filter(District.province_id == province_id)
            .order_by(District.district_name)
            .all()
        )
        return [
            {
                "district_id": i.district_id,
                "district_name": i.district_name,
                "province_id": i.province_id,
            }
            for i in items
        ]

    @staticmethod
    def get_subdistricts_by_district(db: Session, district_id: int):
        items = (
            db.query(Subdistrict)
            .filter(Subdistrict.district_id == district_id)
            .order_by(Subdistrict.subdistrict_name)
            .all()
        )
        return [
            {
                "subdistrict_id": i.subdistrict_id,
                "subdistrict_name": i.subdistrict_name,
                "zip_code": i.zip_code,
                "district_id": i.district_id,
            }
            for i in items
        ]

    @staticmethod
    def get_subdistrict_detail(db: Session, subdistrict_id: int):
        sd = (
            db.query(Subdistrict)
            .filter(Subdistrict.subdistrict_id == subdistrict_id)
            .first()
        )
        if not sd:
            return None
        return {
            "subdistrict_id": sd.subdistrict_id,
            "subdistrict_name": sd.subdistrict_name,
            "zip_code": sd.zip_code,
            "district_id": sd.district_id,
        }