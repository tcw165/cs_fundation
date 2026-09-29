import type { CausalChain, ChainLink, ChainSituation } from "./chain_port";

export const NODE_WIDTH = 340;
export const NODE_HEIGHT = 132;
export const NODE_HEIGHT_OPEN = 340;
export const EDGE_GAP = 68;
export const EDGE_CARD_HEIGHT = 248;
export const LAYOUT_PAD = 8;

export type GraphSelection =
  | {
      kind: "situation";
      situation_id: string;
      version: number;
    }
  | {
      kind: "edge";
      from_situation_id: string;
      from_version: number;
      to_situation_id: string;
      to_version: number;
    };

export type LaidNode = {
  key: string;
  situation_id: string;
  version: number;
  x: number;
  y: number;
  width: number;
  height: number;
  expanded: boolean;
};

export type LaidEdge = {
  key: string;
  from_key: string;
  to_key: string;
  from_situation_id: string;
  from_version: number;
  to_situation_id: string;
  to_version: number;
  p: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  expanded: boolean;
  card: { x: number; y: number; width: number; height: number } | null;
};

export type ChainLayout = {
  nodes: LaidNode[];
  edges: LaidEdge[];
  width: number;
  height: number;
};

export function situation_key(situation_id: string, version: number): string {
  return `${situation_id}:${version}`;
}

export function edge_key(link: {
  from_situation_id: string;
  from_version: number;
  to_situation_id: string;
  to_version: number;
}): string {
  return `${link.from_situation_id}:${link.from_version}->${link.to_situation_id}:${link.to_version}`;
}

export function same_selection(left: GraphSelection | null, right: GraphSelection | null): boolean {
  if (left === null || right === null) {
    return left === right;
  }
  if (left.kind !== right.kind) {
    return false;
  }
  if (left.kind === "situation" && right.kind === "situation") {
    return left.situation_id === right.situation_id && left.version === right.version;
  }
  if (left.kind === "edge" && right.kind === "edge") {
    return edge_key(left) === edge_key(right);
  }
  return false;
}

export function toggle_selection(
  current: GraphSelection | null,
  next: GraphSelection,
): GraphSelection | null {
  if (same_selection(current, next)) {
    return null;
  }
  return next;
}

export function layout_chain(chain: CausalChain, selection: GraphSelection | null): ChainLayout {
  const ordered = ordered_situations(chain);
  const nodes: LaidNode[] = [];
  let cursor = LAYOUT_PAD;
  for (const situation of ordered) {
    const expanded = is_situation_selected(selection, situation);
    const height = expanded ? NODE_HEIGHT_OPEN : NODE_HEIGHT;
    nodes.push({
      key: situation_key(situation.situation_id, situation.version),
      situation_id: situation.situation_id,
      version: situation.version,
      x: LAYOUT_PAD,
      y: cursor,
      width: NODE_WIDTH,
      height,
      expanded,
    });
    cursor += height + EDGE_GAP;
  }

  const by_key = new Map(nodes.map((node) => [node.key, node]));
  const edges: LaidEdge[] = [];
  for (const link of chain.links) {
    const from = by_key.get(situation_key(link.from_situation_id, link.from_version));
    const to = by_key.get(situation_key(link.to_situation_id, link.to_version));
    if (from === undefined || to === undefined) {
      continue;
    }
    const expanded = is_edge_selected(selection, link);
    edges.push({
      key: edge_key(link),
      from_key: from.key,
      to_key: to.key,
      from_situation_id: link.from_situation_id,
      from_version: link.from_version,
      to_situation_id: link.to_situation_id,
      to_version: link.to_version,
      p: link.p,
      x1: from.x + from.width / 2,
      y1: from.y + from.height,
      x2: to.x + to.width / 2,
      y2: to.y,
      expanded,
      card: null,
    });
  }

  const open_edge = edges.find((edge) => edge.expanded);
  if (open_edge !== undefined) {
    const from = by_key.get(open_edge.from_key);
    const to = by_key.get(open_edge.to_key);
    if (from !== undefined && to !== undefined && to.y >= from.y) {
      const gap = to.y - (from.y + from.height);
      const needed = EDGE_CARD_HEIGHT + 28;
      const extra = Math.max(0, needed - gap);
      if (extra > 0) {
        for (const node of nodes) {
          if (node.y >= to.y) {
            node.y += extra;
          }
        }
      }
      open_edge.card = {
        x: from.x,
        y: from.y + from.height + 14,
        width: NODE_WIDTH,
        height: EDGE_CARD_HEIGHT,
      };
      for (const edge of edges) {
        const source = by_key.get(edge.from_key);
        const target = by_key.get(edge.to_key);
        if (source === undefined || target === undefined) {
          continue;
        }
        edge.x1 = source.x + source.width / 2;
        edge.y1 = source.y + source.height;
        edge.x2 = target.x + target.width / 2;
        edge.y2 = target.y;
      }
    }
  }

  const bottom = nodes.reduce((max, node) => Math.max(max, node.y + node.height), LAYOUT_PAD);
  return {
    nodes,
    edges,
    width: NODE_WIDTH + LAYOUT_PAD * 2,
    height: bottom + LAYOUT_PAD,
  };
}

export function ordered_situations(chain: CausalChain): ChainSituation[] {
  const start =
    chain.situations.find((situation) => situation.potential_factors !== undefined) ??
    chain.situations[0];
  if (start === undefined) {
    return [];
  }
  const by_key = new Map(
    chain.situations.map((situation) => [
      situation_key(situation.situation_id, situation.version),
      situation,
    ]),
  );
  const outgoing = new Map<string, ChainLink[]>();
  for (const link of chain.links) {
    const key = situation_key(link.from_situation_id, link.from_version);
    const list = outgoing.get(key) ?? [];
    list.push(link);
    outgoing.set(key, list);
  }
  const ordered: ChainSituation[] = [];
  const seen = new Set<string>();
  const queue = [start];
  while (queue.length > 0) {
    const current = queue.shift();
    if (current === undefined) {
      break;
    }
    const key = situation_key(current.situation_id, current.version);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    ordered.push(current);
    for (const link of outgoing.get(key) ?? []) {
      const next = by_key.get(situation_key(link.to_situation_id, link.to_version));
      if (next !== undefined) {
        queue.push(next);
      }
    }
  }
  for (const situation of chain.situations) {
    const key = situation_key(situation.situation_id, situation.version);
    if (!seen.has(key)) {
      ordered.push(situation);
    }
  }
  return ordered;
}

function is_situation_selected(selection: GraphSelection | null, situation: ChainSituation): boolean {
  return (
    selection?.kind === "situation" &&
    selection.situation_id === situation.situation_id &&
    selection.version === situation.version
  );
}

function is_edge_selected(selection: GraphSelection | null, link: ChainLink): boolean {
  return (
    selection?.kind === "edge" &&
    selection.from_situation_id === link.from_situation_id &&
    selection.from_version === link.from_version &&
    selection.to_situation_id === link.to_situation_id &&
    selection.to_version === link.to_version
  );
}
