from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User
from app.utils.security import decode_access_token

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required")
    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, int(user_id)) if user_id.isdigit() else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def owned_paper(paper_id: int, user: CurrentUser, db: DbSession):
    from app.models.entities import Paper
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.owner_id == user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

