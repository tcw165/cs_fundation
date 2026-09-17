from subarray_sum_equals_k import subarray_sum


def test_subarray_sum_all_ones() -> None:
    assert subarray_sum([1, 1, 1], 2) == 2


def test_subarray_sum_mixed() -> None:
    assert subarray_sum([1, 2, 3], 3) == 2
