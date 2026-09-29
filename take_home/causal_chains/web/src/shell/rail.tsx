import { GearIcon, HomeIcon, LayersIcon, LogoMark, LogoutIcon } from "./icons";

export function Rail({
  server,
  panel_open,
}: {
  server: string;
  panel_open: boolean;
}) {
  const tone = server === "ok" ? "ok" : server === "loading" ? "loading" : "down";
  return (
    <aside className="rail" aria-label="primary">
      <LogoMark />
      <nav className="rail-nav">
        <button type="button" className="rail-button is-active" aria-label="Home" aria-current="page">
          <HomeIcon class_name="rail-icon" />
        </button>
        <button
          type="button"
          className={panel_open ? "rail-button is-active" : "rail-button"}
          aria-label="Causal chain"
          aria-pressed={panel_open}
        >
          <LayersIcon class_name="rail-icon" />
        </button>
      </nav>
      <div className="rail-spacer" />
      <button type="button" className="rail-button" aria-label="Settings">
        <GearIcon class_name="rail-icon" />
      </button>
      <button type="button" className="rail-button" aria-label="Log out">
        <LogoutIcon class_name="rail-icon" />
      </button>
      <span className={`rail-avatar is-${tone}`} role="status" aria-label={`server ${server}`}>
        <span className="rail-avatar-core" />
      </span>
    </aside>
  );
}
