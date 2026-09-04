from shared.ids import FineId, MemberId, LoanId
from fines.domain.fine import Fine
from fines.domain.repository import FineRepository
from fines.domain.fine_calculation import FineCalculationStrategy


class FineService:
    """Application service for the Fines subdomain.

    Holds the fine-calculation STRATEGY (injected) — swapping the policy never
    touches this service or the Fine entity. `assess_fine` is called (with the
    days-overdue FACT) by the lending return flow.
    """

    def __init__(self, fines: FineRepository, strategy: FineCalculationStrategy):
        self._fines = fines
        self._strategy = strategy

    # UC-4: assess a late fine on return (given the days-overdue FACT)
    def assess_fine(self, member_id: MemberId, loan_id: LoanId, days_overdue: int) -> FineId | None:
        if days_overdue <= 0:
            return None                                     # on time → no fine
        amount = self._strategy.calculate(days_overdue)     # FACT -> POLICY -> Money
        fine = Fine(FineId.new(), member_id, loan_id, amount)
        self._fines.save(fine)
        return fine.id

    # UC-6: pay a fine
    def pay_fine(self, fine_id: FineId) -> None:
        fine = self._fines.get(fine_id)                     # load
        fine.pay()                                          # domain command (settle-once guard)
        self._fines.save(fine)                              # save

    def waive_fine(self, fine_id: FineId) -> None:
        fine = self._fines.get(fine_id)
        fine.waive()
        self._fines.save(fine)

    def get_fine(self, fine_id: FineId) -> Fine:
        return self._fines.get(fine_id)

    def list_unpaid_by_member(self, member_id: MemberId) -> list[Fine]:
        return self._fines.find_unpaid_by_member(member_id)
