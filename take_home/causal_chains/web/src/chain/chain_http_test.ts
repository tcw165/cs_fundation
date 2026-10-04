import { describe, expect, it, vi } from "vitest";

import { create_chain_http } from "./chain_http";

describe("create_chain_http", () => {
  it("fetches /api/v1/causal_chains from the api url", async () => {
    const chain = {
      situations: [
        {
          situation_id: "11111111-1111-4111-8111-111111111111",
          version: 1,
          created_timestamp: "2026-10-01T00:00:00+00:00",
          kind: "start",
          title: "Strait shut",
          desc: "now",
          remained_drivers: [],
        },
      ],
      links: [],
    };
    const fetch_mock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [chain],
    });
    vi.stubGlobal("fetch", fetch_mock);
    const chain_port = create_chain_http("http://agents:8000");
    expect(await chain_port.get_chains()).toEqual([chain]);
    expect(fetch_mock).toHaveBeenCalledWith("http://agents:8000/api/v1/causal_chains");
    vi.unstubAllGlobals();
  });
});
