def subarray_sum(nums: list[int], k: int) -> int:
    prefix = 0
    counts: dict[int, int] = {0: 1}
    result = 0

    for num in nums:
        prefix += num
        result += counts.get(prefix - k, 0)
        counts[prefix] = counts.get(prefix, 0) + 1

    return result
