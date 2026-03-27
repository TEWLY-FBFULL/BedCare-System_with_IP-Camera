import secrets
from datetime import datetime, timedelta

def generate_token(exp_minutes=30):
    return secrets.token_urlsafe(32), datetime.utcnow() + timedelta(minutes=exp_minutes)
