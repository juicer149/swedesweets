def is_product_visible(*, is_visible: bool) -> bool:
    """
    Minimal catalog rule for whether a product should appear in catalog UI.
    """
    return is_visible


def is_product_orderable(*, is_orderable: bool) -> bool:
    """
    Minimal catalog rule for whether a product may be ordered right now.
    """
    return is_orderable
