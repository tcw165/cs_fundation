export const FOLLOW_SLACK = 48;

export function distance_from_bottom(
  scroll_top: number,
  scroll_height: number,
  client_height: number,
): number {
  return scroll_height - scroll_top - client_height;
}

export function still_following(distance: number, slack = FOLLOW_SLACK): boolean {
  return distance <= slack;
}
