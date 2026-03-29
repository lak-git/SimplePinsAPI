import logging
from ....services import pin as service
from app.api.dependencies import get_db, get_current_user
from app.schemas.pin import PinCreate, PinResponse, PinListResponse, PinUpdate
from aiomysql import Connection, DictCursor
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import Optional


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PinResponse)
async def create_pin(
    pin_in: PinCreate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
) -> PinResponse:
    async with conn.cursor(DictCursor) as cursor:
        try:
            pin_id, created_at = await service.create_pin(
                cursor,
                current_user["user_uuid"],
                pin_in.title,
                pin_in.body,
                pin_in.image_link,
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Failed to create pin for user {current_user['username']}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured while creating pin.",
            )

    return PinResponse(
        pin_id=pin_id,
        author=current_user["username"],
        title=pin_in.title,
        body=pin_in.body,
        image_link=pin_in.image_link,
        created_at=created_at,
    )


@router.get("/{pin_id}", status_code=status.HTTP_200_OK, response_model=PinResponse)
async def get_pin(pin_id: int, conn: Connection = Depends(get_db)) -> PinResponse:
    """
    Retrieves the details of a single pin by its ID. This endpoint is public.
    """
    async with conn.cursor(DictCursor) as cursor:
        pin_record = await service.get_pin(cursor, pin_id)

        pin_not_found: bool = not pin_record
        if pin_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pin with ID {pin_id} not found.",
            )

    return PinResponse(**pin_record)


@router.get("/", status_code=status.HTTP_200_OK, response_model=PinListResponse)
async def get_pins(
    author: Optional[str] = Query(None, description="Filter by author (username)"),
    title: Optional[str] = Query(None, description="Filter by exact or partial title"),
    created_at: Optional[date] = Query(
        None, description="Filter by exact creation date (YYYY-MM-DD)"
    ),
    sort_by: Optional[str] = Query(
        "created_at", description="Sort by: title, author, or created_at"
    ),
    order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    conn: Connection = Depends(get_db),
) -> PinListResponse:
    async with conn.cursor(DictCursor) as cursor:
        try:
            records = await service.get_pins(
                cursor, author, title, created_at, sort_by, order
            )
        except Exception as e:
            logger.error(f"Database Error during get_pins: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred.",
            )

    pin_responses = [PinResponse(**record) for record in records]
    return PinListResponse(pins=pin_responses)


@router.patch("/{pin_id}", status_code=status.HTTP_200_OK, response_model=PinResponse)
async def update_pin(
    pin_id: int,
    pin_in: PinUpdate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
) -> PinResponse:
    async with conn.cursor(DictCursor) as cursor:
        existing_pin = await service.check_pin_ownership(cursor, pin_id)

        pin_does_not_exist: bool = not existing_pin
        if pin_does_not_exist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pin with ID {pin_id} not found.",
            )

        not_users_pin: bool = existing_pin["UserUUID"] != current_user["user_uuid"]
        if not_users_pin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this pin.",
            )

        update_data = pin_in.model_dump(exclude_unset=True)
        no_pin_update: bool = not update_data
        if no_pin_update:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update.",
            )

        try:
            await service.update_pin(cursor, pin_id, update_data)
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(f"Database Error during update_pin: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred while updating the pin.",
            )

        updated_record = await service.get_pin(cursor, pin_id)

    return PinResponse(**updated_record)


@router.delete("/{pin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pin(
    pin_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
):
    async with conn.cursor(DictCursor) as cursor:
        existing_pin = await service.check_pin_ownership(cursor, pin_id)

        pin_not_found: bool = not existing_pin
        if pin_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pin with ID {pin_id} not found.",
            )

        not_users_pin: bool = existing_pin["UserUUID"] != current_user["user_uuid"]
        if not_users_pin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this pin.",
            )

        try:
            await service.delete_pin(cursor, pin_id)
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.error(f"Database Error during delete_pin: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occurred while deleting the pin.",
            )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
