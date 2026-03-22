class DomainError(Exception):
    pass


class ValidationError(DomainError):
    pass


class BusinessRuleError(DomainError):
    pass
