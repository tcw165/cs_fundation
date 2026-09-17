from trapping_rain_water import trap


def test_trap_example() -> None:
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6


def test_trap_empty() -> None:
    assert trap([]) == 0
