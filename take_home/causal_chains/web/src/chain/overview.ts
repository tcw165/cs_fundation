import type { CausalChain } from "./chain_port";
import { ordered_situations, situation_key, situation_layers } from "./layout";

const STEP_X = 26;
const LANE = 18;
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
    const layers = situation_layers(chain);
    const span = Math.max(STEP_X, Math.max(0, layers.length - 1) * STEP_X + WAVE);
    const tallest = layers.reduce((max, layer) => Math.max(max, layer.length), 1);
    const block = Math.max(WAVE * 2, (tallest - 1) * LANE + WAVE);
    if (cursor_x > ORIGIN && cursor_x + span > ROW_WIDTH) {
      cursor_x = ORIGIN;
      cursor_y = row_bottom + CHAIN_PAD_Y;
    }
    const highlight = is_latest(chain, latest);
    const by_key = new Map<string, OverviewNode>();
    layers.forEach((layer, rank) => {
      const layer_span = (layer.length - 1) * LANE;
      const top = cursor_y + (block - layer_span) / 2;
      layer.forEach((situation, lane) => {
        const key = situation_key(situation.situation_id, situation.version);
        const point = {
          key: `${index}-${key}`,
          cx: cursor_x + rank * STEP_X,
          cy: top + lane * LANE,
          latest: highlight,
        };
        nodes.push(point);
        by_key.set(key, point);
      });
    });
    const chain_right = cursor_x + span;
    const chain_bottom = cursor_y + block;
    max_x = Math.max(max_x, chain_right);
    row_bottom = Math.max(row_bottom, chain_bottom);
    cursor_x = chain_right + CHAIN_PAD_X;
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
