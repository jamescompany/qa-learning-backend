from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int]
    prev_page: Optional[int]


def paginate(
    query,
    page: int = 1,
    limit: int = 20,
    max_limit: int = 100
) -> tuple:
    """
    Apply pagination to a SQLAlchemy query
    
    Returns:
        tuple: (paginated_items, total_count)
    """
    # Ensure valid pagination parameters
    page = max(1, page)
    limit = min(limit, max_limit)
    offset = (page - 1) * limit
    
    # Get total count
    total = query.count()
    
    # Get paginated items
    items = query.offset(offset).limit(limit).all()
    
    return items, total


def create_pagination_response(
    items: List[T],
    total: int,
    page: int,
    limit: int
) -> PaginatedResponse[T]:
    """Create a paginated response with metadata"""
    pages = ceil(total / limit) if limit > 0 else 1
    has_next = page < pages
    has_prev = page > 1
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev,
        next_page=page + 1 if has_next else None,
        prev_page=page - 1 if has_prev else None
    )


def get_pagination_params(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    default_limit: int = 20,
    max_limit: int = 100
) -> Dict[str, int]:
    """Get normalized pagination parameters"""
    page = max(1, page or 1)
    limit = min(limit or default_limit, max_limit)
    offset = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "offset": offset
    }


def create_pagination_links(
    base_url: str,
    page: int,
    limit: int,
    total: int
) -> Dict[str, Optional[str]]:
    """Create pagination links for REST API"""
    pages = ceil(total / limit) if limit > 0 else 1
    
    links = {
        "self": f"{base_url}?page={page}&limit={limit}",
        "first": f"{base_url}?page=1&limit={limit}",
        "last": f"{base_url}?page={pages}&limit={limit}",
        "next": None,
        "prev": None
    }
    
    if page < pages:
        links["next"] = f"{base_url}?page={page + 1}&limit={limit}"
    
    if page > 1:
        links["prev"] = f"{base_url}?page={page - 1}&limit={limit}"
    
    return links


class CursorPagination:
    """Cursor-based pagination for large datasets"""
    
    @staticmethod
    def encode_cursor(value: Any) -> str:
        """Encode a cursor value"""
        import base64
        import json
        
        cursor_data = json.dumps({"value": str(value)})
        return base64.b64encode(cursor_data.encode()).decode()
    
    @staticmethod
    def decode_cursor(cursor: str) -> Any:
        """Decode a cursor value"""
        import base64
        import json
        
        try:
            cursor_data = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_data)["value"]
        except:
            return None
    
    @staticmethod
    def paginate_with_cursor(
        query,
        cursor: Optional[str] = None,
        limit: int = 20,
        order_field: str = "id"
    ) -> Dict[str, Any]:
        """Apply cursor-based pagination to a query"""
        if cursor:
            cursor_value = CursorPagination.decode_cursor(cursor)
            if cursor_value:
                query = query.filter(
                    getattr(query.model, order_field) > cursor_value
                )
        
        # Get limit + 1 to check if there are more items
        items = query.limit(limit + 1).all()
        
        has_more = len(items) > limit
        if has_more:
            items = items[:-1]
        
        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            next_cursor = CursorPagination.encode_cursor(
                getattr(last_item, order_field)
            )
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more
        }