import type { TurnDescriptor } from "./chat_port";

export function turn_is_live(turn: TurnDescriptor | null | undefined): boolean {
  return (turn?.processing.length ?? 0) > 0;
}
