from accounts.models import Store


def public_store_locator_entries():
    """
    Return stores suitable for the public 'Find sweets' page.

    This is a read selector, not business logic:
    - only active stores are shown
    - stores must have a usable address
    - results are ordered for stable display

    The selector returns a lightweight read projection instead of exposing
    full model instances to the template layer when only public display data
    is needed.
    """
    return (
        Store.objects
        .filter(is_active=True)
        .exclude(address__isnull=True)
        .exclude(address="")
        .order_by("name")
        .values("id", "name", "address")
    )
