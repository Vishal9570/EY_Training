from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/orders", tags=["Orders"])


# ── CREATE ──────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a new order",
)
def create_order(
    payload: OrderCreate,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:
    """
    Accepts a deeply nested `OrderCreate` body:
    - **customer** → name, email, phone, shipping_address (nested)
    - **items[]**  → each item embeds a full **product** object
    - **payment_method** enum
    - **notes** (optional)

    Returns an `OrderResponse` which *extends* the stored order with a
    computed **summary** block (subtotal, discounts, grand total, item count).
    """
    order = Order(**payload.model_dump())
    saved = repo.save(order)
    return OrderResponse.from_order(saved)


# ── READ ALL ────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List all orders",
)
def list_orders(
    repo: OrderRepository = Depends(get_repository),
) -> List[OrderResponse]:
    return [OrderResponse.from_order(o) for o in repo.list_all()]


# ── READ ONE ────────────────────────────────────────────────────────────────

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a single order by ID",
)
def get_order(
    order_id: UUID,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:
    order = repo.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )
    return OrderResponse.from_order(order)


# ── UPDATE STATUS (PATCH) ────────────────────────────────────────────────────

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
def update_order_status(
    order_id: UUID,
    new_status: OrderStatus,
    repo: OrderRepository = Depends(get_repository),
) -> OrderResponse:
    """
    Extension task: PATCH only the `status` field.
    Demonstrates partial update without re-validating the whole body.
    """
    order = repo.update_status(order_id, new_status)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )
    return OrderResponse.from_order(order)


# ── DELETE ──────────────────────────────────────────────────────────────────

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel / delete an order",
)
def delete_order(
    order_id: UUID,
    repo: OrderRepository = Depends(get_repository),
) -> None:
    if not repo.delete(order_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found.",
        )


