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

export function sparkline_points(seed: string): string {
  let hash = 0;
  for (const char of seed) {
    hash = (hash * 33 + char.charCodeAt(0)) % 997;
  }
  const points: string[] = [];
  for (let index = 0; index < 18; index += 1) {
    hash = (hash * 17 + 31) % 100;
    points.push(`${index * 14},${30 - (hash % 22)}`);
  }
  return points.join(" ");
}
