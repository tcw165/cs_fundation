class NumMatrix:
    def __init__(self, matrix: list[list[int]]) -> None:
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        prefix: list[list[int]] = [[0] * (cols + 1) for _ in range(rows + 1)]

        for row in range(rows):
            for col in range(cols):
                prefix[row + 1][col + 1] = (
                    matrix[row][col]
                    + prefix[row][col + 1]
                    + prefix[row + 1][col]
                    - prefix[row][col]
                )

        self._prefix = prefix

    def sum_region(self, row1: int, col1: int, row2: int, col2: int) -> int:
        prefix = self._prefix
        return (
            prefix[row2 + 1][col2 + 1]
            - prefix[row1][col2 + 1]
            - prefix[row2 + 1][col1]
            + prefix[row1][col1]
        )
