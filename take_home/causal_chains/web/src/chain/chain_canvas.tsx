import { useEffect, useRef, useState } from "react";

import { bind_overlay_scroll, reveal_overlay_scrollbar } from "../theme/overlay_scroll";
import { chain_for_focus } from "./chain_select";
import type { CausalChain, ChainPort, ChainSituation } from "./chain_port";
import {
  edge_key,
  layout_chain,
  toggle_selection,
  type GraphSelection,
  type LaidEdge,
  type LaidNode,
} from "./layout";
import { ForkIcon } from "../shell/icons";
import { likelihood_label } from "./likelihood";
import { layout_overview } from "./overview";
import type { FocusTarget } from "./panel_state";

import "./chain.css";

export const chain_poll_ms = 2000;

export function ChainCanvas({
  focus,
  chain_port,
  on_fork,
}: {
  focus: FocusTarget;
  chain_port: ChainPort;
  on_fork?: (situation_id: string) => void;
}) {
  const [chains, set_chains] = useState<CausalChain[]>([]);
  const [chain, set_chain] = useState<CausalChain | null>(null);
  const [error, set_error] = useState<string | null>(null);
  const [loaded, set_loaded] = useState(false);
  const [selection, set_selection] = useState<GraphSelection | null>(selection_from_focus(focus));
  const host_ref = useRef<HTMLElement | null>(null);
  const scroll_ref = useRef<HTMLDivElement | null>(null);
  const chain_ref = useRef<CausalChain | null>(null);
  const focus_key = JSON.stringify(focus);

  useEffect(() => {
    set_selection(selection_from_focus(focus));
    const frame = window.requestAnimationFrame(() => {
      host_ref.current?.querySelector("[data-open='true']")?.scrollIntoView?.({
        block: "center",
        behavior: "smooth",
      });
    });
    return () => window.cancelAnimationFrame(frame);
    // The serialized key is the focus identity. A fresh object with the same target should not reset a toggle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focus_key]);

  useEffect(() => {
    let cancelled = false;
    let timer = 0;
    chain_ref.current = null;
    set_chains([]);
    set_chain(null);
    set_error(null);
    set_loaded(false);
    const poll = () => {
      chain_port
        .get_chains()
        .then((chains) => {
          if (cancelled) {
            return;
          }
          const next = chain_for_focus(chains, focus);
          chain_ref.current = next;
          set_chains(chains);
          set_chain(next);
          set_error(null);
          set_loaded(true);
        })
        .catch((reason: unknown) => {
          if (cancelled) {
            return;
          }
          if (chain_ref.current === null) {
            set_error(reason instanceof Error ? reason.message : "chain failed");
          }
          set_loaded(true);
        })
        .finally(() => {
          if (cancelled) {
            return;
          }
          timer = window.setTimeout(poll, chain_poll_ms);
        });
    };
    poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [chain_port, focus]);

  const panel_scrollable = chains.length > 0 || chain !== null;
  useEffect(() => {
    const node = scroll_ref.current;
    if (node === null) {
      return;
    }
    return bind_overlay_scroll(node);
  }, [panel_scrollable]);

  const title =
    focus.kind === "chain" || focus.kind === "case" ? focus.title : "Causal chain";
  const layout = chain === null ? null : layout_chain(chain, selection);
  const overview = layout_overview(chains, chain);

  return (
    <section className="chain-canvas" aria-label="causal chain" ref={host_ref}>
      <header className="panel-heading">
        <p className="panel-kicker">Causal chain</p>
        <h2>{title || "Saved chain"}</h2>
      </header>
      {error !== null ? <p className="panel-status">{error}</p> : null}
      {error === null && !loaded ? <p className="panel-status">loading</p> : null}
      {error === null && loaded && chain === null ? (
        <p className="panel-status">chain not found</p>
      ) : null}
      {chains.length > 0 || (chain !== null && layout !== null) ? (
        <div className="graph-scroll overlay-scroll" ref={scroll_ref}>
          {overview.nodes.length > 0 ? (
            <svg
              className="case-overview"
              viewBox={`0 0 ${overview.width} ${overview.height}`}
              role="img"
              aria-label="all cases"
            >
              {overview.edges.map((edge) => (
                <line
                  key={edge.key}
                  className={edge.latest ? "overview-edge is-latest" : "overview-edge"}
                  x1={edge.x1}
                  y1={edge.y1}
                  x2={edge.x2}
                  y2={edge.y2}
                />
              ))}
              {overview.nodes.map((node) => (
                <circle
                  key={node.key}
                  className={node.latest ? "overview-node is-latest" : "overview-node"}
                  data-latest={node.latest ? "true" : "false"}
                  cx={node.cx}
                  cy={node.cy}
                  r={node.latest ? 8 : 6}
                />
              ))}
            </svg>
          ) : null}
          {chain !== null && layout !== null ? (
          <div className="graph-canvas" style={{ width: layout.width, height: layout.height }}>
            <svg className="graph-edges" viewBox={`0 0 ${layout.width} ${layout.height}`}>
              {layout.edges.map((edge) => (
                <path key={edge.key} className="graph-edge" d={edge_path(edge)} />
              ))}
            </svg>
            {layout.nodes.map((node) => {
              const situation = chain.situations.find(
                (item) => item.situation_id === node.situation_id && item.version === node.version,
              );
              if (situation === undefined) {
                return null;
              }
              return (
                <SituationCard
                  key={node.key}
                  node={node}
                  situation={situation}
                  incoming_p={incoming_probability(chain, node)}
                  on_fork={on_fork}
                  on_toggle={() =>
                    set_selection((current) =>
                      toggle_selection(current, {
                        kind: "situation",
                        situation_id: node.situation_id,
                        version: node.version,
                      }),
                    )
                  }
                />
              );
            })}
            {layout.edges.map((edge) => (
              <button
                key={`${edge.key}:hit`}
                type="button"
                className="edge-hit"
                style={{ left: (edge.x1 + edge.x2) / 2, top: (edge.y1 + edge.y2) / 2 }}
                aria-label={`Open link ${edge.p}`}
                aria-expanded={edge.expanded}
                onClick={() =>
                  set_selection((current) =>
                    toggle_selection(current, {
                      kind: "edge",
                      from_situation_id: edge.from_situation_id,
                      from_version: edge.from_version,
                      to_situation_id: edge.to_situation_id,
                      to_version: edge.to_version,
                    }),
                  )
                }
              >
                {edge.p}
              </button>
            ))}
            {layout.edges.map((edge) => {
              const link = chain.links.find((item) => edge_key(item) === edge.key);
              if (!edge.expanded || edge.card === null || link === undefined) {
                return null;
              }
              return (
                <article
                  key={`${edge.key}:card`}
                  className="edge-card is-open overlay-scroll"
                  onScroll={(event) => reveal_overlay_scrollbar(event.currentTarget)}
                  style={{
                    transform: `translate(${edge.card.x}px, ${edge.card.y}px)`,
                    width: edge.card.width,
                    height: edge.card.height,
                  }}
                >
                  <p className="panel-kicker">Leads to</p>
                  <p className="edge-p">{edge.p}</p>
                  <p className="edge-likelihood">{likelihood_label(edge.p)}</p>
                  <div className="edge-gauge" aria-hidden="true">
                    <Gauge p={edge.p} />
                  </div>
                  <dl className="edge-inputs">
                    {link.inputs.map((input) => (
                      <div key={input.name}>
                        <dt>{input.name}</dt>
                        <dd>{input.desc}</dd>
                        <dd>{input.probability}</dd>
                      </div>
                    ))}
                  </dl>
                </article>
              );
            })}
          </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function SituationCard({
  node,
  situation,
  incoming_p,
  on_fork,
  on_toggle,
}: {
  node: LaidNode;
  situation: ChainSituation;
  incoming_p: string | null;
  on_fork?: (situation_id: string) => void;
  on_toggle: () => void;
}) {
  const kind = situation_kind(situation);
  const style = {
    transform: `translate(${node.x}px, ${node.y}px)`,
    width: node.width,
    height: node.height,
  };
  const header = (
    <>
      <span className={`kind-pill is-${kind}`}>{kind}</span>
      <span className="node-version">v{situation.version}</span>
      <strong className="node-title">{situation.title}</strong>
    </>
  );
  const fork =
    kind === "step" ? (
      <ForkButton on_fork={() => on_fork?.(situation.situation_id)} />
    ) : null;
  if (!node.expanded) {
    return (
      <div
        className="node-card"
        style={style}
        data-situation-id={node.situation_id}
        data-x={node.x}
        data-y={node.y}
        data-open="false"
      >
        <button
          type="button"
          className="node-face"
          aria-expanded={false}
          onClick={on_toggle}
        >
          {header}
          {incoming_p !== null ? <span className="node-p">{incoming_p}</span> : null}
        </button>
        {fork}
      </div>
    );
  }
  return (
    <article
      className="node-card is-open overlay-scroll"
      onScroll={(event) => reveal_overlay_scrollbar(event.currentTarget)}
      style={style}
      data-situation-id={node.situation_id}
      data-x={node.x}
      data-y={node.y}
      data-open="true"
    >
      <button type="button" className="node-toggle" aria-expanded onClick={on_toggle}>
        {header}
      </button>
      {fork}
      <div className="node-detail">
        <p>{situation.desc}</p>
        <dl className="node-meta">
          <div>
            <dt>situation_id</dt>
            <dd>{situation.situation_id}</dd>
          </div>
          <div>
            <dt>version</dt>
            <dd>{situation.version}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}

function ForkButton({ on_fork }: { on_fork: () => void }) {
  return (
    <button
      type="button"
      className="node-fork"
      aria-label="Fork from this situation"
      onClick={(event) => {
        event.stopPropagation();
        on_fork();
      }}
    >
      <ForkIcon />
    </button>
  );
}

function Gauge({ p }: { p: string }) {
  const value = Math.min(1, Math.max(0, Number(p) || 0));
  const angle = Math.PI * (1 - value);
  const x = 60 + Math.cos(angle) * 42;
  const y = 58 - Math.sin(angle) * 42;
  return (
    <svg viewBox="0 0 120 70">
      <path d="M18 58 A 42 42 0 0 1 102 58" fill="none" stroke="#2a2a30" strokeWidth="8" />
      <path d="M18 58 A 42 42 0 0 1 102 58" fill="none" stroke="#c6f25a" strokeWidth="8" strokeDasharray={`${value * 132} 132`} />
      <circle cx={x} cy={y} r="4" fill="#f4f4f5" />
    </svg>
  );
}

function edge_path(edge: LaidEdge): string {
  const mid_y = (edge.y1 + edge.y2) / 2;
  return `M ${edge.x1} ${edge.y1} C ${edge.x1} ${mid_y}, ${edge.x2} ${mid_y}, ${edge.x2} ${edge.y2}`;
}

function selection_from_focus(focus: FocusTarget): GraphSelection | null {
  if (focus.kind === "case") {
    return null;
  }
  if (focus.kind === "chain") {
    return {
      kind: "situation",
      situation_id: focus.root_situation_id,
      version: focus.root_version,
    };
  }
  return focus;
}

function situation_kind(situation: ChainSituation): "start" | "step" | "terminal" {
  if (situation.kind === "start") {
    return "start";
  }
  if (situation.kind === "terminal") {
    return "terminal";
  }
  return "step";
}

function incoming_probability(chain: CausalChain, node: LaidNode): string | null {
  const link = chain.links.find(
    (item) => item.to_situation_id === node.situation_id && item.to_version === node.version,
  );
  return link?.p ?? null;
}
