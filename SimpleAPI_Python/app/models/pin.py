from aiomysql import DictCursor
from typing import Optional


INSERT_QUERY = """
INSERT INTO Pin (UserUUID, Title, Body, ImageLink)
VALUES (%s, %s, %s, %s)
"""
FETCH_CREATED_AT_QUERY = "SELECT CreatedAt FROM Pin WHERE PinID = %s"

BASE_GET_PIN_QUERY = """
SELECT 
    p.PinID AS pin_id, 
    u.Username AS author, 
    p.Title AS title, 
    p.Body AS body, 
    p.ImageLink AS image_link, 
    p.CreatedAt AS created_at
FROM Pin p
JOIN User u ON p.UserUUID = u.UserUUID
"""
GET_SINGLE_PIN_QUERY = f"{BASE_GET_PIN_QUERY} WHERE p.PinID = %s"
OWNERSHIP_CHECK_QUERY = "SELECT UserUUID FROM Pin WHERE PinID = %s"
DELETE_QUERY = "DELETE FROM Pin WHERE PinID = %s"


async def add_pin(
    cursor: DictCursor, user_uuid: bytes, title: str, body: str, image_link: str
) -> Optional[int]:
    await cursor.execute(INSERT_QUERY, (user_uuid, title, body, image_link))
    return cursor.lastrowid


async def get_pin_created_at(cursor: DictCursor, pin_id: int) -> dict:
    await cursor.execute(FETCH_CREATED_AT_QUERY, (pin_id,))
    return await cursor.fetchone()


async def get_pin_by_id(cursor: DictCursor, pin_id: int) -> dict:
    await cursor.execute(GET_SINGLE_PIN_QUERY, (pin_id,))
    return await cursor.fetchone()


async def get_pins(
    cursor: DictCursor, conditions: str, params: tuple, order_clause: str
) -> list[dict]:
    query = f"{BASE_GET_PIN_QUERY} WHERE 1=1 {conditions} ORDER BY {order_clause}"
    await cursor.execute(query, params)
    return await cursor.fetchall()


async def get_pin_ownership(cursor: DictCursor, pin_id: int) -> dict:
    await cursor.execute(OWNERSHIP_CHECK_QUERY, (pin_id,))
    return await cursor.fetchone()


async def update_pin(cursor: DictCursor, set_clause: str, params: tuple):
    query = f"UPDATE Pin SET {set_clause} WHERE PinID = %s"
    await cursor.execute(query, params)


async def delete_pin(cursor: DictCursor, pin_id: int):
    await cursor.execute(DELETE_QUERY, (pin_id,))
