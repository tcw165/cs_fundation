def subset_sum(nums: list[int], target: int) -> bool:
    reachable = {0}

    for num in nums:
        reachable = reachable | {value + num for value in reachable}
        if target in reachable:
            return True

    return target in reachable
