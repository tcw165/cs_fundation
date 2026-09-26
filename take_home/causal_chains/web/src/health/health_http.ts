import type { HealthPort, HealthResponse } from "./health_port";

export function create_health_http(api_url: string): HealthPort {
  return {
    get_health: async (): Promise<HealthResponse> => {
      const response = await fetch(`${api_url}/health`);
      if (!response.ok) {
        throw new Error(`health failed: ${response.status}`);
      }
      return response.json();
    },
  };
}
