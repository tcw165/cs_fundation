CREATE CONSTRAINT situation_id IF NOT EXISTS
FOR (s:Situation) REQUIRE s.situation_id IS UNIQUE;

CREATE CONSTRAINT case_id IF NOT EXISTS
FOR (c:Case) REQUIRE c.case_id IS UNIQUE;

CREATE
  (case:Case {case_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"}),
  (now:Situation {
    situation_id: "11111111-1111-4111-8111-111111111111",
    version: 1,
    desc: "Strait shut 208 days, transit about 0 against 85 mb/d, blockade still in force, latest deal rejected, about 400 ships waiting.",
    kind: "start",
    potential_factors: ["blockade", "rejected deal"],
    original_ask: ""
  }),
  (deal:Situation {
    situation_id: "22222222-2222-4222-8222-222222222222",
    version: 1,
    desc: "US accepts a deal this week.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (no_deal:Situation {
    situation_id: "33333333-3333-4333-8333-333333333333",
    version: 1,
    desc: "No deal this week.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (clear:Situation {
    situation_id: "44444444-4444-4444-8444-444444444444",
    version: 1,
    desc: "Ships clear by October 3 and normal traffic resumes.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (stuck:Situation {
    situation_id: "55555555-5555-4555-8555-555555555555",
    version: 1,
    desc: "Ships still stuck after a deal.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (resumes:Situation {
    situation_id: "66666666-6666-4666-8666-666666666666",
    version: 1,
    desc: "Traffic resumes by October 3 without a deal.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (shut:Situation {
    situation_id: "77777777-7777-4777-8777-777777777777",
    version: 1,
    desc: "Stays shut.",
    kind: "situation",
    potential_factors: [],
    original_ask: ""
  }),
  (now)-[:BELONGS_TO]->(case),
  (deal)-[:BELONGS_TO]->(case),
  (no_deal)-[:BELONGS_TO]->(case),
  (clear)-[:BELONGS_TO]->(case),
  (stuck)-[:BELONGS_TO]->(case),
  (resumes)-[:BELONGS_TO]->(case),
  (shut)-[:BELONGS_TO]->(case),
  (now)-[:LEADS_TO {p: 0.08}]->(deal),
  (now)-[:LEADS_TO {p: 0.92}]->(no_deal),
  (deal)-[:LEADS_TO {p: 0.20}]->(clear),
  (deal)-[:LEADS_TO {p: 0.80}]->(stuck),
  (no_deal)-[:LEADS_TO {p: 0.005}]->(resumes),
  (no_deal)-[:LEADS_TO {p: 0.995}]->(shut);
