from __future__ import annotations

from accounts.roles import Capability

VIEW_CAPABILITIES = {
    "business_portal:index": Capability.VIEW_BUSINESS_PORTAL,
    "business_portal:edit_store": Capability.EDIT_OWN_ACCOUNT,
    "business_portal:orders": Capability.VIEW_OWN_ORDERS,
    "business_portal:order_detail": Capability.VIEW_OWN_ORDERS,
    "business_portal:repeat_order": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:cart": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:navbar_cart_fragment": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:add_cart_offer": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:cart_review": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:set_cart_line_quantity": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:remove_cart_line": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:catalog": Capability.VIEW_BUSINESS_PORTAL,
    "business_portal:catalog_product": Capability.VIEW_BUSINESS_PORTAL,
    "business_portal:catalog_add_product": Capability.PLACE_BUSINESS_ORDERS,
    "business_portal:contact": Capability.VIEW_BUSINESS_PORTAL,
    "business_portal:faq": Capability.VIEW_BUSINESS_PORTAL,
}
