---
name: sales_tax_ingest
description: Load an Alabama local tax-rate CSV into DynamoDB Local. Every run deletes tax_rate_period and writes the file fresh.
---

# Sales tax ingest

Use this when a person gives you a local tax-rate CSV and wants it loaded.

The tool deletes `tax_rate_period` before it writes. Do not merge with rows already in the table. Do not dedup.

Run:

```bash
bazel run //coding/anrok_ai_programming/agent_skills/sales_tax_ingest:ingest -- --csv /path/to/taxrates.csv
```

Stdout is `IngestResult` JSON: `rows_read`, `rows_written`, `table`, `endpoint`.

The CSV shape is the Alabama Department of Revenue local cities and counties tax-rate file: https://www.revenue.alabama.gov/sales-use/local-cities-and-counties-tax-rates-text-file/

If port 8002 is closed, the tool starts `coding/anrok_ai_programming/docker-compose.yml` and uses `http://127.0.0.1:8002`.
