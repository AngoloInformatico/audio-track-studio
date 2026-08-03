import type { ChangeEvent } from "react";

import type { ProjectActivity } from "../hooks/useProjectAutosave";
import type { ThemePreference } from "../hooks/useTheme";
import { Icon } from "./Icon";

interface TopbarProps {
  fileName?: string;
  canExport: boolean;
  canAnalyze: boolean;
  canRecognize: boolean;
  canSave: boolean;
  modalOpen: boolean;
  onOpen: () => void;
  onExport: () => void;
  onAnalyze: () => void;
  onRecognize: () => void;
  onSave: () => void;
  projectName?: string;
  projectActivity?: ProjectActivity;
  preference: ThemePreference;
  onThemeChange: (theme: ThemePreference) => void;
}

export function Topbar({ fileName, projectName, projectActivity, canAnalyze, canExport, canRecognize, canSave, modalOpen, onOpen, onAnalyze, onExport, onRecognize, onSave, preference, onThemeChange }: TopbarProps) {
  const chooseTheme = (event: ChangeEvent<HTMLSelectElement>) => {
    onThemeChange(event.target.value as ThemePreference);
  };

  return (
    <header className="topbar">
      <div className="project-heading">
        <span className="eyebrow">PROGETTO CORRENTE</span>
        <strong title={projectName ?? fileName}>{projectName ?? fileName ?? "Nessun audio aperto"}</strong>
        {projectName && fileName && <small title={fileName}>{fileName}</small>}
        {projectActivity && <span className={`project-activity ${projectActivity}`}>{activityLabel(projectActivity)}</span>}
      </div>
      <div className="toolbar" aria-label="Azioni progetto">
        <button className="button secondary" disabled={modalOpen} onClick={onOpen} type="button">
          <Icon name="upload" size={17} /> Apri
        </button>
        <button className="button ghost" disabled={!canSave || modalOpen || projectActivity === "saving"} onClick={onSave} title="Salva progetto" type="button">
          <Icon name="save" size={17} /> Salva
        </button>
        <span className="toolbar-divider" />
        <button className="button ghost" disabled={!canAnalyze || modalOpen} onClick={onAnalyze} type="button">
          <Icon name="activity" size={17} /> Analizza
        </button>
        <button className="button ghost" disabled={!canRecognize || modalOpen} onClick={onRecognize} type="button">
          <Icon name="search" size={17} /> Riconosci
        </button>
        <button className="button primary" disabled={!canExport || modalOpen} onClick={onExport} type="button">
          <Icon name="download" size={17} /> Esporta
        </button>
        <label className="theme-select" title="Tema interfaccia">
          <Icon name={preference === "dark" ? "moon" : "sun"} size={17} />
          <select aria-label="Tema" onChange={chooseTheme} value={preference}>
            <option value="light">Chiaro</option>
            <option value="dark">Scuro</option>
            <option value="system">Sistema</option>
          </select>
          <Icon name="chevronDown" size={14} />
        </label>
      </div>
    </header>
  );
}

function activityLabel(activity: ProjectActivity): string {
  if (activity === "saving") return "Salvataggio…";
  if (activity === "saved") return "Salvato";
  if (activity === "autosaved") return "Autosave aggiornato";
  return "Salvataggio non riuscito";
}
