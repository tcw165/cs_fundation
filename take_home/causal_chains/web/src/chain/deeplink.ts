export type Deeplink =
  | {
      route: "case";
      case_id: string;
    }
  | {
      route: "chain";
      root_situation_id: string;
      root_version: number;
      title: string;
    }
  | {
      route: "situation";
      situation_id: string;
      version: number;
    }
  | {
      route: "edge";
      from_situation_id: string;
      from_version: number;
      to_situation_id: string;
      to_version: number;
    };

export function parse_deeplink(link: string): Deeplink | null {
  const trimmed = link.trim();
  if (trimmed.startsWith("causal_chains://")) {
    return parse_scheme(trimmed);
  }
  return parse_legacy(trimmed);
}

export function deeplink_href(link: Deeplink): string {
  const params = new URLSearchParams();
  if (link.route === "case") {
    return `causal_chains://chain/${link.case_id}`;
  }
  if (link.route === "chain") {
    params.set("root_situation_id", link.root_situation_id);
    params.set("root_version", String(link.root_version));
    if (link.title !== "") {
      params.set("title", link.title);
    }
    return `causal_chains://chain?${params.toString()}`;
  }
  if (link.route === "situation") {
    params.set("situation_id", link.situation_id);
    params.set("version", String(link.version));
    return `causal_chains://situation?${params.toString()}`;
  }
  params.set("from_situation_id", link.from_situation_id);
  params.set("from_version", String(link.from_version));
  params.set("to_situation_id", link.to_situation_id);
  params.set("to_version", String(link.to_version));
  return `causal_chains://edge?${params.toString()}`;
}

function parse_scheme(link: string): Deeplink | null {
  const match = /^causal_chains:\/\/([^?#]+)(?:\?(.*))?$/.exec(link);
  if (match === null) {
    return null;
  }
  const route = (match[1] ?? "").replace(/\/$/, "");
  const params = new URLSearchParams(match[2] ?? "");
  const case_route = /^chain\/(.+)$/.exec(route);
  if (case_route !== null) {
    const case_id = case_route[1] ?? "";
    if (case_id === "") {
      return null;
    }
    return { route: "case", case_id };
  }
  if (route === "chain") {
    const root_situation_id = params.get("root_situation_id") ?? "";
    const root_version = number_param(params, "root_version");
    if (root_situation_id === "" || root_version === null) {
      return null;
    }
    return {
      route: "chain",
      root_situation_id,
      root_version,
      title: params.get("title") ?? "",
    };
  }
  if (route === "situation") {
    const situation_id = params.get("situation_id") ?? "";
    const version = number_param(params, "version");
    if (situation_id === "" || version === null) {
      return null;
    }
    return { route: "situation", situation_id, version };
  }
  if (route === "edge") {
    const from_situation_id = params.get("from_situation_id") ?? "";
    const to_situation_id = params.get("to_situation_id") ?? "";
    const from_version = number_param(params, "from_version");
    const to_version = number_param(params, "to_version");
    if (
      from_situation_id === "" ||
      to_situation_id === "" ||
      from_version === null ||
      to_version === null
    ) {
      return null;
    }
    return {
      route: "edge",
      from_situation_id,
      from_version,
      to_situation_id,
      to_version,
    };
  }
  return null;
}

function parse_legacy(link: string): Deeplink | null {
  let url: URL;
  try {
    url = new URL(link, "http://local");
  } catch {
    return null;
  }
  const parts = url.pathname.split("/").filter((part) => part !== "");
  if (parts[0] !== "chain") {
    return null;
  }
  const root_situation_id = parts[1] ?? "";
  const root_version = Number(parts[2] ?? "");
  if (root_situation_id === "" || !Number.isFinite(root_version)) {
    return null;
  }
  return {
    route: "chain",
    root_situation_id,
    root_version,
    title: url.searchParams.get("title") ?? "",
  };
}

function number_param(params: URLSearchParams, key: string): number | null {
  const raw = params.get(key);
  if (raw === null || raw === "") {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}
