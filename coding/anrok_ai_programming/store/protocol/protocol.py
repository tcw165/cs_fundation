from datetime import date
from typing import Protocol, runtime_checkable

from coding.anrok_ai_programming.models.models import IngestResult, RetrieveResult, TaxRatePeriod


@runtime_checkable
class TaxRateStore(Protocol):
    def replace_all(self, periods: list[TaxRatePeriod]) -> IngestResult: ...

    def find_in_force(
        self,
        locality: str,
        as_of: date,
        tax_type: str,
        rate_type: str,
    ) -> RetrieveResult: ...
