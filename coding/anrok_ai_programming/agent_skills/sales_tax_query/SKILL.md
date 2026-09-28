---
name: sales_tax_query
description: Look up the local tax rate in force for a locality. Defaults to general sales tax today.
---

# Sales tax query

Use this when a person asks for a locality's tax rate. The usual question is the general sales tax in force right now.

Run:

```bash
bazel run //coding/anrok_ai_programming/agent_skills/sales_tax_query:query -- --locality "HALEYVILLE"
```

Leave `--as-of`, `--tax-type`, and `--rate-type` unset unless the person asked for a different date or a different tax. Unset means today, `ST`, and `GENER`.

Stdout is `RetrieveResult` JSON. Read `rate` first. Open `periods` only when `rate` is null, or when the person asked which county code applies. `pj_rate` is the police-jurisdiction rate when every matching row shares it.

`rate_unit` is `percent` except for `WDFEE`, where it is `flat`. Do not call a `WDFEE` number a percent.

This tool does not delete rows. A missing `tax_rate_period` table is an error. Load the CSV with `sales_tax_ingest` first.

If port 8002 is closed, the tool starts `coding/anrok_ai_programming/docker-compose.yml` and uses `http://127.0.0.1:8002`.
