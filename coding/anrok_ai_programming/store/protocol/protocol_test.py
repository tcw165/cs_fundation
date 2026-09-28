from datetime import date

from coding.anrok_ai_programming.models.models import IngestResult, RetrieveResult, TaxRatePeriod
from coding.anrok_ai_programming.store.protocol.protocol import TaxRateStore


class _Store:
    def replace_all(self, periods: list[TaxRatePeriod]) -> IngestResult:
        raise NotImplementedError

    def find_in_force(
        self,
        locality: str,
        as_of: date,
        tax_type: str,
        rate_type: str,
    ) -> RetrieveResult:
        raise NotImplementedError


class _ReplaceOnly:
    def replace_all(self, periods: list[TaxRatePeriod]) -> IngestResult:
        raise NotImplementedError


def test_tax_rate_store_requires_both_methods() -> None:
    assert isinstance(_Store(), TaxRateStore)
    assert not isinstance(_ReplaceOnly(), TaxRateStore)
