import type { ReactNode, SVGProps } from "react";

export type IconName =
  | "activity"
  | "check"
  | "chevronDown"
  | "clock"
  | "download"
  | "fileAudio"
  | "folder"
  | "help"
  | "home"
  | "info"
  | "moon"
  | "plus"
  | "pause"
  | "play"
  | "save"
  | "search"
  | "settings"
  | "skipBack"
  | "skipForward"
  | "sparkles"
  | "split"
  | "square"
  | "sun"
  | "trash"
  | "upload"
  | "volume"
  | "waveform"
  | "x";

const paths: Record<IconName, ReactNode> = {
  activity: <><path d="M3 12h4l2.5-7 5 14 2.5-7h4" /></>,
  check: <path d="m5 12 4 4L19 6" />,
  chevronDown: <path d="m7 10 5 5 5-5" />,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4" /><path d="M5 19h14" /></>,
  fileAudio: <><path d="M6 3h8l4 4v14H6z" /><path d="M14 3v5h5M9 15v-3l5-1v3" /><circle cx="8.5" cy="16" r="1.5" /><circle cx="13.5" cy="15" r="1.5" /></>,
  folder: <path d="M3 6.5h7l2 2h9v10.5H3z" />,
  help: <><circle cx="12" cy="12" r="9" /><path d="M9.8 9a2.3 2.3 0 1 1 3.2 2.1c-.7.3-1 .8-1 1.4v.5M12 17h.01" /></>,
  home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10M9 20v-6h6v6" /></>,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7h.01" /></>,
  moon: <path d="M20 15.5A8 8 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z" />,
  plus: <path d="M12 5v14M5 12h14" />,
  pause: <><path d="M9 7v10M15 7v10" /></>,
  play: <path d="m9 6 9 6-9 6z" />,
  save: <><path d="M5 3h12l2 2v16H5z" /><path d="M8 3v6h8V3M8 21v-7h8v7" /></>,
  search: <><circle cx="11" cy="11" r="7" /><path d="m16 16 4 4" /></>,
  settings: <><circle cx="12" cy="12" r="3" /><path d="M19 13.5v-3l-2-.7-.7-1.7.9-1.9-2.1-2.1-1.9.9-1.7-.7-.7-2h-3l-.7 2-1.7.7-1.9-.9-2.1 2.1.9 1.9-.7 1.7-2 .7v3l2 .7.7 1.7-.9 1.9 2.1 2.1 1.9-.9 1.7.7.7 2h3l.7-2 1.7-.7 1.9.9 2.1-2.1-.9-1.9.7-1.7z" /></>,
  skipBack: <><path d="M6 6v12M18 7l-8 5 8 5z" /></>,
  skipForward: <><path d="M18 6v12M6 7l8 5-8 5z" /></>,
  sparkles: <><path d="m12 3 1.4 3.6L17 8l-3.6 1.4L12 13l-1.4-3.6L7 8l3.6-1.4zM18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8zM5 13l.6 1.4L7 15l-1.4.6L5 17l-.6-1.4L3 15l1.4-.6z" /></>,
  split: <><path d="M12 3v18M8 7 4 3M8 17l-4 4M16 7l4-4M16 17l4 4" /><circle cx="12" cy="12" r="2" /></>,
  square: <rect x="7" y="7" width="10" height="10" rx="1" />,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  trash: <><path d="M5 7h14M9 7V4h6v3M7 7l1 14h8l1-14M10 11v6M14 11v6" /></>,
  upload: <><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" /><path d="M5 14v6h14v-6" /></>,
  volume: <><path d="M4 10v4h4l5 4V6l-5 4z" /><path d="M16 9a4 4 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11" /></>,
  waveform: <path d="M3 12h2l1-5 2 10 2-13 2 16 2-12 2 8 2-5 1 1h2" />,
  x: <path d="M6 6l12 12M18 6 6 18" />,
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 20, ...props }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.7"
      viewBox="0 0 24 24"
      width={size}
      {...props}
    >
      {paths[name]}
    </svg>
  );
}
