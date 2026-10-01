import type { CausalChain } from "./chain_port";
import { ordered_situations, situation_key } from "./layout";

const STEP_X = 26;
const WAVE = 14;
const CHAIN_PAD_X = 40;
const CHAIN_PAD_Y = 36;
const ROW_WIDTH = 520;
const ORIGIN = 18;

export type OverviewNode = {
  key: string;
  cx: number;
  cy: number;
  latest: boolean;
};

export type OverviewEdge = {
  key: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  latest: boolean;
};

export type OverviewLayout = {
  nodes: OverviewNode[];
  edges: OverviewEdge[];
  width: number;
  height: number;
};

export function layout_overview(
  chains: CausalChain[],
  latest: CausalChain | null,
): OverviewLayout {
  const nodes: OverviewNode[] = [];
  const edges: OverviewEdge[] = [];
  let cursor_x = ORIGIN;
  let cursor_y = ORIGIN;
  let row_bottom = ORIGIN;
  let max_x = ORIGIN;
  chains.forEach((chain, index) => {
    const situations = ordered_situations(chain);
    const span = Math.max(STEP_X, (situations.length - 1) * STEP_X + WAVE);
    if (cursor_x > ORIGIN && cursor_x + span > ROW_WIDTH) {
      cursor_x = ORIGIN;
      cursor_y = row_bottom + CHAIN_PAD_Y;
    }
    const highlight = is_latest(chain, latest);
    const points = situations.map((situation, step) => {
      const point = {
        key: `${index}-${situation_key(situation.situation_id, situation.version)}`,
        cx: cursor_x + step * STEP_X,
        cy: cursor_y + Math.round(Math.sin(step * 0.9) * WAVE) + WAVE,
        latest: highlight,
      };
      nodes.push(point);
      return point;
    });
    const chain_right = cursor_x + span;
    const chain_bottom = cursor_y + WAVE * 2 + 8;
    max_x = Math.max(max_x, chain_right);
    row_bottom = Math.max(row_bottom, chain_bottom);
    cursor_x = chain_right + CHAIN_PAD_X;
    const by_key = new Map(
      situations.map((situation, step) => [
        situation_key(situation.situation_id, situation.version),
        points[step],
      ]),
    );
    for (const link of chain.links) {
      const from = by_key.get(situation_key(link.from_situation_id, link.from_version));
      const to = by_key.get(situation_key(link.to_situation_id, link.to_version));
      if (from === undefined || to === undefined) {
        continue;
      }
      edges.push({
        key: `${from.key}->${to.key}`,
        x1: from.cx,
        y1: from.cy,
        x2: to.cx,
        y2: to.cy,
        latest: highlight,
      });
    }
  });
  const width = Math.max(ROW_WIDTH, max_x + ORIGIN);
  const height = Math.max(ORIGIN * 2, row_bottom + ORIGIN);
  return { nodes, edges, width, height };
}

function is_latest(chain: CausalChain, latest: CausalChain | null): boolean {
  if (latest === null) {
    return false;
  }
  if (chain.case_id !== undefined && latest.case_id !== undefined) {
    return chain.case_id === latest.case_id;
  }
  const chain_start = ordered_situations(chain)[0];
  const latest_start = ordered_situations(latest)[0];
  if (chain_start === undefined || latest_start === undefined) {
    return false;
  }
  return (
    chain_start.situation_id === latest_start.situation_id &&
    chain_start.version === latest_start.version
  );
}
