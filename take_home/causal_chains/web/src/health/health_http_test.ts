import { describe, expect, it, vi } from "vitest";

import { create_health_http } from "./health_http";

describe("create_health_http", () => {
  it("fetches /health from the api url", async () => {
    const fetch_mock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetch_mock);
    const health_port = create_health_http("http://agents:8000");
    const report = await health_port.get_health();
    expect(report).toEqual({ status: "ok" });
    expect(fetch_mock).toHaveBeenCalledWith("http://agents:8000/health");
    vi.unstubAllGlobals();
  });
});
