# Goal
Take one step from the current situation toward the terminal. Either link the current situation to the terminal, or create the next situation with only one key-factor changed and link the current situation to it. Save that link once the step is sorted out.

# Key Rules
- The prompt is the direction for this one step. It starts with the case id, then the open line from the present through the current situation including each saved link, then the one change to make.
- When no room remains for another situation, or the one remaining change is the terminal itself, do not save a situation. Link the current situation to the terminal. Return no situation.
- Otherwise change only one key-factor relative to the current situation. Name that key-factor in the new description. Save that one mid-chain situation. Link the current situation to it. Do not save a start or the terminal. Do not return two.
- For the one link, ask what a person could move. Save that link once. The stored probability is the mean of those inputs. Do not set a probability.
- When you save a situation, save once. The id is assigned when the situation is saved. Return that saved situation.
