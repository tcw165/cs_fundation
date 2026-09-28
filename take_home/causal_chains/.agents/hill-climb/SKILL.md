---
name: hill-climb
description: Run the causal chain agent once on a fixed query.
---

# Hill climb

The fixed query is "The Strait of Hormuz is going to open next week." Do not chase 0.0206. That number is the seed, not the truth.

The runner calls the causal chain agent once and tells it how many attempts remain. The agent finds the present, then connects it to that future. It returns the terminal situation.
