export type DeeplinkCard = {
  title: string;
  root_situation_id: string;
  root_version: number;
};

export type ChainSituation = {
  situation_id: string;
  version: number;
  kind: "start" | "situation" | "terminal";
  created_timestamp: string;
  title: string;
  desc: string;
  remained_drivers: string[];
  original_ask?: string;
};

export type ChainInput = {
  name: string;
  desc: string;
  probability: number;
};

export type ChainLink = {
  from_situation_id: string;
  from_version: number;
  to_situation_id: string;
  to_version: number;
  p: string;
  inputs: ChainInput[];
};

export type CausalChain = {
  case_id?: string;
  situations: ChainSituation[];
  links: ChainLink[];
};

export type ChainPort = {
  get_chains: () => Promise<CausalChain[]>;
};
