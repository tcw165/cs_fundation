# Goal
Take one step from the current situation toward the terminal. Either link the current situation to the terminal, or create the next situation with only one driver changed and link the current situation to it. Save that link once the step is sorted out.

# Examples

## Common shape

The direction for this one step starts with the case id, then the open line from the present through the current situation including each saved link, then the one driver to change.

step 0:
- Read the current situation, its remained drivers, and the terminal situation.
- Search the web for more context on those remained drivers.

step 1:
- Pick one remained driver from the current situation, and say why that one. Change only one driver from the current situation's remained drivers.
- Write a short title for that one mid-chain situation. Name that driver in the description.
- Save the next situation with that driver removed from the remained drivers. Save once. The id is assigned when the situation is saved.
- Do not save a start or the terminal. Do not return two.

step 3:
- Ask what a person could move. Price the link from the current situation to the next situation. The stored probability is the mean of those inputs. Do not set a probability.
- Save the link from the current situation to the next situation. Save that link once.

step N:
- Return the saved next situation when it is not the terminal.

## When the one remaining change is the terminal itself

- Do not save a situation. Link the current situation to the terminal. Return no situation.
