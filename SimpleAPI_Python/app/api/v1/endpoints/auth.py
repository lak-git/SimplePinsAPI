import jwt
import logging
from ....services import auth as service
from app.api.dependencies import get_db
from app.core.limiter import limiter
from app.schemas.token import TokenResponse, RefreshToken
from aiomysql import Connection, DictCursor
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def obtain_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: Connection = Depends(get_db),
) -> TokenResponse:
    async with conn.cursor(DictCursor) as cursor:
        invalid_username_password: bool = await service.check_invalid_username_password(
            cursor, form_data.username, form_data.password
        )
        if invalid_username_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            access_token, refresh_token, expires_in = await service.save_refresh_token(
                cursor, form_data.username
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Failed to store refresh token for user {form_data.username} at /tokens: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured when obtaining token.",
            )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
        )


@router.post("/refresh", response_model=TokenResponse)
async def renew_acess_token(
    request: RefreshToken, conn: Connection = Depends(get_db)
) -> TokenResponse:
    try:
        invalid_type, user_uuid = service.check_valid_token_type(
            request.refresh_token, "refresh"
        )
        if invalid_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token has expired.",
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT Decoding Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials!!",
        )

    async with conn.cursor(DictCursor) as cursor:
        token_not_found: bool = await service.check_rtoken_exists(
            cursor, request.refresh_token
        )
        if token_not_found:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token not found in database.",
            )
        revoked_token: bool = await service.check_rtoken_is_revoked(
            cursor, request.refresh_token
        )
        if revoked_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token is revoked.",
            )

    # TODO: Insert new Refresh Token and revoke old one.

    new_access_token, new_refresh_token, expires_in = service.renew_tokens(user_uuid)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )
