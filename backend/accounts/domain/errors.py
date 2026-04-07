class AccountProvisioningError(Exception):
    """
    Base class for account provisioning errors.

    These errors belong to the explicit account-creation workflow rather than
    raw Django/ORM exceptions leaking into views.
    """


class DuplicateAccountIdentity(AccountProvisioningError):
    """
    Raised when a username or email is already in use.
    """


class UnsupportedAccountCommand(AccountProvisioningError):
    """
    Raised when the dispatch layer receives an unknown command type.
    """
