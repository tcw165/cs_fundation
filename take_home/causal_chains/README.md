# Demo

The chat sits in the center. The chain panel stays folded until a `causal_chains://` link is ready. From `web/`, open `/?demo=1` to play the Hormuz turn.

![Folded chat](web/e2e/shots/01-chat-folded.png)

The next paragraph waits until the current one has finished animating.

![Queued paragraph](web/e2e/shots/02-message-queued.png)

The panel then unfolds beside the chat.

![Unfolded panel](web/e2e/shots/03-panel-unfolded.png)

A situation opens into a scrolling card and pushes the other nodes aside.

![Situation card](web/e2e/shots/04-situation-card.png)

An edge does the same for its probability and inputs.

![Edge card](web/e2e/shots/05-edge-card.png)

[Recording](web/e2e/shots/chat-chain.webm)

# Paths from now to the query

The query probability is the sum of the path products into the yes destinations. Each situation's yes and no edges sum to 1.

```mermaid
flowchart TD
  nowNode["now"]
  dealYes["yes: deal"]
  noDeal["no: no deal"]
  clearFromDeal["yes: clear"]
  failFromDeal["no"]
  clearFromNoDeal["yes: clear"]
  failFromNoDeal["no"]
  nowNode -->|"P(deal)"| dealYes
  nowNode -->|"P(no deal)"| noDeal
  dealYes -->|"P(clear given deal)"| clearFromDeal
  dealYes -->|"1 - P(clear given deal)"| failFromDeal
  noDeal -->|"P(clear given no deal)"| clearFromNoDeal
  noDeal -->|"1 - P(clear given no deal)"| failFromNoDeal
```

P(reopen) = P(deal) * P(clear | deal) + P(no deal) * P(clear | no deal)
          = 0.0206

# Schema

(:Case {case_id})<-[:BELONGS_TO]-(:Situation {situation_id, desc, kind})-[:LEADS_TO {p, inputs}]->(:Situation)
