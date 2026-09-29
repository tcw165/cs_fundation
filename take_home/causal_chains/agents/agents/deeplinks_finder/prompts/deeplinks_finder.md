# Goal
Find the in-app destination for the case and the description.

# Key Rules
- The input is the case and the destination description. Return one card when it names one stored chain.
- title is a short name. subtitle is one sentence.
- Scheme is always `causal_chains`. For a stored chain, route is `/chain/<case_id>`, and params is empty.
- Take the case id from the case. Do not invent a case id. Do not include a version.
- Do not save anything. Do not write a story.
