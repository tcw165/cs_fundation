# Goal
Create the next situation from the current situation. Change only one key-factor. When that next situation is sorted out, save it in the database.

# Key Rules
- The prompt is the direction for this one step. It starts with the case id, then the one change to make.
- Change only one key-factor relative to from_situation. Name that key-factor in the new description.
- Save at most one mid-chain situation on that case. Do not save a start or the terminal. Do not return two.
- When no room remains for another situation, or the one remaining change is the terminal itself, return no situation and do not save.
- When you save, save once. The id is assigned when the situation is saved. Return that saved situation.
- Do not set a probability.
