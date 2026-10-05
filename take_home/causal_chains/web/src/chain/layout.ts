import type { CausalChain, ChainLink, ChainSituation } from "./chain_port";

export const NODE_WIDTH = 340;
export const NODE_HEIGHT = 220;
export const NODE_HEIGHT_OPEN = 340;
export const EDGE_GAP = 128;
export const EDGE_CARD_HEIGHT = 248;
export const LAYOUT_PAD = 8;
export const COLUMN_GAP = 56;

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

export function situation_layers(chain: CausalChain): ChainSituation[][] {
  const by_key = new Map(
    chain.situations.map((situation) => [
      situation_key(situation.situation_id, situation.version),
      situation,
    ]),
  );
  const incoming = new Map<string, string[]>();
  const outgoing = new Map<string, string[]>();
  for (const situation of chain.situations) {
    const key = situation_key(situation.situation_id, situation.version);
    incoming.set(key, []);
    outgoing.set(key, []);
  }
  for (const link of chain.links) {
    const from = situation_key(link.from_situation_id, link.from_version);
    const to = situation_key(link.to_situation_id, link.to_version);
    if (!by_key.has(from) || !by_key.has(to)) {
      continue;
    }
    outgoing.get(from)?.push(to);
    incoming.get(to)?.push(from);
  }

  const rank = new Map<string, number>();
  const remaining = new Map<string, number>();
  const queue: string[] = [];
  for (const [key, parents] of incoming) {
    remaining.set(key, parents.length);
    if (parents.length === 0) {
      rank.set(key, 0);
      queue.push(key);
    }
  }
  let head = 0;
  while (head < queue.length) {
    const key = queue[head];
    head += 1;
    const here = rank.get(key) ?? 0;
    for (const next of outgoing.get(key) ?? []) {
      rank.set(next, Math.max(rank.get(next) ?? 0, here + 1));
      const left = (remaining.get(next) ?? 1) - 1;
      remaining.set(next, left);
      if (left === 0) {
        queue.push(next);
      }
    }
  }
  for (const situation of chain.situations) {
    const key = situation_key(situation.situation_id, situation.version);
    if (!rank.has(key)) {
      rank.set(key, 0);
    }
  }

  const depth = Math.max(0, ...rank.values());
  const layers: ChainSituation[][] = Array.from({ length: depth + 1 }, () => []);
  for (const situation of chain.situations) {
    const key = situation_key(situation.situation_id, situation.version);
    layers[rank.get(key) ?? 0]?.push(situation);
  }
  sweep_layers(layers, incoming, outgoing);
  return layers.filter((layer) => layer.length > 0);
}

export function layout_chain(chain: CausalChain, selection: GraphSelection | null): ChainLayout {
  const layers = situation_layers(chain);
  const widest = layers.reduce(
    (max, layer) => Math.max(max, row_width(layer.length)),
    NODE_WIDTH,
  );
  const nodes: LaidNode[] = [];
  let cursor = LAYOUT_PAD;
  for (const layer of layers) {
    const offset = LAYOUT_PAD + (widest - row_width(layer.length)) / 2;
    let row_height = 0;
    layer.forEach((situation, index) => {
      const expanded = is_situation_selected(selection, situation);
      const height = expanded ? NODE_HEIGHT_OPEN : NODE_HEIGHT;
      row_height = Math.max(row_height, height);
      nodes.push({
        key: situation_key(situation.situation_id, situation.version),
        situation_id: situation.situation_id,
        version: situation.version,
        x: offset + index * (NODE_WIDTH + COLUMN_GAP),
        y: cursor,
        width: NODE_WIDTH,
        height,
        expanded,
      });
    });
    cursor += row_height + EDGE_GAP;
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
    if (from !== undefined && to !== undefined && to.y > from.y) {
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
  const right = nodes.reduce((max, node) => Math.max(max, node.x + node.width), LAYOUT_PAD);
  return {
    nodes,
    edges,
    width: right + LAYOUT_PAD,
    height: bottom + LAYOUT_PAD,
  };
}

function row_width(count: number): number {
  if (count <= 0) {
    return 0;
  }
  return count * NODE_WIDTH + (count - 1) * COLUMN_GAP;
}

function sweep_layers(
  layers: ChainSituation[][],
  incoming: Map<string, string[]>,
  outgoing: Map<string, string[]>,
): void {
  for (let pass = 0; pass < 4; pass += 1) {
    for (let depth = 1; depth < layers.length; depth += 1) {
      const previous = layers[depth - 1] ?? [];
      const layer = layers[depth];
      if (layer === undefined) {
        continue;
      }
      layers[depth] = [...layer].sort((left, right) =>
        compare_by_anchor(left, right, layer, previous, incoming),
      );
    }
    for (let depth = layers.length - 2; depth >= 0; depth -= 1) {
      const next = layers[depth + 1] ?? [];
      const layer = layers[depth];
      if (layer === undefined) {
        continue;
      }
      layers[depth] = [...layer].sort((left, right) =>
        compare_by_anchor(left, right, layer, next, outgoing),
      );
    }
  }
}

function compare_by_anchor(
  left: ChainSituation,
  right: ChainSituation,
  layer: ChainSituation[],
  adjacent: ChainSituation[],
  links: Map<string, string[]>,
): number {
  const left_key = situation_key(left.situation_id, left.version);
  const right_key = situation_key(right.situation_id, right.version);
  const left_anchor = median_anchor(links.get(left_key) ?? [], adjacent, index_of(layer, left_key));
  const right_anchor = median_anchor(
    links.get(right_key) ?? [],
    adjacent,
    index_of(layer, right_key),
  );
  if (left_anchor !== right_anchor) {
    return left_anchor - right_anchor;
  }
  if (left_key < right_key) {
    return -1;
  }
  if (left_key > right_key) {
    return 1;
  }
  return 0;
}

function median_anchor(keys: string[], layer: ChainSituation[], fallback: number): number {
  const indexes = keys
    .map((key) => index_of(layer, key))
    .filter((index) => index >= 0)
    .sort((left, right) => left - right);
  if (indexes.length === 0) {
    return fallback;
  }
  const mid = (indexes.length - 1) / 2;
  const lower = indexes[Math.floor(mid)] ?? fallback;
  const upper = indexes[Math.ceil(mid)] ?? lower;
  return (lower + upper) / 2;
}

function index_of(layer: ChainSituation[], key: string): number {
  return layer.findIndex(
    (situation) => situation_key(situation.situation_id, situation.version) === key,
  );
}

export function ordered_situations(chain: CausalChain): ChainSituation[] {
  const start =
    chain.situations.find((situation) => situation.kind === "start") ??
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
