---
name: hill-climb
description: Run the discovery loop on a fixed query until it closes or the quota is spent.
---

# Hill climb

The fixed query is "The Strait of Hormuz is going to open next week." Do not chase 0.0206. That number is the seed, not the truth.

The runner calls `now_scout` once, then `path_builder` until the path closes or `attempt_quota` is spent. A close step gets one close-out prompt. There is no `ChainGraph` and no examine score.
