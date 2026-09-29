import { parse_deeplink } from "./deeplink";
import type { DeeplinkCard } from "./chain_port";

export type FocusTarget =
  | {
      kind: "chain";
      root_situation_id: string;
      root_version: number;
      title: string;
    }
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

export type PanelState = {
  open: boolean;
  focus: FocusTarget | null;
};

export const folded_panel: PanelState = { open: false, focus: null };

export function panel_from_link(link: string): PanelState | null {
  const parsed = parse_deeplink(link);
  if (parsed === null) {
    return null;
  }
  if (parsed.route === "chain") {
    return {
      open: true,
      focus: {
        kind: "chain",
        root_situation_id: parsed.root_situation_id,
        root_version: parsed.root_version,
        title: parsed.title,
      },
    };
  }
  if (parsed.route === "situation") {
    return {
      open: true,
      focus: {
        kind: "situation",
        situation_id: parsed.situation_id,
        version: parsed.version,
      },
    };
  }
  return {
    open: true,
    focus: {
      kind: "edge",
      from_situation_id: parsed.from_situation_id,
      from_version: parsed.from_version,
      to_situation_id: parsed.to_situation_id,
      to_version: parsed.to_version,
    },
  };
}

export function card_from_focus(focus: FocusTarget | null): DeeplinkCard | null {
  if (focus === null) {
    return null;
  }
  if (focus.kind === "chain") {
    return {
      title: focus.title,
      root_situation_id: focus.root_situation_id,
      root_version: focus.root_version,
    };
  }
  if (focus.kind === "situation") {
    return {
      title: "",
      root_situation_id: focus.situation_id,
      root_version: focus.version,
    };
  }
  return {
    title: "",
    root_situation_id: focus.from_situation_id,
    root_version: focus.from_version,
  };
}
