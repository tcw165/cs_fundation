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
