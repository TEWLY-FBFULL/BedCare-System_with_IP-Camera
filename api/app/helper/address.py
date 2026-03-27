from sqlalchemy.orm import Session
from app.models.address import Address
from app.models.subdistrict import Subdistrict
from app.models.district import District
from app.models.province import Province
from app.schemas.user.address import AddressInfo

def get_full_address(db: Session, address_id: int):
    addr = (
        db.query(Address, Subdistrict, District, Province)
        .join(Subdistrict, Address.subdistrict_id == Subdistrict.subdistrict_id)
        .join(District, Subdistrict.district_id == District.district_id)
        .join(Province, District.province_id == Province.province_id)
        .filter(Address.address_id == address_id)
        .first()
    )
    if not addr:
        return None
    a, sd, d, p = addr
    return AddressInfo(
        address_id=a.address_id,
        house_no=a.house_no,
        road=a.road,
        village=a.village,
        subdistrict_id=sd.subdistrict_id,
        subdistrict_name=sd.subdistrict_name,
        zip_code=sd.zip_code,
        district_id=d.district_id,
        district_name=d.district_name,
        province_id=p.province_id,
        province_name=p.province_name,
    )