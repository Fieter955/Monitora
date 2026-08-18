import type { SVGProps } from "react";

type IconName =
  | "dashboard"
  | "devices"
  | "alerts"
  | "reports"
  | "external"
  | "logout"
  | "menu"
  | "plus"
  | "edit"
  | "trash"
  | "download"
  | "refresh"
  | "map"
  | "topology"
  | "close"
  | "search";

const paths: Record<IconName, React.ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  devices: <><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></>,
  alerts: <><path d="M10.3 3.4 2.5 17a2 2 0 0 0 1.7 3h15.6a2 2 0 0 0 1.7-3L13.7 3.4a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/></>,
  reports: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/></>,
  external: <><path d="M15 3h6v6M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/></>,
  menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
  plus: <><path d="M12 5v14M5 12h14"/></>,
  edit: <><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></>,
  trash: <><path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v5M14 11v5"/></>,
  download: <><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></>,
  refresh: <><path d="M20 6v6h-6"/><path d="M4 18v-6h6"/><path d="M18.5 9A7 7 0 0 0 6.2 6.2L4 8M5.5 15A7 7 0 0 0 17.8 17.8L20 16"/></>,
  map: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z"/><path d="M9 3v15M15 6v15"/></>,
  topology: <><circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="12" cy="18" r="2"/><path d="m7 7 4 9M17 7l-4 9M7 6h10"/></>,
  close: <path d="m6 6 12 12M18 6 6 18"/>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
};

export function Icon({name, ...props}: {name: IconName} & SVGProps<SVGSVGElement>) {
  return <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" {...props}>{paths[name]}</svg>;
}
