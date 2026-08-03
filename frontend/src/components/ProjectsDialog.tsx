import { useEffect, useRef, useState, type MouseEvent } from "react";

import {
  applyProject,
  closeAudio,
  getRecentProjects,
  getRecoveryProjects,
  inspectProject,
  openAudio,
  prepareProject,
} from "../services/api";
import type {
  AudioSession,
  ProjectApplyResult,
  ProjectPreview,
  ProjectSummary,
} from "../types/audio";
import { formatBytes, formatTime } from "../utils/format";
import { Icon } from "./Icon";

interface ProjectsDialogProps {
  hasSession: boolean;
  onOpened: (session: AudioSession, applied: ProjectApplyResult, preview: ProjectPreview) => void;
  onNew: () => void;
  onSaveAs: () => void;
  onClose: () => void;
}

export function ProjectsDialog(props: ProjectsDialogProps) {
  const [recent, setRecent] = useState<ProjectSummary[]>([]);
  const [recoveries, setRecoveries] = useState<ProjectSummary[]>([]);
  const [preview, setPreview] = useState<ProjectPreview>();
  const [sourceFile, setSourceFile] = useState<File>();
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string>();
  const projectInput = useRef<HTMLInputElement>(null);
  const sourceInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    Promise.all([getRecentProjects(), getRecoveryProjects()])
      .then(([saved, recovery]) => { if (active) { setRecent(saved); setRecoveries(recovery); } })
      .catch((reason: unknown) => { if (active) setError(readMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const inspectFile = async (file: File) => {
    setBusy(true);
    setError(undefined);
    try {
      setPreview(await inspectProject(file));
      setSourceFile(undefined);
    } catch (reason) {
      setError(readMessage(reason));
    } finally {
      setBusy(false);
    }
  };
  const prepare = async (summary: ProjectSummary) => {
    setBusy(true);
    setError(undefined);
    try {
      setPreview(await prepareProject(
        summary.kind === "saved" ? summary.id : undefined,
        summary.kind === "recovery" ? summary.id : undefined,
      ));
      setSourceFile(undefined);
    } catch (reason) {
      setError(readMessage(reason));
    } finally {
      setBusy(false);
    }
  };
  const openPrepared = async () => {
    if (!preview || !sourceFile) return;
    if (props.hasSession && !window.confirm("Sostituire il progetto corrente? Le modifiche non salvate potrebbero andare perse.")) return;
    setBusy(true);
    setProgress(0);
    setError(undefined);
    let session: AudioSession | undefined;
    try {
      session = await openAudio(sourceFile, setProgress);
      const applied = await applyProject(preview.token, session.id);
      props.onOpened(session, applied, preview);
      props.onClose();
    } catch (reason) {
      if (session) await closeAudio(session.id);
      setError(readMessage(reason));
    } finally {
      setBusy(false);
    }
  };
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !busy) props.onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="projects-title" aria-modal="true" className="export-dialog projects-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon project-icon"><Icon name="folder" size={22} /></div>
          <div><span className="section-kicker"><span /> FASE 7</span><h2 id="projects-title">Progetti</h2><p>Salvataggi, recenti e recovery</p></div>
          <button aria-label="Chiudi progetti" className="dialog-close" disabled={busy} onClick={props.onClose} type="button"><Icon name="x" /></button>
        </header>

        <input accept=".atsproject,application/json" className="project-hidden-input" onChange={(event) => { const file = event.currentTarget.files?.item(0); if (file) void inspectFile(file); event.currentTarget.value = ""; }} ref={projectInput} type="file" />
        <input accept=".flac,.wav,.mp3,.m4a,.aac,audio/*" className="project-hidden-input" onChange={(event) => setSourceFile(event.currentTarget.files?.item(0) ?? undefined)} ref={sourceInput} type="file" />

        {preview ? (
          <ProjectRelink
            busy={busy}
            onBack={() => { setPreview(undefined); setSourceFile(undefined); setError(undefined); }}
            onChooseSource={() => sourceInput.current?.click()}
            onOpen={() => void openPrepared()}
            preview={preview}
            progress={progress}
            sourceFile={sourceFile}
          />
        ) : (
          <div className="project-hub">
            <div className="project-actions">
              <button className="project-action-card" disabled={busy} onClick={() => projectInput.current?.click()} type="button"><Icon name="upload" size={22} /><span><strong>Apri progetto</strong><small>Seleziona un file .atsproject</small></span></button>
              <button className="project-action-card" disabled={!props.hasSession || busy} onClick={props.onSaveAs} type="button"><Icon name="save" size={22} /><span><strong>Salva con nome</strong><small>Crea una nuova copia del progetto</small></span></button>
              <button className="project-action-card" disabled={busy} onClick={() => { if (!props.hasSession || window.confirm("Creare un nuovo progetto? Le modifiche non salvate potrebbero andare perse.")) { props.onNew(); props.onClose(); } }} type="button"><Icon name="plus" size={22} /><span><strong>Nuovo progetto</strong><small>Chiude la sessione corrente</small></span></button>
            </div>
            {loading ? <div className="dialog-loading"><Icon name="activity" /> Lettura progetti recenti…</div> : <ProjectLists onPrepare={(item) => void prepare(item)} recent={recent} recoveries={recoveries} />}
          </div>
        )}
        {error && <div className="export-error project-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
      </section>
    </div>
  );
}

function ProjectLists({ recent, recoveries, onPrepare }: { recent: ProjectSummary[]; recoveries: ProjectSummary[]; onPrepare: (item: ProjectSummary) => void }) {
  return (
    <div className="project-lists">
      {recoveries.length > 0 && <ProjectSection items={recoveries} label="RECOVERY DISPONIBILI" onPrepare={onPrepare} />}
      <ProjectSection items={recent} label="PROGETTI RECENTI" onPrepare={onPrepare} />
    </div>
  );
}

function ProjectSection({ label, items, onPrepare }: { label: string; items: ProjectSummary[]; onPrepare: (item: ProjectSummary) => void }) {
  return (
    <section className="project-section">
      <span className="section-kicker"><span /> {label}</span>
      {items.length ? <div className="project-list">{items.map((item) => <div className="project-row-wrap" key={`${item.kind}-${item.id}`}><button className="project-row" onClick={() => onPrepare(item)} type="button"><span className="project-row-icon"><Icon name={item.kind === "recovery" ? "activity" : "folder"} size={18} /></span><span><strong>{item.name}</strong><small>{item.source_name} · {item.track_count} tracce</small></span><span className="project-row-meta"><strong>{new Date(item.updated_at).toLocaleDateString("it-IT")}</strong><small>{item.has_covers ? "Cover incluse" : item.kind === "recovery" ? "Ripristino" : "Solo metadati"}</small></span></button>{item.download_url && <a aria-label={`Scarica ${item.name}`} className="project-download" download href={item.download_url} title="Scarica file .atsproject"><Icon name="download" size={16} /></a>}</div>)}</div> : <div className="project-empty">Nessun progetto salvato.</div>}
    </section>
  );
}

function ProjectRelink({ preview, sourceFile, busy, progress, onChooseSource, onOpen, onBack }: { preview: ProjectPreview; sourceFile?: File; busy: boolean; progress: number; onChooseSource: () => void; onOpen: () => void; onBack: () => void }) {
  return (
    <div className="project-relink">
      <div className="project-preview-summary"><div><span>Progetto</span><strong>{preview.name}</strong></div><div><span>Tracce</span><strong>{preview.track_count}</strong></div><div><span>Cover</span><strong>{preview.has_covers ? "Incluse" : "Nessuna"}</strong></div></div>
      <div className="relink-source"><Icon name="fileAudio" size={26} /><span><small>SORGENTE ATTESA</small><strong>{preview.source.name}</strong><p>{preview.source.format} · {formatTime(preview.source.duration_seconds, false)} · {formatBytes(preview.source.size_bytes)}</p></span></div>
      <div className="relink-explanation"><Icon name="info" size={17} /> Il progetto non duplica l’audio. Se il file è stato spostato, seleziona la nuova posizione: dimensione, durata e impronta SHA-256 verranno verificate prima del ripristino.</div>
      <button className="button secondary relink-button" disabled={busy} onClick={onChooseSource} type="button"><Icon name="upload" size={16} /> {sourceFile ? sourceFile.name : "Ricollega file audio"}</button>
      {busy && progress > 0 && <div className="project-upload-progress"><div className="progress-track"><span style={{ width: `${progress}%` }} /></div><small>Importazione sorgente {progress}%</small></div>}
      <footer className="dialog-footer"><button className="button secondary" disabled={busy} onClick={onBack} type="button">Indietro</button><button className="button primary" disabled={!sourceFile || busy} onClick={onOpen} type="button"><Icon name="folder" size={16} /> {busy ? "Ripristino…" : "Apri progetto"}</button></footer>
    </div>
  );
}

function readMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Errore durante la gestione del progetto.";
}
