import smtplib
from email.message import EmailMessage
import os
from app.models.patient import Patient
from app.models.room import Room
from app.models.alert_log import AlertLog
from app.models.user import User
from sqlalchemy.orm import Session
from app.services.permission import get_alert_recipients
from app.models.enum import SeverityEnumClass

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = os.getenv("MQTT_PORT")
DEVTEST_URL = os.getenv("DEVTEST_URL")

class EmailService:
    @staticmethod
    def send_verify_email(email: str, verify_url: str):
        msg = EmailMessage()
        msg["Subject"] = "ยืนยันอีเมลของคุณกับ SleepCare"
        msg["From"] = EMAIL_HOST
        msg["To"] = email
        # text fallback
        msg.set_content(f"กรุณายืนยันอีเมลของคุณ: {verify_url}")
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
            <div style="max-width:600px;margin:auto;background:white;border-radius:8px;padding:30px;text-align:center;">
                <h2 style="color:#2c3e50;">ยืนยันอีเมลของคุณ</h2>
                <p style="color:#555;font-size:16px;">
                    ขอบคุณที่สมัครใช้งาน <b>SleepCare</b><br>
                    กรุณาคลิกปุ่มด้านล่างเพื่อยืนยันอีเมลของคุณ
                </p>
                <a href="{verify_url}" 
                style="display:inline-block;margin-top:20px;padding:14px 28px;
                background-color:#4CAF50;color:white;text-decoration:none;
                border-radius:6px;font-size:16px;font-weight:bold;">
                ยืนยันอีเมล
                </a>
                <p style="margin-top:30px;color:#888;font-size:14px;">
                    หากปุ่มไม่ทำงาน กรุณาคัดลอกลิงก์นี้ไปเปิดในเบราว์เซอร์
                </p>
                <p style="word-break:break-all;color:#3498db;">
                    {verify_url}
                </p>
                <hr style="margin-top:30px;border:none;border-top:1px solid #eee;">
                <p style="font-size:12px;color:#aaa;">
                    SleepCare System
                </p>
            </div>
        </body>
        </html>
        """
        msg.add_alternative(html_content, subtype="html")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                smtp.send_message(msg)
            return "ส่งสำเร็จแล้ว!"
        except Exception as e:
            print("[DEV] Verify email:", email, verify_url)
            return "ไม่สามารถส่งอีเมลได้"

    @staticmethod
    def send_reset_password_email(email: str, reset_url: str):
        msg = EmailMessage()
        html_content = f"""
        <html>
            <body>
                <p>คุณได้ขอรีเซ็ตรหัสผ่านสำหรับบัญชี <b>SleepCare</b></p>
                <p>กรุณาคลิกที่ลิงก์ด้านล่างเพื่อเปลี่ยนรหัสผ่านใหม่:</p>
                <p>
                    <a href="{reset_url}"
                       style="display:inline-block;
                              padding:10px 15px;
                              background-color:#4CAF50;
                              color:white;
                              text-decoration:none;
                              border-radius:5px;">
                        รีเซ็ตรหัสผ่าน
                    </a>
                </p>
                <p>หากคุณไม่ได้เป็นผู้ร้องขอ สามารถละเว้นอีเมลนี้ได้</p>
            </body>
        </html>
        """
        msg["Subject"] = "รีเซ็ตรหัสผ่าน SleepCare"
        msg["From"] = EMAIL_HOST
        msg["To"] = email
        msg.set_content("กรุณาเปิดอีเมลนี้ด้วยโปรแกรมที่รองรับ HTML")
        msg.add_alternative(html_content, subtype="html")
        try: # use Port 465 for SSL
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                smtp.send_message(msg)
            return "ส่งอีเมลรีเซ็ตรหัสผ่านสำเร็จแล้ว!"
        except Exception as e:
            print("[DEV] Reset password error:", email, reset_url)
            return "ไม่สามารถส่งอีเมลได้"

    @staticmethod
    def send_patient_share_email(
        email: str, 
        share_url: str,
        inviter_name: str,
        role_name: str,
        expires_at: str
        ):
        msg = EmailMessage()
        html_content = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
        <div style="max-width:600px; margin:auto; background:white; padding:30px; border-radius:8px; box-shadow:0 4px 10px rgba(0,0,0,0.05);">
            <h2 style="color:#2196F3; margin-top:0;">คำเชิญเข้าดูแลผู้ป่วย</h2>
            <p>สวัสดี,</p>
            <p>
            <strong>{inviter_name}</strong> ได้เชิญคุณให้เข้าถึงข้อมูลผู้ป่วยในระบบ <b>SleepCare</b>
            </p>
            <table style="width:100%; margin:20px 0; border-collapse: collapse;">
            <tr>
                <td style="padding:8px 0;"><strong>บทบาทที่ได้รับ:</strong></td>
                <td style="padding:8px 0;">{role_name}</td>
            </tr>
            <tr>
                <td style="padding:8px 0;"><strong>ลิงก์หมดอายุ:</strong></td>
                <td style="padding:8px 0; color:#d32f2f;">{expires_at}</td>
            </tr>
            </table>
            <div style="text-align:center; margin:30px 0;">
            <a href="{share_url}"
                style="background-color:#2196F3;
                        color:white;
                        padding:12px 20px;
                        text-decoration:none;
                        border-radius:6px;
                        font-weight:bold;
                        display:inline-block;">
                ยืนยันการเข้าถึงผู้ป่วย
            </a>
            </div>
            <p style="font-size:14px; color:#555;">
            หากคุณไม่ได้คาดหวังคำเชิญนี้ สามารถเพิกเฉยต่ออีเมลฉบับนี้ได้
            </p>
            <hr style="margin:30px 0; border:none; border-top:1px solid #eee;">
            <p style="font-size:12px; color:#999;">
            ระบบ SleepCare | อีเมลนี้ถูกส่งโดยอัตโนมัติ
            </p>
        </div>
        </body>
        </html>
        """
        msg["Subject"] = "คุณได้รับคำเชิญให้เข้าดูแลผู้ป่วยใน SleepCare"
        msg["From"] = EMAIL_HOST
        msg["To"] = email
        msg.set_content(f"""
            คุณได้รับคำเชิญจาก {inviter_name}
            บทบาทที่ได้รับ: {role_name}
            ลิงก์หมดอายุ: {expires_at}
            คลิกที่ลิงก์นี้:
            {share_url}
            """)
        msg.add_alternative(html_content, subtype="html")
        try: # use Port 465 for SSL
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                smtp.send_message(msg)
            return "ส่งอีเมลเชิญดูแลผู้ป่วยสำเร็จแล้ว!"
        except Exception as e:
            print("[DEV] Patient share email error:", email, share_url)
            return "ไม่สามารถส่งอีเมลได้"
        
    @staticmethod
    def send_facility_share_email(
        email: str,
        share_url: str,
        inviter_name: str,
        facility_name: str,
        role_name: str,
        expires_at: str,
    ):
        msg = EmailMessage()
        html_content = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
        <div style="max-width:600px; margin:auto; background:white; padding:30px; border-radius:10px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
            <h2 style="color:#4CAF50; margin-top:0;">คำเชิญเข้าร่วมสถานที่ดูแล</h2>
            <p>สวัสดี,</p>
            <p>
            <strong>{inviter_name}</strong> ได้เชิญคุณเข้าร่วมสถานที่ดูแลในระบบ <b>SleepCare</b>
            </p>
            <div style="background:#f9fbfc; padding:15px; border-radius:8px; margin:20px 0;">
            <p style="margin:5px 0;"><strong>สถานที่:</strong> {facility_name}</p>
            <p style="margin:5px 0;"><strong>บทบาทที่ได้รับ:</strong> {role_name}</p>
            <p style="margin:5px 0; color:#d32f2f;">
                <strong>ลิงก์หมดอายุ:</strong> {expires_at}
            </p>
            </div>
            <div style="text-align:center; margin:30px 0;">
            <a href="{share_url}"
                style="
                    display:inline-block;
                    padding:14px 22px;
                    background-color:#4CAF50;
                    color:white;
                    text-decoration:none;
                    border-radius:8px;
                    font-weight:bold;
                    font-size:15px;
                ">
                ยืนยันเข้าร่วมสถานที่
            </a>
            </div>
            <p style="font-size:14px; color:#555;">
            เมื่อยืนยันแล้ว คุณจะสามารถเข้าถึงข้อมูล ห้อง และผู้ป่วยที่เกี่ยวข้องกับสถานที่นี้ได้ตามสิทธิ์ของคุณ
            </p>
            <hr style="margin:30px 0; border:none; border-top:1px solid #eee;">
            <p style="font-size:12px; color:#999;">
            หากคุณไม่ได้คาดหวังคำเชิญนี้ กรุณาละเว้นอีเมลฉบับนี้<br>
            ระบบ SleepCare | อีเมลนี้ถูกส่งโดยอัตโนมัติ
            </p>
        </div>
        </body>
        </html>
        """
        msg["Subject"] = "คำเชิญเข้าร่วมสถานที่ดูแลใน SleepCare"
        msg["From"] = EMAIL_HOST
        msg["To"] = email
        msg.set_content(f"""
        คุณได้รับคำเชิญเข้าร่วมสถานที่ในระบบ SleepCare
        ผู้เชิญ: {inviter_name}
        สถานที่: {facility_name}
        บทบาทที่ได้รับ: {role_name}
        ลิงก์หมดอายุ: {expires_at}
        คลิกเพื่อยืนยัน:
        {share_url}
        """)
        msg.add_alternative(html_content, subtype="html")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                smtp.send_message(msg)
            return "ส่งอีเมลเชิญเข้าร่วมสถานที่สำเร็จแล้ว!"
        except Exception as e:
            print("[DEV] Facility share email error:", email, share_url)
            return "ไม่สามารถส่งอีเมลได้"
        
    @staticmethod
    def send_new_device_data_to_email(email: str, payload: dict):
        msg = EmailMessage()
        facility_name = payload.get("facility_name")
        room_name = payload.get("room_name")
        device_id = payload.get("device_id")
        device_token = payload.get("device_token")
        url = payload.get("URL")
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color:#f4f6f8; padding:20px;">
                <div style="max-width:600px; margin:auto; background:white; padding:24px; border-radius:8px;">
                    <h2 style="color:#2c3e50; margin-bottom:10px;">
                        อุปกรณ์ใหม่ถูกสร้างเรียบร้อยแล้ว
                    </h2>
                    <p style="color:#555; margin-bottom:20px;">
                        สถานที่: <strong>{facility_name}</strong><br>
                        ห้อง: <strong>{room_name}</strong>
                    </p>
                    <p style="color:#555;">
                        กรุณานำข้อมูลด้านล่างไปตั้งค่าใน Raspberry Pi ของคุณ:
                    </p>
                    <div style="background:#f1f3f5; padding:16px; border-radius:8px; margin:20px 0;">
                        <p style="margin:6px 0;">
                            <strong>Device ID:</strong> {device_id}
                        </p>
                        <p style="margin:6px 0;">
                            <strong>Token สำหรับเข้าสู่ระบบ:</strong>
                        </p>
                        <p style="
                            word-break: break-all;
                            background:#fff3f3;
                            padding:10px;
                            border-radius:6px;
                            color:#c62828;
                            font-weight:bold;
                        ">
                            {device_token}
                        </p>
                        <p style="margin:6px 0;">
                            <strong>URL สำหรับเข้าสู่ระบบ:</strong>
                        </p>
                        <p style="
                            word-break: break-all;
                            background:#fff3f3;
                            padding:10px;
                            border-radius:6px;
                            color:#c62828;
                            font-weight:bold;
                        ">
                            {url}
                        </p>
                    </div>
                    <p style="color:#777; font-size:13px;">
                        ⚠ โปรดเก็บ Device Token นี้เป็นความลับ และอย่าแชร์กับผู้อื่น
                    </p>
                    <p style="color:#999; font-size:12px; margin-top:30px;">
                        หากคุณไม่ได้เป็นผู้ดำเนินการ กรุณาติดต่อผู้ดูแลระบบทันที
                    </p>
                </div>
            </body>
        </html>
        """
        msg["Subject"] = f"ข้อมูลอุปกรณ์ใหม่ - ห้อง {room_name} ({facility_name})"
        msg["From"] = EMAIL_HOST
        msg["To"] = email
        msg.set_content("กรุณาเปิดอีเมลนี้ด้วยโปรแกรมที่รองรับ HTML")
        msg.add_alternative(html_content, subtype="html")
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                smtp.send_message(msg)
            return "ส่งข้อมูลอุปกรณ์ทางอีเมลสำเร็จแล้ว!"
        except Exception as e:
            print("[DEV] New device email error:", email, payload)
            return "ไม่สามารถส่งอีเมลได้"
        
    @staticmethod
    def send_alert(db: Session, alert: AlertLog, room: Room):
        facility = room.facility
        patient = db.query(Patient).filter(Patient.patient_id == alert.patient_id).first() if alert.patient_id else None
        
        recipient_emails = get_alert_recipients(db, facility.facility_id, alert.patient_id)
        if not recipient_emails:
            return

        users = db.query(User).filter(User.email.in_(recipient_emails), User.is_active == True).all()
        
        is_emergency = alert.severity == SeverityEnumClass.emergency
        subject = f"[{alert.severity.value.upper()}] {alert.message} - ห้อง {room.room_number}"

        for user in users:
            ack_link = f"{DEVTEST_URL}/alerts/acknowledge/{alert.alert_id}?user_id={user.user_id}"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding:20px; color:#333;">
                    <div style="max-width:600px; margin:auto; border:2px solid {'#e74c3c' if is_emergency else '#f39c12'}; border-radius:10px; padding:20px;">
                        <h2 style="color:{'#e74c3c' if is_emergency else '#f39c12'};">แจ้งเตือนระดับ {alert.severity.value}</h2>
                        <p>เรียนคุณ {user.first_name},</p>
                        <p><strong>สถานที่:</strong> {facility.facility_name}</p>
                        <p><strong>ห้อง:</strong> {room.room_number}</p>
                        <p><strong>ผู้ป่วย:</strong> {patient.first_name if patient else 'ไม่ระบุ'} {patient.last_name if patient else ''}</p>
                        <p><strong>รายละเอียด:</strong> {alert.message}</p>
                        <p><strong>เวลา:</strong> {alert.created_at.strftime('%d/%m/%Y %H:%M:%S')}</p>
                        {f'''
                        <div style="margin-top:30px; text-align:center;">
                            <a href="{ack_link}" 
                            style="background-color:#e74c3c; color:white; padding:12px 25px; text-decoration:none; border-radius:5px; font-weight:bold;">
                            คลิกเพื่อยืนยันการรับทราบเหตุการณ์
                            </a>
                        </div>
                        ''' if is_emergency else ''}
                    </div>
                </body>
            </html>
            """
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = EMAIL_HOST
            msg["To"] = user.email
            msg.add_alternative(html_content, subtype="html")
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(EMAIL_HOST, EMAIL_PASSWORD)
                    smtp.send_message(msg)
            except Exception as e:
                print(f"Failed to send email to {user.email}: {e}")