import { useState, type DragEvent } from "react";

import type { UploadState } from "../types/audio";
import { Icon } from "./Icon";

interface ImportPanelProps {
  backendOnline: boolean;
  upload: UploadState;
  onFile: (file: File) => void;
  onOpen: () => void;
}

export function ImportPanel({ backendOnline, upload, onFile, onOpen }: ImportPanelProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files.item(0);
    if (file) onFile(file);
  };

  const busy = upload.status === "uploading";
  return (
    <section className="welcome-panel">
      <div className="welcome-copy">
        <span className="section-kicker"><span /> EDITOR AUDIO LOCALE</span>
        <h1>Trasforma un lungo mix<br />in tracce curate.</h1>
        <p>
          Importa un file audio, osserva la waveform e ascolta ogni passaggio. Il sorgente originale
          rimane sempre intatto.
        </p>
        <div className="format-row" aria-label="Formati supportati">
          {['FLAC', 'MP3', 'WAV', 'M4A', 'AAC'].map((format) => <span key={format}>{format}</span>)}
        </div>
      </div>
      <div
        className={`drop-zone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <div className="drop-icon"><Icon name="fileAudio" size={34} /></div>
        {busy ? (
          <>
            <h2>Importazione in corso…</h2>
            <p>Il file viene copiato nella cache di lavoro senza caricarlo interamente in memoria.</p>
            <div className="progress-track" role="progressbar" aria-valuenow={upload.progress}>
              <span style={{ width: `${upload.progress}%` }} />
            </div>
            <strong className="progress-label">{upload.progress}%</strong>
          </>
        ) : (
          <>
            <h2>Trascina qui il tuo audio</h2>
            <p>oppure selezionalo dal computer</p>
            <button className="button primary large" disabled={!backendOnline} onClick={onOpen} type="button">
              <Icon name="upload" size={18} /> Scegli file audio
            </button>
            {!backendOnline && <small>Avvia il backend locale per importare un file.</small>}
          </>
        )}
        {upload.status === "error" && <div className="inline-error" role="alert">{upload.message}</div>}
      </div>
      <div className="privacy-note"><Icon name="info" size={17} /> Elaborazione locale. Nessun audio viene inviato a servizi esterni.</div>
    </section>
  );
}
