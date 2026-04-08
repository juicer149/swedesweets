from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from accounts.domain.errors import DuplicateAccountIdentity
from accounts.domain.roles import StaffAccessLevel
from accounts.models import StaffAccount, Store

from .commands import CreateStaffAccountCommand, CreateStoreAccountCommand

User = get_user_model()


def _normalize_username(value: str) -> str:
    return value.strip()


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _ensure_unique_identity(*, username: str, email: str) -> None:
    if User.objects.filter(username=username).exists():
        raise DuplicateAccountIdentity("A user with this username already exists.")

    if email and User.objects.filter(email=email).exists():
        raise DuplicateAccountIdentity("A user with this email already exists.")


@transaction.atomic
def create_store_account(command: CreateStoreAccountCommand):
    username = _normalize_username(command.username)
    email = _normalize_email(command.email)

    _ensure_unique_identity(username=username, email=email)

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=command.password,
            is_staff=False,
            is_superuser=False,
        )
        store = Store.objects.create(
            user=user,
            name=command.store_name.strip(),
            phone=command.phone.strip(),
            address=command.address.strip(),
            is_active=command.is_active,
        )
    except IntegrityError as exc:
        raise DuplicateAccountIdentity(
            "Could not create store account due to duplicate identity."
        ) from exc

    return store


@transaction.atomic
def create_staff_account(command: CreateStaffAccountCommand):
    username = _normalize_username(command.username)
    email = _normalize_email(command.email)

    _ensure_unique_identity(username=username, email=email)

    is_full_staff = command.access_level == StaffAccessLevel.FULL

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=command.password,
            is_staff=is_full_staff,
            is_superuser=is_full_staff,
        )
        staff_account = StaffAccount.objects.create(
            user=user,
            access_level=command.access_level,
        )
    except IntegrityError as exc:
        raise DuplicateAccountIdentity(
            "Could not create staff account due to duplicate identity."
        ) from exc

    return staff_account
