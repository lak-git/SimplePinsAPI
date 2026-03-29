from ..models import pin as model
from aiomysql import DictCursor
from datetime import date
from typing import Any, Optional, Tuple


async def create_pin(
    cursor: DictCursor, user_uuid: bytes, title: str, body: str, image_link: str
) -> Tuple[int, Any]:
    pin_id = await model.add_pin(cursor, user_uuid, title, body, image_link)
    record = await model.get_pin_created_at(cursor, pin_id)
    return pin_id, record["CreatedAt"]


async def get_pin(cursor: DictCursor, pin_id: int) -> Optional[dict]:
    return await model.get_pin_by_id(cursor, pin_id)


async def get_pins(
    cursor: DictCursor,
    author: Optional[str],
    title: Optional[str],
    created_at: Optional[date],
    sort_by: str,
    order: str,
) -> list[dict]:
    query_params = []
    conditions = ""

    if author:
        conditions += " AND u.Username = %s"
        query_params.append(author)
    if title:
        conditions += " AND p.Title LIKE %s"
        query_params.append(f"%{title}%")
    if created_at:
        conditions += " AND DATE(p.CreatedAt) = %s"
        query_params.append(created_at)

    allowed_sort_columns = {
        "title": "p.Title",
        "author": "u.Username",
        "created_at": "p.CreatedAt",
    }
    secure_sort_column = allowed_sort_columns.get(sort_by.lower(), "p.CreatedAt")
    secure_order = "ASC" if order.lower() == "asc" else "DESC"
    order_clause = f"{secure_sort_column} {secure_order}"

    return await model.get_pins(cursor, conditions, tuple(query_params), order_clause)


async def check_pin_ownership(cursor: DictCursor, pin_id: int) -> Optional[dict]:
    return await model.get_pin_ownership(cursor, pin_id)


async def update_pin(cursor: DictCursor, pin_id: int, update_data: dict):
    set_clauses = []
    query_params = []
    column_mapping = {"title": "Title", "body": "Body", "image_link": "ImageLink"}

    for field, value in update_data.items():
        db_column = column_mapping[field]
        set_clauses.append(f"{db_column} = %s")
        query_params.append(value)

    set_clause_string = ", ".join(set_clauses)
    query_params.append(pin_id)

    await model.update_pin(cursor, set_clause_string, tuple(query_params))


async def delete_pin(cursor: DictCursor, pin_id: int):
    await model.delete_pin(cursor, pin_id)
