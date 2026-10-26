from decimal import Decimal

from common.cart_price_feedback import cart_price_feedback


def test_price_change_uses_exact_decimal_money_and_signed_labels():
    feedback = cart_price_feedback(Decimal("0.10"), Decimal("0.30"))
    assert feedback["subtotal_label"] == "€0.30"
    assert feedback["subtotal_delta_label"] == "+€0.20"
    reduced = cart_price_feedback(Decimal("0.30"), Decimal("0.10"))
    assert reduced["subtotal_delta_label"] == "−€0.20"


def test_unknown_subtotal_never_invents_a_change():
    assert cart_price_feedback(None, Decimal("4.00"))["subtotal_delta_label"] is None
    assert cart_price_feedback(Decimal("4.00"), None)["subtotal_label"] is None
    unchanged = cart_price_feedback(Decimal("4.00"), Decimal("4.00"))
    assert unchanged["subtotal_delta_label"] is None
