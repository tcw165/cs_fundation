# Goal
Save the next situations that can follow the current one, on the way toward the future you were given.

# Key Rules
- The input is the current description, the user's ask, and thoughts about how much room is left.
- When the thoughts say there is room to explore, save several plausible next situations.
- When the thoughts say the gap must close, save the situations that reach the future.
- The id is assigned when each situation is saved. Do not set a probability.
- While the chain is still open, return the saved next situations.
- When one saved next situation states that ask, in those words or a close restatement, return that terminal situation alone, including its id and the user's ask.
