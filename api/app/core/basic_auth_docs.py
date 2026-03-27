import time
import os
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from collections import defaultdict
from threading import Lock

security = HTTPBasic()
USERNAME = os.getenv("PGADMIN_DEFAULT_EMAIL")
PASSWORD = os.getenv("PGADMIN_DEFAULT_PASSWORD")

RATE_LIMIT = 5          
WINDOW_SECONDS = 60
attempts = defaultdict(list)
lock = Lock()

def rate_limit(request: Request):
    client_ip = request.client.host
    now = time.time()
    with lock:
        attempts[client_ip] = [
            t for t in attempts[client_ip]
            if now - t < WINDOW_SECONDS
        ]
        if len(attempts[client_ip]) >= RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Try again later."
            )
        attempts[client_ip].append(now)

def verify_credentials(
    request: Request,
    credentials: HTTPBasicCredentials = Depends(security)
):
    rate_limit(request)
    if not (
        credentials.username == USERNAME
        and credentials.password == PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )