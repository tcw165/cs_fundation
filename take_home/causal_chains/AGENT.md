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

### Logging

Log messages use f-strings: `logger().info(f"tool call {tool_name}")`. Do not use `%` formatting.

## AI agents

- Agents live under `agents/agents/`.
- An agent's system prompt is `agents/agents/<agent>/prompts/<agent>.md`.
- A system prompt starts with `# Goal`, then `# Key Rules`. The causal chain agent uses `# Iterative Process` instead, with nested steps for the loop. Do not add an `# Examples` section.
- Write the prompt in natural language. Do not quote tool or function names.
- Every agent tool has a docstring for the function and for each argument.

## Play

```bash
cd take_home/causal_chains
just play
```

That brings up every service in the compose file and waits until they are ready. Open the chat at `http://127.0.0.1:5173/`. The API is on port 8000.

## Offline eval

Use this when you need to quickly validate the causal chain core functionality. It starts Neo4j and saves the chain there. Each run deletes the situations already in the graph. Pass `--no-clean-graph` to keep them. Open `http://localhost:7474` to read the graph.

```bash
cd take_home/causal_chains
just eval-offline 'Republicans win the House but Democrats take the senate during the Midterm.'
```

A recorded run of `The Strait of Hormuz is going to open next week.` is in `agents/eval/README.md`.

## Development

- Shape a plan as a stack of PRs. Each PR is one branch stacked on the previous one.
- Every PR in the plan has a Before snippet and an After snippet. The snippets are the real code, short enough to read in one look.
- After the stack is pushed, watch it. Address review comments, and watch CI until the checks finish.
