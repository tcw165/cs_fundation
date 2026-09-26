CREATE CONSTRAINT situation_id IF NOT EXISTS
FOR (s:Situation) REQUIRE s.situation_id IS UNIQUE;

CREATE
  (now:Situation {
    situation_id: "11111111-1111-4111-8111-111111111111",
    desc: "Strait shut 208 days, transit about 0 against 85 mb/d, blockade still in force, latest deal rejected, about 400 ships waiting.",
    is_root: true
  }),
  (deal:Situation {
    situation_id: "22222222-2222-4222-8222-222222222222",
    desc: "US accepts a deal this week.",
    is_root: false
  }),
  (no_deal:Situation {
    situation_id: "33333333-3333-4333-8333-333333333333",
    desc: "No deal this week.",
    is_root: false
  }),
  (clear:Situation {
    situation_id: "44444444-4444-4444-8444-444444444444",
    desc: "Ships clear by October 3 and normal traffic resumes.",
    is_root: false
  }),
  (stuck:Situation {
    situation_id: "55555555-5555-4555-8555-555555555555",
    desc: "Ships still stuck after a deal.",
    is_root: false
  }),
  (resumes:Situation {
    situation_id: "66666666-6666-4666-8666-666666666666",
    desc: "Traffic resumes by October 3 without a deal.",
    is_root: false
  }),
  (shut:Situation {
    situation_id: "77777777-7777-4777-8777-777777777777",
    desc: "Stays shut.",
    is_root: false
  }),
  (now)-[:LEADS_TO {p: 0.08}]->(deal),
  (now)-[:LEADS_TO {p: 0.92}]->(no_deal),
  (deal)-[:LEADS_TO {p: 0.20}]->(clear),
  (deal)-[:LEADS_TO {p: 0.80}]->(stuck),
  (no_deal)-[:LEADS_TO {p: 0.005}]->(resumes),
  (no_deal)-[:LEADS_TO {p: 0.995}]->(shut);
