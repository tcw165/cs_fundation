CREATE CONSTRAINT situation_id IF NOT EXISTS
FOR (s:Situation) REQUIRE s.situation_id IS UNIQUE;

CREATE CONSTRAINT case_id IF NOT EXISTS
FOR (c:Case) REQUIRE c.case_id IS UNIQUE;

MERGE (case:Case {case_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"})

MERGE (now:Situation {situation_id: "11111111-1111-4111-8111-111111111111"})
SET now.version = 1,
    now.desc = "Strait shut 208 days, transit about 0 against 85 mb/d, blockade still in force, latest deal rejected, about 400 ships waiting.",
    now.kind = "start",
    now.potential_factors = ["blockade", "rejected deal"],
    now.original_ask = ""

MERGE (deal:Situation {situation_id: "22222222-2222-4222-8222-222222222222"})
SET deal.version = 1,
    deal.desc = "US accepts a deal this week.",
    deal.kind = "situation",
    deal.potential_factors = [],
    deal.original_ask = ""

MERGE (no_deal:Situation {situation_id: "33333333-3333-4333-8333-333333333333"})
SET no_deal.version = 1,
    no_deal.desc = "No deal this week.",
    no_deal.kind = "situation",
    no_deal.potential_factors = [],
    no_deal.original_ask = ""

MERGE (clear:Situation {situation_id: "44444444-4444-4444-8444-444444444444"})
SET clear.version = 1,
    clear.desc = "Ships clear by October 3 and normal traffic resumes.",
    clear.kind = "situation",
    clear.potential_factors = [],
    clear.original_ask = ""

MERGE (stuck:Situation {situation_id: "55555555-5555-4555-8555-555555555555"})
SET stuck.version = 1,
    stuck.desc = "Ships still stuck after a deal.",
    stuck.kind = "situation",
    stuck.potential_factors = [],
    stuck.original_ask = ""

MERGE (resumes:Situation {situation_id: "66666666-6666-4666-8666-666666666666"})
SET resumes.version = 1,
    resumes.desc = "Traffic resumes by October 3 without a deal.",
    resumes.kind = "situation",
    resumes.potential_factors = [],
    resumes.original_ask = ""

MERGE (shut:Situation {situation_id: "77777777-7777-4777-8777-777777777777"})
SET shut.version = 1,
    shut.desc = "Stays shut.",
    shut.kind = "situation",
    shut.potential_factors = [],
    shut.original_ask = ""

MERGE (now)-[:BELONGS_TO]->(case)
MERGE (deal)-[:BELONGS_TO]->(case)
MERGE (no_deal)-[:BELONGS_TO]->(case)
MERGE (clear)-[:BELONGS_TO]->(case)
MERGE (stuck)-[:BELONGS_TO]->(case)
MERGE (resumes)-[:BELONGS_TO]->(case)
MERGE (shut)-[:BELONGS_TO]->(case)

MERGE (now)-[now_deal:LEADS_TO]->(deal)
SET now_deal.p = 0.08
MERGE (now)-[now_no_deal:LEADS_TO]->(no_deal)
SET now_no_deal.p = 0.92
MERGE (deal)-[deal_clear:LEADS_TO]->(clear)
SET deal_clear.p = 0.20
MERGE (deal)-[deal_stuck:LEADS_TO]->(stuck)
SET deal_stuck.p = 0.80
MERGE (no_deal)-[no_deal_resumes:LEADS_TO]->(resumes)
SET no_deal_resumes.p = 0.005
MERGE (no_deal)-[no_deal_shut:LEADS_TO]->(shut)
SET no_deal_shut.p = 0.995
