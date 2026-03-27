import re
from pydantic import BaseModel, EmailStr, Field, validator

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$"
)

class BaseRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str = Field(min_length=9, max_length=10)
    password: str = Field(min_length=8)
    @validator("password")
    def validate_password(cls, v: str):
        if " " in v:
            raise ValueError("รหัสผ่านต้องไม่มีช่องว่าง")
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร และประกอบด้วยตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และอักขระพิเศษ"
            )
        return v
    
    @validator("phone")
    def validate_phone(cls, v: str):
        if not v.isdigit():
            raise ValueError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
    @validator("new_password")
    def validate_password(cls, v: str):
        if " " in v:
            raise ValueError("รหัสผ่านต้องไม่มีช่องว่าง")
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร และประกอบด้วยตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก ตัวเลข และอักขระพิเศษ"
            )
        return v