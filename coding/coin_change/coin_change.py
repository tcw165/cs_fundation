def coin_change(coins: list[int], amount: int) -> int:
    if amount == 0:
        return 0

    dp = [amount + 1] * (amount + 1)
    dp[0] = 0

    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value:
                dp[value] = min(dp[value], dp[value - coin] + 1)

    return dp[amount] if dp[amount] <= amount else -1
