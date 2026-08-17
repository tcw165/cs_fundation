from subset_sum import subset_sum


def test_subset_sum_true() -> None:
    assert subset_sum([3, 34, 4, 12, 5, 2], 9) is True


def test_subset_sum_false() -> None:
    assert subset_sum([9], 4) is False
