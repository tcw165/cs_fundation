from coin_change import coin_change


def test_coin_change_example() -> None:
    assert coin_change([1, 2, 5], 11) == 3


def test_coin_change_impossible() -> None:
    assert coin_change([2], 3) == -1
