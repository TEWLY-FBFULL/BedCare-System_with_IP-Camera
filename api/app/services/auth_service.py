import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.doctor import Doctor
from app.models.nurse import Nurse
from app.models.role import Role
from app.models.user_token import UserToken

from app.utils.password import hash_password, verify_password
from app.utils.token_generator import generate_token
from app.core.security import create_access_token
from app.services.email_service import EmailService

class AuthService:
    def _get_role_id(self, db: Session, role_name: str) -> int:
        role = db.query(Role).filter(Role.role_name == role_name).first()
        if not role:
            raise ValueError("ไม่พบบทบาทผู้ใช้งาน")
        return role.role_id
    
    def _ensure_email_not_exists(self, db: Session, email: str):
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            raise ValueError("อีเมลนี้ถูกใช้งานแล้ว")
        
    def _create_verify_token(self, db: Session, user: User):
        token, expires_at = generate_token(60)
        verify_token = UserToken(
            user_id=user.user_id,
            token=token,
            token_type="verify_email",
            expires_at=expires_at
        )
        db.add(verify_token)
        return token
    
    def _create_reset_token(self, db: Session, user: User):
        token, expires_at = generate_token(30)
        reset_token = UserToken(
            user_id=user.user_id,
            token=token,
            token_type="reset_password",
            expires_at=expires_at
        )
        db.add(reset_token)
        return token
    
    def register_doctor(self, db: Session, payload):
        try:
            self._ensure_email_not_exists(db, payload.email)
            role_id = self._get_role_id(db, "doctor")
            user = User(
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                phone=payload.phone,
                password_hash=hash_password(payload.password),
                role_id=role_id
            )
            db.add(user)
            db.flush() # to get user_id
            doctor = Doctor(
                doctor_id=user.user_id,
                specialty_id=payload.specialty_id,
                level_id=payload.level_id,
                license_no=payload.license_no
            )
            db.add(doctor)
            # create token + send email
            token = self._create_verify_token(db, user)
            db.commit()
            frontend_url = os.getenv("REAL_FRONTEND_URL")
            verify_url = f"{frontend_url}/verify?token={token}"
            EmailService.send_verify_email(user.email, verify_url)
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise
    
    def register_nurse(self, db: Session, payload):
        try:
            self._ensure_email_not_exists(db, payload.email)
            role_id = self._get_role_id(db, "nurse")
            user = User(
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                phone=payload.phone,
                password_hash=hash_password(payload.password),
                role_id=role_id
            )
            db.add(user)
            db.flush() # to get user_id
            nurse = Nurse(
                nurse_id=user.user_id,
                nurse_type_id=payload.nurse_type_id,
                level_id=payload.level_id,
                license_no=payload.license_no
            )
            db.add(nurse)
            # create token + send email
            token = self._create_verify_token(db, user)
            db.commit()
            frontend_url = os.getenv("REAL_FRONTEND_URL")
            verify_url = f"{frontend_url}/verify?token={token}"
            EmailService.send_verify_email(user.email, verify_url)
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise
    
    def register_relative(self, db: Session, payload):
        try:
            self._ensure_email_not_exists(db, payload.email)
            role_id = self._get_role_id(db, "relative")
            user = User(
                first_name=payload.first_name,
                last_name=payload.last_name,
                email=payload.email,
                phone=payload.phone,
                password_hash=hash_password(payload.password),
                role_id=role_id
            )
            db.add(user)
            db.flush()
            # create token + send email
            token = self._create_verify_token(db, user)
            db.commit()
            frontend_url = os.getenv("REAL_FRONTEND_URL")
            verify_url = f"{frontend_url}/verify?token={token}"
            EmailService.send_verify_email(user.email, verify_url)
            db.refresh(user)
            return user
        except Exception:
            db.rollback()
            raise

    def login(self, db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("อีเมลหรือรหัสผ่านไม่ถูกต้อง")
        if not user.is_active or not user.email_verified:
            raise ValueError("เกิดข้อผิดพลาด กรุณาลองอีกครั้งภายหลัง")
        # get role_name
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        role_name = role.role_name if role else "unknown"
        token = create_access_token({
            "sub": str(user.user_id),
            "role": role_name,
            "tv": user.token_version
        })
        return token
    
    def verify_email(self, db: Session, token: str):
        now_utc = datetime.now(timezone.utc)
        token_row = (
            db.query(UserToken)
            .filter(
                UserToken.token == token,
                UserToken.token_type == "verify_email",
                UserToken.used_at.is_(None),
                UserToken.expires_at > now_utc
            )
            .first()
        )
        if not token_row:
            raise ValueError("Token ไม่ถูกต้องหรือหมดอายุ")
        user = db.query(User).filter(User.user_id == token_row.user_id).first()
        if not user:
            raise ValueError("ไม่พบผู้ใช้งาน")
        user.email_verified = True
        user.is_active = True
        token_row.used_at = now_utc
        db.commit()
        return {
            "message": "ยืนยันอีเมลสำเร็จ",
            "verified_at": now_utc.isoformat()
        }
    
    def forgot_password(self, db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        response = {
            "message": "หากอีเมลนี้มีอยู่ในระบบ เราจะส่งลิงก์รีเซ็ตรหัสผ่านให้"
        }
        if not user:
            return response
        if not user.is_active:
            return response
        token = self._create_reset_token(db, user)
        db.commit()
        frontend_url = os.getenv("DEVTEST_URL")
        reset_url = f"{frontend_url}/auth/reset-password?token={token}"
        EmailService.send_reset_password_email(user.email, reset_url)
        return response

    def reset_password(self, db: Session, token: str, new_password: str):
        now_utc = datetime.now(timezone.utc)
        token_row = (
            db.query(UserToken)
            .filter(
                UserToken.token == token,
                UserToken.token_type == "reset_password",
                UserToken.used_at.is_(None),
                UserToken.expires_at > now_utc
            )
            .first()
        )
        if not token_row:
            raise ValueError("Token ไม่ถูกต้องหรือหมดอายุ")
        user = db.query(User).filter(User.user_id == token_row.user_id).first()
        if not user:
            raise ValueError("ไม่พบผู้ใช้งาน")
        user.password_hash = hash_password(new_password)
        token_row.used_at = now_utc
        db.commit()
        return {
            "message": "รีเซ็ตรหัสผ่านสำเร็จ",
            "reset_at": now_utc.isoformat()
        }
    
    def logout(self, db: Session, user: User):
        # bump token version → revoke all existing tokens
        user.token_version += 1
        db.commit()
        return {"message": "Logged out successfully"}