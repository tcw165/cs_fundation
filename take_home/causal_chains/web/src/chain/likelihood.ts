export function likelihood_label(p: string): string {
  const value = Number(p);
  if (!Number.isFinite(value)) {
    return "unknown";
  }
  if (value < 0.25) {
    return "very unlikely";
  }
  if (value < 0.5) {
    return "unlikely";
  }
  if (value < 0.75) {
    return "likely";
  }
  return "very likely";
}
