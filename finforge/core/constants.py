"""Static constants shared across the framework."""

from finforge.core.enums import PersonaType

DEFAULT_CITY = "Bengaluru"
DEFAULT_START_DATE = "2026-01-01"
DEFAULT_USER_COUNT = 10
DEFAULT_MONTHS = 1
DEFAULT_INITIAL_BALANCE_RANGE = (500.0, 3000.0)
DEFAULT_INCOME_RANGE = {
    PersonaType.SALARIED.value: (3500.0, 9000.0),
    PersonaType.STUDENT.value: (150.0, 1200.0),
}
