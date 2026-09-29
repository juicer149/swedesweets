from __future__ import annotations

import json
from decimal import Decimal
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.parse import (
    quote,
    urlencode,
)
from urllib.request import (
    Request,
    urlopen,
)

from payments.contracts import (
    ExternalPaymentState,
    ExternalPaymentStatus,
    HostedPaymentError,
    HostedPaymentRequest,
    HostedPaymentSession,
)


SUMUP_API_BASE_URL = "https://api.sumup.com"
SUMUP_CHECKOUTS_PATH = "/v0.1/checkouts"


class SumUpPaymentError(HostedPaymentError):
    """Raised when communication with SumUp cannot be trusted."""


class SumUpHostedPaymentProvider:
    """Adapter between our payment contract and SumUp Online Payments."""

    def __init__(
        self,
        *,
        api_key: str,
        merchant_code: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        api_key = api_key.strip()
        merchant_code = merchant_code.strip()

        if not api_key:
            raise ValueError(
                "SumUp API key is required"
            )

        if not merchant_code:
            raise ValueError(
                "SumUp merchant code is required"
            )

        self._api_key = api_key
        self._merchant_code = merchant_code
        self._timeout_seconds = timeout_seconds

    def create_payment(
        self,
        *,
        request: HostedPaymentRequest,
    ) -> HostedPaymentSession:
        payload = {
            "checkout_reference": request.reference,
            "amount": _decimal_to_json_number(
                request.amount,
            ),
            "currency": request.currency,
            "merchant_code": self._merchant_code,
            "description": request.description,
            "redirect_url": request.customer_return_url,
            "return_url": request.webhook_url,
            "hosted_checkout": {
                "enabled": True,
            },
        }

        response = self._request_json(
            method="POST",
            path=SUMUP_CHECKOUTS_PATH,
            payload=payload,
        )

        provider_payment_id = response.get(
            "id"
        )
        redirect_url = response.get(
            "hosted_checkout_url"
        )

        if not isinstance(
            provider_payment_id,
            str,
        ) or not provider_payment_id:
            raise SumUpPaymentError(
                "SumUp checkout response has no checkout id"
            )

        if not isinstance(
            redirect_url,
            str,
        ) or not redirect_url:
            raise SumUpPaymentError(
                "SumUp checkout response has no hosted checkout URL"
            )

        return HostedPaymentSession(
            provider_payment_id=provider_payment_id,
            redirect_url=redirect_url,
        )

    def get_payment(
        self,
        *,
        provider_payment_id: str,
    ) -> ExternalPaymentState:
        """Retrieve and normalize the current SumUp checkout state."""

        provider_payment_id = _required_payment_id(
            provider_payment_id
        )

        response = self._request_json(
            method="GET",
            path=_checkout_path(provider_payment_id),
        )

        state = _checkout_state(
            response
        )

        if state.provider_payment_id != provider_payment_id:
            raise SumUpPaymentError(
                "SumUp returned an unexpected checkout id"
            )

        return state

    def find_payment_by_reference(
        self,
        *,
        reference: str,
    ) -> ExternalPaymentState | None:
        """Find the checkout created with our reference, if SumUp has one."""

        reference = reference.strip()

        if not reference:
            raise ValueError(
                "payment reference is required"
            )

        response = self._request(
            method="GET",
            path=(
                f"{SUMUP_CHECKOUTS_PATH}?"
                f"{urlencode({'checkout_reference': reference})}"
            ),
        )

        if not isinstance(
            response,
            list,
        ):
            raise SumUpPaymentError(
                "SumUp returned an invalid checkout list"
            )

        # A checkout without a reference field is kept as a possible match:
        # wrongly reporting "no payment" could hide a real one.
        matches = [
            checkout
            for checkout in response
            if isinstance(checkout, dict)
            and checkout.get("checkout_reference", reference) == reference
        ]

        if not matches:
            return None

        if len(matches) > 1:
            raise SumUpPaymentError(
                f"SumUp has several checkouts with reference {reference!r}"
            )

        return _checkout_state(
            matches[0]
        )

    def cancel_payment(
        self,
        *,
        provider_payment_id: str,
    ) -> None:
        """Deactivate an open SumUp checkout so it can no longer be paid."""

        provider_payment_id = _required_payment_id(
            provider_payment_id
        )

        self._request(
            method="DELETE",
            path=_checkout_path(provider_payment_id),
        )

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object]:
        data = self._request(
            method=method,
            path=path,
            payload=payload,
        )

        if not isinstance(
            data,
            dict,
        ):
            raise SumUpPaymentError(
                "SumUp returned an invalid checkout response"
            )

        return data

    def _request(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> object:
        body = None

        if payload is not None:
            body = json.dumps(
                payload,
            ).encode("utf-8")

        http_request = Request(
            url=f"{SUMUP_API_BASE_URL}{path}",
            data=body,
            method=method,
            headers={
                "Authorization": (
                    f"Bearer {self._api_key}"
                ),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(
                http_request,
                timeout=self._timeout_seconds,
            ) as response:
                response_body = response.read()

        except HTTPError as exc:
            raise SumUpPaymentError(
                f"SumUp returned HTTP {exc.code}"
            ) from exc

        except URLError as exc:
            raise SumUpPaymentError(
                "Could not reach SumUp"
            ) from exc

        if not response_body:
            return None

        try:
            return json.loads(
                response_body,
            )
        except json.JSONDecodeError as exc:
            raise SumUpPaymentError(
                "SumUp returned invalid JSON"
            ) from exc


def _checkout_state(
    checkout: dict[str, object],
) -> ExternalPaymentState:
    response_id = checkout.get(
        "id"
    )

    if not isinstance(response_id, str) or not response_id:
        raise SumUpPaymentError(
            "SumUp checkout has no id"
        )

    hosted_payment_url = checkout.get(
        "hosted_checkout_url"
    )

    if not isinstance(
        hosted_payment_url,
        str,
    ) or not hosted_payment_url:
        hosted_payment_url = None

    status = checkout.get(
        "status"
    )

    if status == "PENDING":
        return ExternalPaymentState(
            provider_payment_id=response_id,
            status=ExternalPaymentStatus.PENDING,
            hosted_payment_url=hosted_payment_url,
        )

    if status in {
        "FAILED",
        "EXPIRED",
    }:
        return ExternalPaymentState(
            provider_payment_id=response_id,
            status=ExternalPaymentStatus.FAILED,
            hosted_payment_url=hosted_payment_url,
        )

    if status == "PAID":
        transaction_id = checkout.get(
            "transaction_id"
        )

        if not isinstance(
            transaction_id,
            str,
        ) or not transaction_id:
            raise SumUpPaymentError(
                "paid SumUp checkout has no transaction id"
            )

        return ExternalPaymentState(
            provider_payment_id=response_id,
            status=ExternalPaymentStatus.SUCCEEDED,
            provider_transaction_id=transaction_id,
            hosted_payment_url=hosted_payment_url,
        )

    raise SumUpPaymentError(
        f"unsupported SumUp checkout status: {status!r}"
    )


def _required_payment_id(
    provider_payment_id: str,
) -> str:
    provider_payment_id = provider_payment_id.strip()

    if not provider_payment_id:
        raise ValueError(
            "provider payment id is required"
        )

    return provider_payment_id


def _checkout_path(
    provider_payment_id: str,
) -> str:
    return (
        f"{SUMUP_CHECKOUTS_PATH}/"
        f"{quote(provider_payment_id, safe='')}"
    )


def _decimal_to_json_number(
    value: Decimal,
) -> float:
    return float(value)
