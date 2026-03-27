import logging
from app.api.dependencies import get_db, get_current_user
from app.schemas.pin import PinCreate, PinResponse
from aiomysql import Connection, DictCursor
from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter()
logger = logging.getLogger(__name__)

INSERT_QUERY = """
INSERT INTO Pin (UserUUID, Title, Body, ImageLink)
VALUES (%s, %s, %s, %s)
"""
FETCH_QUERY = "SELECT CreatedAt FROM Pin WHERE PinID = %s"


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PinResponse)
async def create_pin(
    pin_in: PinCreate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db),
) -> PinResponse:
    async with conn.cursor(DictCursor) as cursor:
        try:
            await cursor.execute(
                INSERT_QUERY,
                (
                    current_user["user_uuid"],
                    pin_in.title,
                    pin_in.body,
                    pin_in.image_link,
                ),
            )
            await conn.commit()
            pin_id: int = cursor.lastrowid
        except Exception as e:
            await conn.rollback()
            logger.error(
                f"Failed to create pin for user {current_user['username']}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A database error occured while creating pin.",
            )

        await cursor.execute(FETCH_QUERY, (pin_id))
        pin_record = await cursor.fetchone()

    return PinResponse(
        pin_id=pin_id,
        author=current_user["username"],
        title=pin_in.title,
        body=pin_in.body,
        image_link=pin_in.image_link,
        created_at=pin_record["CreatedAt"],
    )


GET_PIN_QUERY = """
SELECT 
    p.PinID AS pin_id, 
    u.Username AS author, 
    p.Title AS title, 
    p.Body AS body, 
    p.ImageLink AS image_link, 
    p.CreatedAt AS created_at
FROM Pin p
JOIN User u ON p.UserUUID = u.UserUUID
WHERE p.PinID = %s
"""


@router.get("/{pin_id}", status_code=status.HTTP_200_OK, response_model=PinResponse)
async def get_pin(pin_id: int, conn: Connection = Depends(get_db)):
    """
    Retrieves the details of a single pin by its ID. This endpoint is public.
    """
    async with conn.cursor(DictCursor) as cursor:
        await cursor.execute(GET_PIN_QUERY, (pin_id,))
        pin_record = await cursor.fetchone()

        pin_not_found: bool = not pin_record
        if pin_not_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pin with ID {pin_id} not found.",
            )

    # Dictionary unpacking
    return PinResponse(**pin_record)
