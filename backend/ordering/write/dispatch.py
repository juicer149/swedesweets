from dataclasses import dataclass
from typing import Callable

from ordering.domain.errors import OrderingError
from ordering.models import Order

from .actions import (
    cancel_order,
    mark_order_as_delivered,
    mark_order_as_packed,
    save_staff_order_progress,
)


@dataclass(frozen=True, slots=True)
class StaffOrderActionSpec:
    """
    Small dispatch spec for one supported staff order action.

    This keeps the mapping between:
    - submitted action name
    - write-layer handler
    - success message

    explicit and easy to extend.
    """

    handler: Callable[..., Order]
    success_message: str


STAFF_ORDER_ACTIONS: dict[str, StaffOrderActionSpec] = {
    "save": StaffOrderActionSpec(
        handler=save_staff_order_progress,
        success_message="Notes saved.",
    ),
    "mark_packed": StaffOrderActionSpec(
        handler=mark_order_as_packed,
        success_message="Order marked as packed.",
    ),
    "mark_delivered": StaffOrderActionSpec(
        handler=mark_order_as_delivered,
        success_message="Order marked as delivered.",
    ),
    "cancel_order": StaffOrderActionSpec(
        handler=cancel_order,
        success_message="Order cancelled.",
    ),
}


def dispatch_staff_order_action(*, action: str, order: Order, staff_notes: str) -> str:
    """
    Dispatch one submitted staff order action.

    Returns the success message associated with the action so the HTTP layer
    can stay thin and only be responsible for flashing feedback and redirecting.
    """
    spec = STAFF_ORDER_ACTIONS.get(action)

    if spec is None:
        raise OrderingError(f"Unsupported staff order action: {action}")

    spec.handler(order=order, staff_notes=staff_notes)
    return spec.success_message
