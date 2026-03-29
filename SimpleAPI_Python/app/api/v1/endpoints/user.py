import logging
from aiomysql import Connection, DictCursor
from ....services import user as service
from app.api.dependencies import get_db
from app.core.limiter import limiter
from app.schemas.user import UserCreate, UserRegistrationResponse
from fastapi import APIRouter, Depends, HTTPException, status, Request


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=UserRegistrationResponse
)
@limiter.limit("5/minute")  # 5 accounts per minute
async def register_user(
    request: Request, user_in: UserCreate, conn: Connection = Depends(get_db)
) -> UserRegistrationResponse:
    async with conn.cursor(DictCursor) as cursor:
        existing_user: bool = await service.check_user_exists(cursor, user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User already registered"
            )

        try:
            (
                user_uuid,
                access_token,
                refresh_token,
                expires_in,
            ) = await service.register_user(cursor, user_in.username, user_in.password)
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Database Error occured during registration for {user_in.username}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured during registration.",
            )

        return UserRegistrationResponse(
            user_id=user_uuid,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
