---
name: hill-climb
description: Run crystal_ball on a fixed query and keep a graph only when examine raises the score.
---

# Hill climb

The fixed query is "The Strait of Hormuz is going to open next week." Do not chase 0.0206. That number is the seed, not the truth.

1. Run crystal_ball on the fixed sentence. The first run has no critique.
2. Call examine on the ChainGraph. The score is code.
3. If the score is higher than the last kept graph, keep this graph. Write one change that names a single failed check.
4. Run crystal_ball again with the same sentence plus that one change.
5. Stop when the score does not rise, or after 3 runs. Return the kept graph.
