from range_sum_query_2d import NumMatrix


def test_sum_region_example() -> None:
    matrix = NumMatrix(
        [
            [3, 0, 1, 4, 2],
            [5, 6, 3, 2, 1],
            [1, 2, 0, 1, 5],
            [4, 1, 0, 1, 7],
            [1, 0, 3, 0, 5],
        ]
    )
    assert matrix.sum_region(2, 1, 4, 3) == 8
