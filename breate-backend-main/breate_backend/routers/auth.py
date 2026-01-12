from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from breate_backend.database import get_db
from breate_backend import models

# ---------------------------------------
# CONFIG
# ---------------------------------------
SECRET_KEY = "breate_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_hasher = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------
# REQUEST SCHEMAS
# ---------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


# ---------------------------------------
# UTILS
# ---------------------------------------
def get_password_hash(password: str):
    """Hash password with Argon2"""
    return pwd_hasher.hash(password)


def verify_password(plain: str, hashed: str):
    """Verify plain password against stored hash"""
    try:
        pwd_hasher.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Generate JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------
# ROUTES
# ---------------------------------------
@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user using JSON body (email, password, username)
    """
    existing_user = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(payload.password)
    new_user = models.User(
        email=payload.email,
        username=payload.username or payload.email.split("@")[0],
        password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully", "user": new_user.username}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password (returns JWT token)
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------
# AUTH HELPER (used in protected routes)
# ---------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Extracts and verifies the current user from a JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


