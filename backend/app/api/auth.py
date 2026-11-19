from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import CurrentUser, DbSession
from app.models.entities import User
from app.schemas import TokenOut, UserLogin, UserOut, UserRegister
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: DbSession):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id)), user=user)


@router.post("/login", response_model=TokenOut)
def login(payload: UserLogin, db: DbSession):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenOut(access_token=create_access_token(str(user.id)), user=user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user

