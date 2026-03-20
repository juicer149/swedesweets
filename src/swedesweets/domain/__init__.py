from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, time, timezone
from enum import StrEnum
from typing import Iterable
from uuid import UUID, uuid4


# ============================================================
# Errors
# ============================================================


class DomainError(Exception):
    """Base domain exception."""


class ValidationError(DomainError):
    """Raised when an entity or value object has invalid state."""


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""


# ============================================================
# Roles and statuses
# ============================================================


class BusinessRole(StrEnum):
    STORE = "store"
    SUPPLIER = "supplier"


class SystemRole(StrEnum):
    ADMIN = "admin"
    OPERATOR = "operator"


class StoreRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrderItemStatus(StrEnum):
    PENDING = "pending"
    PARTIAL = "partial"
    DELIVERED = "delivered"


class OrderStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"


# ============================================================
# Value objects
# ============================================================


@dataclass(frozen=True, slots=True)
class DeliveryWindow:
    """Preferred delivery time window for a store."""

    weekday: int  # 0=Monday ... 6=Sunday
    start: time
    end: time

    def __post_init__(self) -> None:
        if not 0 <= self.weekday <= 6:
            raise ValidationError("weekday must be between 0 and 6")

        if self.start >= self.end:
            raise ValidationError("delivery window start must be before end")


# ============================================================
# Core entities
# ============================================================


@dataclass(frozen=True, slots=True)
class User:
    """
    A system user.

    business_role answers: who are you in the business?
    system_role answers: what technical/system privileges do you have?
    """

    id: UUID
    username: str
    password_hash: bytes
    business_role: BusinessRole
    system_role: SystemRole

    def __post_init__(self) -> None:
        if not self.username.strip():
            raise ValidationError("username required")

        if not self.password_hash:
            raise ValidationError("password_hash required")


@dataclass(frozen=True, slots=True)
class Product:
    """
    A product in the supplier catalog.

    category is intentionally a str for now.
    That keeps v0.1 flexible while still allowing normalization.
    """

    id: UUID
    sku: str
    name: str
    category: str
    unit: str  # e.g. "kg", "box", "bag"

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValidationError("product sku required")

        if not self.name.strip():
            raise ValidationError("product name required")

        normalized_category = self.category.strip().lower()
        if not normalized_category:
            raise ValidationError("product category required")

        normalized_unit = self.unit.strip().lower()
        if not normalized_unit:
            raise ValidationError("product unit required")

        object.__setattr__(self, "category", normalized_category)
        object.__setattr__(self, "unit", normalized_unit)


@dataclass(frozen=True, slots=True)
class Store:
    """A retail store supplied by SwedeSweets."""

    id: UUID
    name: str
    address: str
    contact_name: str | None = None
    contact_email: str | None = None
    delivery_window: DeliveryWindow | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("store name required")

        if not self.address.strip():
            raise ValidationError("store address required")


# ============================================================
# Store onboarding
# ============================================================


@dataclass(frozen=True, slots=True)
class StoreAccountRequest:
    """
    A request from a store asking for an account.

    State transitions:
        pending -> approved
        pending -> rejected

    No other transitions are allowed.
    """

    id: UUID
    requested_at: datetime
    store_name: str
    contact_name: str
    contact_email: str
    address: str
    #phone_number: str | None = None
    status: StoreRequestStatus = StoreRequestStatus.PENDING

    def __post_init__(self) -> None:
        if self.requested_at.tzinfo is None:
            raise ValidationError("requested_at must be timezone-aware")

        if not self.store_name.strip():
            raise ValidationError("store_name required")

        if not self.contact_name.strip():
            raise ValidationError("contact_name required")

        if not self.contact_email.strip():
            raise ValidationError("contact_email required")

        if not self.address.strip():
            raise ValidationError("address required")

    def approve(self) -> StoreAccountRequest:
        if self.status is not StoreRequestStatus.PENDING:
            raise BusinessRuleError("only pending requests can be approved")

        return replace(self, status=StoreRequestStatus.APPROVED)

    def reject(self) -> StoreAccountRequest:
        if self.status is not StoreRequestStatus.PENDING:
            raise BusinessRuleError("only pending requests can be rejected")

        return replace(self, status=StoreRequestStatus.REJECTED)


# ============================================================
# Assortment templates and store assortment
# ============================================================


@dataclass(frozen=True, slots=True)
class AssortmentTemplateItem:
    """
    An item in a reusable assortment template.

    par_level is the nominal/default refill quantity target.
    """

    product_id: UUID
    par_level: int = 1
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.par_level <= 0:
            raise ValidationError("par_level must be > 0")


