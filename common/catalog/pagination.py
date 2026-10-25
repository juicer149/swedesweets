"""Small HTML batches and a text-only search index for both sales channels."""

from __future__ import annotations

from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.cache import patch_cache_control

PAGE_SIZE = 12


def catalog_response(request, *, product_cards, template_name):
    cards = tuple(product_cards)
    if request.GET.get("catalog_cards") == "1":
        try:
            ids = [int(value) for value in request.GET.get("ids", "").split(",")]
        except ValueError:
            return HttpResponseBadRequest("Invalid product ids.")
        if not 1 <= len(ids) <= PAGE_SIZE or len(set(ids)) != len(ids) or min(ids) < 1:
            return HttpResponseBadRequest("Invalid product ids.")
        allowed = {card.product_id: card for card in cards}
        selected = [allowed[pk] for pk in ids if pk in allowed]
        response = JsonResponse(
            {
                "html": render_to_string(
                    "includes/catalog/cards.html",
                    {
                        "product_cards": selected,
                        "csrf_token": get_token(request),
                    },
                    request=request,
                ),
                "ids": [card.product_id for card in selected],
            }
        )
        patch_cache_control(response, private=True, no_store=True)
        return response
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError as error:
        raise Http404("Invalid catalog page.") from error
    if page < 1 or (page > 1 and (page - 1) * PAGE_SIZE >= len(cards)):
        raise Http404("Invalid catalog page.")
    return render(
        request,
        template_name,
        {
            "product_cards": cards,
            "initial_product_cards": cards[(page - 1) * PAGE_SIZE : page * PAGE_SIZE],
            "catalog_index": [
                {
                    "id": card.product_id,
                    "category": card.category_key,
                    "search": card.search_text,
                }
                for card in cards
            ],
            "catalog_page_size": PAGE_SIZE,
            "catalog_previous_page": page - 1 if page > 1 else None,
            "catalog_next_page": page + 1 if page * PAGE_SIZE < len(cards) else None,
        },
    )
