class AccountProvisioningError(Exception):
    """Base class for account provisioning errors."""


class DuplicateAccountIdentity(AccountProvisioningError):
    """Raised when a username or email is already in use."""


class UnsupportedAccountCommand(AccountProvisioningError):
    """Raised when dispatch receives an unsupported account command."""


class InvalidAccountIdentity(AccountProvisioningError):
    """
    Raised when a Django user has an impossible business-identity combination.

    DESIGN DECISION:
    A user may represent exactly one business identity in this system:

    - store user via Store
    - internal staff user via StaffAccount
    - unknown/unconfigured user

    A user must never be linked to both Store and StaffAccount at the same time.
    If that happens, the data is considered invalid and role resolution should fail
    loudly instead of silently picking one identity.
    """
