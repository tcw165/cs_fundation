# Causal chains

Rules for this package. Paths below are relative to `take_home/causal_chains/`.

## Backend

### Dependency injection

`AppContainer` shares the lifespan of the host app process. It may hold sub-containers, and those sub-containers may hold their own. Wire dependencies through the container. Do not construct clients inside a service that the container already provides.

### Models, protocol, and implementation

Keep models, protocols, and implementations apart.

- A component's interface lives at `xxx/protocol/protocol.py`.
- The implementation lives in `xxx/`, next to that protocol package.
- Every model has a docstring.

## AI agents

- Agents live under `agents/agents/`.
- An agent's system prompt is `agents/agents/<agent>/prompts/<agent>.md`.
- A system prompt starts with `# Goal`, then `# Key Rules`. The causal chain agent uses `# Iterative Process` instead, with nested steps for the loop. Do not add an `# Examples` section.
- Write the prompt in natural language. Do not quote tool or function names.
- Every agent tool has a docstring for the function and for each argument.

## Offline eval

Use this when you need to quickly validate the causal chain core functionality:

```bash
bazel run //take_home/causal_chains/agents/eval/offline:offline -- --query "The Strait of Hormuz is going to open next week."
```