@dataclass(frozen=True, slots=True)
class AssortmentTemplate:
    """
    A reusable assortment template.

    Important: templates are copied into store-specific assortment records.
    They are not shared mutable references.
    """

    id: UUID
    name: str
    items: tuple[AssortmentTemplateItem, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationError("template name required")

        if not self.items:
            raise ValidationError("template must contain at least one item")

        _ensure_unique_product_ids(item.product_id for item in self.items)


@dataclass(frozen=True, slots=True)
class StoreProduct:
    """
    A store-specific assortment record.

    This is copied data owned by the store assortment, not just a reference
    to a template item.
    """

    id: UUID
    store_id: UUID
    product_id: UUID
    par_level: int = 1
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.par_level <= 0:
            raise ValidationError("par_level must be > 0")


@dataclass(frozen=True, slots=True)
class StoreAssortment:
    """
    The assortment for a specific store.

    This is effectively the store's local view of which products it can order.
    """

    store_id: UUID
    items: tuple[StoreProduct, ...]

    def __post_init__(self) -> None:
        _ensure_unique_product_ids(item.product_id for item in self.items)

        for item in self.items:
            if item.store_id != self.store_id:
                raise ValidationError(
                    "all assortment items must belong to the same store"
                )

    def includes_product(self, product_id: UUID) -> bool:
        return any(
            item.product_id == product_id and item.enabled
            for item in self.items
        )

    def add_product(
        self,
        product_id: UUID,
        *,
        par_level: int = 1,
        enabled: bool = True,
    ) -> StoreAssortment:
        if any(item.product_id == product_id for item in self.items):
            raise BusinessRuleError("product already exists in store assortment")

        new_item = StoreProduct(
            id=uuid4(),
            store_id=self.store_id,
            product_id=product_id,
            par_level=par_level,
            enabled=enabled,
        )

        return StoreAssortment(
            store_id=self.store_id,
            items=self.items + (new_item,),
        )

    def remove_product(self, product_id: UUID) -> StoreAssortment:
        new_items = tuple(
            item for item in self.items if item.product_id != product_id
        )

        if len(new_items) == len(self.items):
            raise BusinessRuleError("product not found in store assortment")

        return StoreAssortment(
            store_id=self.store_id,
            items=new_items,
        )

    def enable_product(self, product_id: UUID) -> StoreAssortment:
        return self._set_enabled(product_id, True)

    def disable_product(self, product_id: UUID) -> StoreAssortment:
        return self._set_enabled(product_id, False)

    def _set_enabled(self, product_id: UUID, enabled: bool) -> StoreAssortment:
        found = False
        new_items: list[StoreProduct] = []

        for item in self.items:
            if item.product_id == product_id:
                found = True
                new_items.append(
                    StoreProduct(
                        id=item.id,
                        store_id=item.store_id,
                        product_id=item.product_id,
                        par_level=item.par_level,
                        enabled=enabled,
                    )
                )
            else:
                new_items.append(item)

        if not found:
            raise BusinessRuleError("product not found in store assortment")

        return StoreAssortment(
            store_id=self.store_id,
            items=tuple(new_items),
        )


# ============================================================
# Orders
# ============================================================


@dataclass(frozen=True, slots=True)
class OrderItem:
    """A single requested product line in an order."""

    id: UUID
    product_id: UUID
    requested_qty: int
    delivered_qty: int = 0

    def __post_init__(self) -> None:
        if self.requested_qty <= 0:
            raise ValidationError("requested_qty must be > 0")

        if self.delivered_qty < 0:
            raise ValidationError("delivered_qty cannot be negative")

        if self.delivered_qty > self.requested_qty:
            raise ValidationError("delivered_qty cannot exceed requested_qty")

    @property
    def status(self) -> OrderItemStatus:
        if self.delivered_qty == 0:
            return OrderItemStatus.PENDING

        if self.delivered_qty < self.requested_qty:
            return OrderItemStatus.PARTIAL

        return OrderItemStatus.DELIVERED

    def deliver(self, qty: int) -> OrderItem:
        if qty <= 0:
            raise ValidationError("delivery quantity must be > 0")

        new_delivered_qty = self.delivered_qty + qty
        if new_delivered_qty > self.requested_qty:
            raise BusinessRuleError("cannot deliver more than requested quantity")

        return OrderItem(
            id=self.id,
            product_id=self.product_id,
            requested_qty=self.requested_qty,
            delivered_qty=new_delivered_qty,
        )


@dataclass(frozen=True, slots=True)
class Order:
    """
    A replenishment order from a store.

    Order status is derived from item statuses instead of being stored
    separately as its own mutable source of truth.
    """

    id: UUID
    store_id: UUID
    created_at: datetime
    items: tuple[OrderItem, ...]

    def __post_init__(self) -> None:
        if self.created_at.tzinfo is None:
            raise ValidationError("created_at must be timezone-aware")

        if not self.items:
            raise ValidationError("order must contain at least one item")

        _ensure_unique_product_ids(item.product_id for item in self.items)

    @property
    def status(self) -> OrderStatus:
        statuses = {item.status for item in self.items}

        if statuses == {OrderItemStatus.PENDING}:
            return OrderStatus.PENDING

        if statuses == {OrderItemStatus.DELIVERED}:
            return OrderStatus.COMPLETED

        if OrderItemStatus.PENDING in statuses:
            return OrderStatus.IN_PROGRESS

        return OrderStatus.PARTIAL

    def total_requested_qty(self) -> int:
        return sum(item.requested_qty for item in self.items)

    def total_delivered_qty(self) -> int:
        return sum(item.delivered_qty for item in self.items)

    def deliver_item(self, product_id: UUID, qty: int) -> Order:
        found = False
        new_items: list[OrderItem] = []

        for item in self.items:
            if item.product_id == product_id:
                found = True
                new_items.append(item.deliver(qty))
            else:
                new_items.append(item)

        if not found:
            raise BusinessRuleError("product is not part of this order")

        return Order(
            id=self.id,
            store_id=self.store_id,
            created_at=self.created_at,
            items=tuple(new_items),
        )


# ============================================================
# Domain factories / services
# ============================================================


def create_store_user(*, username: str, password_hash: bytes) -> User:
    return User(
        id=uuid4(),
        username=username,
        password_hash=password_hash,
        business_role=BusinessRole.STORE,
        system_role=SystemRole.OPERATOR,
    )


def create_supplier_user(
    *,
    username: str,
    password_hash: bytes,
    system_role: SystemRole = SystemRole.OPERATOR,
) -> User:
    return User(
        id=uuid4(),
        username=username,
        password_hash=password_hash,
        business_role=BusinessRole.SUPPLIER,
        system_role=system_role,
    )


def create_admin_user(*, username: str, password_hash: bytes) -> User:
    return User(
        id=uuid4(),
        username=username,
        password_hash=password_hash,
        business_role=BusinessRole.SUPPLIER,
        system_role=SystemRole.ADMIN,
    )


def create_store_from_approved_request(request: StoreAccountRequest) -> Store:
    if request.status is not StoreRequestStatus.APPROVED:
        raise BusinessRuleError(
            "store can only be created from an approved request"
        )

    return Store(
        id=request.id,
        name=request.store_name,
        address=request.address,
        contact_name=request.contact_name,
        contact_email=request.contact_email,
    )


def create_empty_store_assortment(store_id: UUID) -> StoreAssortment:
    return StoreAssortment(store_id=store_id, items=())


def copy_template_to_store_assortment(
    *,
    store_id: UUID,
    template: AssortmentTemplate,
) -> StoreAssortment:
    items = tuple(
        StoreProduct(
            id=uuid4(),
            store_id=store_id,
            product_id=template_item.product_id,
            par_level=template_item.par_level,
            enabled=template_item.enabled,
        )
        for template_item in template.items
    )

    return StoreAssortment(
        store_id=store_id,
        items=items,
    )


def create_order(
    *,
    store_id: UUID,
    assortment: StoreAssortment,
    requested_items: Iterable[tuple[UUID, int]],
    created_at: datetime | None = None,
) -> Order:
    item_pairs = tuple(requested_items)

    if not item_pairs:
        raise ValidationError("order must contain at least one requested item")

    order_items: list[OrderItem] = []

    for product_id, requested_qty in item_pairs:
        if not assortment.includes_product(product_id):
            raise BusinessRuleError(
                "store cannot order product outside its assortment"
            )

        order_items.append(
            OrderItem(
                id=uuid4(),
                product_id=product_id,
                requested_qty=requested_qty,
            )
        )

    return Order(
        id=uuid4(),
        store_id=store_id,
        created_at=created_at or datetime.now(timezone.utc),
        items=tuple(order_items),
    )


def create_restock_order_from_flags(
    *,
    store_id: UUID,
    assortment: StoreAssortment,
    refill_product_ids: Iterable[UUID],
    default_qty: int = 1,
    created_at: datetime | None = None,
) -> Order:
    if default_qty <= 0:
        raise ValidationError("default_qty must be > 0")

    requested_items = tuple(
        (product_id, default_qty)
        for product_id in refill_product_ids
    )

    return create_order(
        store_id=store_id,
        assortment=assortment,
        requested_items=requested_items,
        created_at=created_at,
    )


# ============================================================
# Internal helpers
# ============================================================

def _ensure_unique_product_ids(product_ids: Iterable[UUID]) -> None:
    seen: set[UUID] = set()

    for product_id in product_ids:
        if product_id in seen:
            raise ValidationError("duplicate product_id is not allowed")
        seen.add(product_id)
