import { useState, type FormEvent, type MouseEvent } from "react";

import { Icon } from "./Icon";

interface SaveProjectDialogProps {
  initialName: string;
  autosaveEnabled: boolean;
  saveAs: boolean;
  saving: boolean;
  error?: string;
  onSave: (name: string, autosaveEnabled: boolean) => Promise<void>;
  onClose: () => void;
}

export function SaveProjectDialog(props: SaveProjectDialogProps) {
  const [name, setName] = useState(props.initialName);
  const [autosave, setAutosave] = useState(props.autosaveEnabled);
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !props.saving) props.onClose();
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    await props.onSave(name.trim(), autosave);
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="save-project-title" aria-modal="true" className="export-dialog save-project-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon project-icon"><Icon name="save" size={22} /></div>
          <div><span className="section-kicker"><span /> FASE 7</span><h2 id="save-project-title">{props.saveAs ? "Salva progetto con nome" : "Salva progetto"}</h2><p>Formato Audio Track Studio · .atsproject</p></div>
          <button aria-label="Chiudi salvataggio progetto" className="dialog-close" disabled={props.saving} onClick={props.onClose} type="button"><Icon name="x" /></button>
        </header>
        <form onSubmit={(event) => void submit(event)}>
          <label className="field"><span>Nome progetto</span><input autoFocus maxLength={200} onChange={(event) => setName(event.target.value)} required value={name} /><small>Il file verrà salvato nella cartella progetti dell’applicazione.</small></label>
          <label className="project-toggle"><input checked={autosave} onChange={(event) => setAutosave(event.target.checked)} type="checkbox" /><span><strong>Abilita autosave e recovery</strong><small>Crea periodicamente uno snapshot atomico senza includere il file audio.</small></span></label>
          <div className="project-source-note"><Icon name="info" size={17} /><span><strong>L’audio non viene duplicato</strong><small>Alla riapertura ti verrà chiesto di ricollegare la sorgente originale.</small></span></div>
          {props.error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {props.error}</div>}
          <footer className="dialog-footer">
            <button className="button secondary" disabled={props.saving} onClick={props.onClose} type="button">Annulla</button>
            <button className="button primary" disabled={props.saving || !name.trim()} type="submit"><Icon name="save" size={16} /> {props.saving ? "Salvataggio…" : "Salva .atsproject"}</button>
          </footer>
        </form>
      </section>
    </div>
  );
}
