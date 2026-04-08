from accounts.domain.errors import UnsupportedAccountCommand

from .actions import create_staff_account, create_store_account
from .commands import CreateStaffAccountCommand, CreateStoreAccountCommand

COMMAND_HANDLER = {
    CreateStoreAccountCommand: create_store_account,
    CreateStaffAccountCommand: create_staff_account,
}


def dispatch_account_creation(command):
    handler = COMMAND_HANDLER.get(type(command))
    if handler is None:
        raise UnsupportedAccountCommand(
            f"Unsupported account command: {type(command).__name__}"
        )
    return handler(command)
