export type HealthResponse = { status: string };

export type HealthPort = {
  get_health: () => Promise<HealthResponse>;
};
