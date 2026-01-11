from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Твой конфиг базы (лежит в корне)
from db_config import get_db
from core.config import settings
from .schemas import Token, UserCreate, UserRead, UserUpdate, UserProfile
from .models import User
from .security import create_access_token, get_password_hash, verify_password 
from .dependencies import get_current_active_user, require_admin
from .service import get_all_users, update_user, delete_user, get_user_by_id, get_user_profile_stats

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    # 1. Ищем пользователя
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # 2. Проверяем пароль прямо тут
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Генерируем токен
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Важно: добавляем роль в токен
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users", response_model=UserRead)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Проверяем дубликаты
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    # Role handling: ensure it's correct (Enum handles validation, but we can access value)
    # The requirement was to ensure role is converted to lowercase, which the Enum value already is.
    
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role, 
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return get_all_users(db, skip=skip, limit=limit)

@router.get("/users/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return get_user_by_id(db, user_id)

@router.put("/users/{user_id}", response_model=UserRead)
def update_user_endpoint(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return update_user(db, user_id=user_id, user_update=user_update)

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    delete_user(db, user_id=user_id)

@router.get("/profile", response_model=UserProfile)
def read_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return get_user_profile_stats(db, current_user.id)

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    return current_user