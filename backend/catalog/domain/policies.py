def is_product_orderable(*, is_active: bool) -> bool:
    """
    Minimal catalog rule for whether a product may be ordered.

    Right now a product is orderable if it is active.
    Future rules can be added here without changing callers.
    """
    return is_active
