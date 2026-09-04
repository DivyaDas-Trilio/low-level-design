from abc import ABC, abstractmethod

from fines.domain.money import Money


class FineCalculationStrategy(ABC):
    """Turns a FACT (days overdue) into a POLICY outcome (money owed).

    A Strategy (not an invariant): the RATE is a business decision that may change
    (grace periods, member discounts). Injected, so changing it never touches Fine.
    """

    @abstractmethod
    def calculate(self, days_overdue: int) -> Money:
        ...


class StandardFineStrategy(FineCalculationStrategy):
    """Business rule #3: ₹5 per day late — but the RATE is injected.

    The default keeps ₹5, so existing callers are unchanged; the composition
    root passes the rate from config (Step 14.1). Raising the fine to ₹6 is then
    an environment change, not a code change — the domain stays pure (it never
    imports config; it just receives a Money).
    """

    def __init__(self, rate: Money = Money.rupees(5)):
        self._rate = rate

    def calculate(self, days_overdue: int) -> Money:
        return self._rate.multiply(max(0, days_overdue))


class GracePeriodFineStrategy(FineCalculationStrategy):
    """Example of OCP: a new policy is a NEW class — existing ones untouched."""

    def __init__(self, grace_days: int = 2, rate: Money = Money.rupees(5)):
        self._grace = grace_days
        self._rate = rate

    def calculate(self, days_overdue: int) -> Money:
        chargeable = max(0, days_overdue - self._grace)
        return self._rate.multiply(chargeable)
