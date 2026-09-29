type IconProps = {
  class_name?: string;
};

export function LogoMark() {
  return (
    <svg className="rail-logo" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="10" fill="#16181d" />
      <circle cx="12" cy="14" r="5" fill="#ff7a59" />
      <circle cx="20" cy="13" r="4" fill="#7dffe4" />
      <circle cx="17" cy="21" r="4.5" fill="#c6f25a" />
    </svg>
  );
}

export function HomeIcon({ class_name }: IconProps) {
  return (
    <svg className={class_name} viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function LayersIcon({ class_name }: IconProps) {
  return (
    <svg className={class_name} viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 4 3.5 8.5 12 13l8.5-4.5zM6 12.2 3.5 13.5 12 18l8.5-4.5L18 12.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function GearIcon({ class_name }: IconProps) {
  return (
    <svg className={class_name} viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M12 3.5v2.2M12 18.3v2.2M3.5 12h2.2M18.3 12h2.2M6.2 6.2l1.6 1.6M16.2 16.2l1.6 1.6M17.8 6.2l-1.6 1.6M7.8 16.2l-1.6 1.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function LogoutIcon({ class_name }: IconProps) {
  return (
    <svg className={class_name} viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M10 7V5a1 1 0 0 1 1-1h7v16h-7a1 1 0 0 1-1-1v-2M4 12h10M11 8l4 4-4 4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="9" y="3" width="6" height="11" rx="3" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M6.5 11a5.5 5.5 0 0 0 11 0M12 16.5V21"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 12h12M13 6l6 6-6 6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
