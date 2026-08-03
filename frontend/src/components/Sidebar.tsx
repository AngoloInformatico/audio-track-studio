import { Icon, type IconName } from "./Icon";

interface SidebarProps {
  backendOnline: boolean;
  onProjects: () => void;
  onAbout: () => void;
}

const items: Array<{ label: string; icon: IconName; action?: "projects" | "about" }> = [
  { label: "Editor", icon: "home" },
  { label: "Progetti", icon: "folder", action: "projects" },
  { label: "Informazioni", icon: "info", action: "about" },
];

export function Sidebar({ backendOnline, onProjects, onAbout }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand" aria-label="Audio Track Studio">
        <div className="brand-mark"><Icon name="waveform" size={24} /></div>
        <div><strong>Audio Track</strong><span>Studio</span></div>
      </div>
      <nav className="main-nav" aria-label="Navigazione principale">
        {items.map((item) => (
          <button
            className={item.label === "Editor" ? "nav-item active" : "nav-item"}
            key={item.label}
            onClick={item.action === "projects" ? onProjects : item.action === "about" ? onAbout : undefined}
            type="button"
          >
            <Icon name={item.icon} size={19} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className={`backend-pill ${backendOnline ? "online" : "offline"}`}>
          <span className="status-dot" />
          Backend {backendOnline ? "connesso" : "non raggiungibile"}
        </div>
        <span className="version">Release · v1.0.1</span>
      </div>
    </aside>
  );
}
