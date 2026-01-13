from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from breate_backend.database import get_db
from breate_backend import models
from breate_backend.auth import SECRET_KEY, ALGORITHM, verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Extracts and validates the current user from JWT token.
    Token contains email in 'sub' field (from /users/login endpoint).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_access_token(token)
        # Check token type if present
        if payload.get("type") and payload.get("type") != "access":
            raise credentials_exception
        
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception

    except (JWTError, HTTPException):
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        raise credentials_exception

    return user
