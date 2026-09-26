# Paths from now to the query

P(reopen) = P(deal) * P(clear | deal) + P(no deal) * P(clear | no deal)
          = 0.0206

# Schema

(:Situation {situation_id, desc, is_root})-[:LEADS_TO {p}]->(:Situation)
