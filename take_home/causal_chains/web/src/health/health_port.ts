export type HealthResponse = { status: string; db: string };

export type HealthPort = {
  get_health: () => Promise<HealthResponse>;
};
