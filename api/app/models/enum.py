from sqlalchemy.types import Enum as PgEnum
import enum

relation_type_enum = PgEnum(
    "caregiver", "relative", "doctor", name="relation_type_enum"
)

FacilityTypeEnum = PgEnum(
    "home", "hospital", "other", name="facility_type_enum"
)

class SensorTypeEnumClass(str, enum.Enum):
    pi_camera_motion = "pi_camera_motion"
    bme680 = "bme680"
    bh1750 = "bh1750"
    hlk_ld2410 = "hlk_ld2410"
    usb_microphone = "usb_microphone"
    emergency_button = "emergency_button"

SensorTypeEnum = PgEnum(
    SensorTypeEnumClass,
    name="sensor_type_enum"
)

PostureLabelEnum = PgEnum(
    "Supine", "Prone", "To-Left", "To-Right", "Unknown",
    name="posture_label_enum"
)

PostureQualityEnum = PgEnum(
    "good", "moderate", "poor", "danger", name="posture_quality_enum"
)

class AlertTypeEnumClass(str, enum.Enum):
    posture = "posture"
    vital = "vital"
    environment = "environment"

AlertTypeEnum = PgEnum(
    AlertTypeEnumClass,
    name="alert_type_enum"
)

class SeverityEnumClass(str, enum.Enum):
    warning = "warning"
    emergency = "emergency"

SeverityEnum = PgEnum(
    SeverityEnumClass,
    name="severity_enum"
)