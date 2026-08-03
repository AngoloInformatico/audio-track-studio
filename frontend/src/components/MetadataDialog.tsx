import { useRef, useState, type FormEvent, type MouseEvent } from "react";

import type { CoverInfo, Track, TrackMetadataUpdate } from "../types/audio";
import { formatBytes } from "../utils/format";
import {
  metadataFormFromTrack,
  metadataUpdateFromForm,
  type MetadataFormValue,
} from "../utils/metadata";
import { Icon } from "./Icon";

interface MetadataDialogProps {
  track: Track;
  saving: boolean;
  onUpdate: (trackId: string, update: TrackMetadataUpdate) => Promise<boolean>;
  onUploadCover: (trackId: string, file: File) => Promise<boolean>;
  onFetchCover: (trackId: string, releaseGroupId: string) => Promise<boolean>;
  onRemoveCover: (trackId: string) => Promise<boolean>;
  onClose: () => void;
}

export function MetadataDialog(props: MetadataDialogProps) {
  const [form, setForm] = useState<MetadataFormValue>(() => metadataFormFromTrack(props.track));
  const [error, setError] = useState<string>();
  const [coverBusy, setCoverBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const setField = (field: keyof MetadataFormValue, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    const success = await props.onUpdate(props.track.id, metadataUpdateFromForm(form));
    if (success) props.onClose();
    else setError("Non è stato possibile salvare i metadati.");
  };
  const upload = async (file: File) => {
    setCoverBusy(true);
    setError(undefined);
    try {
      if (!await props.onUploadCover(props.track.id, file)) {
        setError("La copertina non è stata caricata. Usa un file JPEG o PNG entro 10 MB.");
      }
    } finally {
      setCoverBusy(false);
    }
  };
  const fetchCover = async () => {
    if (!props.track.release_group_id) return;
    setCoverBusy(true);
    setError(undefined);
    try {
      if (!await props.onFetchCover(props.track.id, props.track.release_group_id)) {
        setError("Nessuna copertina disponibile online. Puoi sceglierne una manualmente.");
      }
    } finally {
      setCoverBusy(false);
    }
  };
  const removeCover = async () => {
    setCoverBusy(true);
    setError(undefined);
    try {
      if (!await props.onRemoveCover(props.track.id)) {
        setError("Non è stato possibile rimuovere la copertina.");
      }
    } finally {
      setCoverBusy(false);
    }
  };
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !props.saving && !coverBusy) props.onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="metadata-title" aria-modal="true" className="export-dialog metadata-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon metadata-icon"><Icon name="fileAudio" size={22} /></div>
          <div><span className="section-kicker"><span /> FASE 6</span><h2 id="metadata-title">Metadati e copertina</h2><p>Traccia {props.track.number} · {props.track.title || "Senza titolo"}</p></div>
          <button aria-label="Chiudi editor metadati" className="dialog-close" disabled={props.saving || coverBusy} onClick={props.onClose} type="button"><Icon name="x" /></button>
        </header>

        <form className="metadata-form" onSubmit={(event) => void submit(event)}>
          <div className="metadata-layout">
            <section className="cover-editor" aria-label="Copertina traccia">
              <div className={`cover-preview ${props.track.cover ? "available" : "empty"}`}>
                {props.track.cover ? <img alt={`Copertina ${props.track.title || `traccia ${props.track.number}`}`} src={`${props.track.cover.url}?v=${props.track.cover.size_bytes}`} /> : <><Icon name="fileAudio" size={35} /><strong>Nessuna copertina</strong><small>L’esportazione resta sempre disponibile.</small></>}
              </div>
              {props.track.cover && <div className="cover-facts"><span>{props.track.cover.mime_type === "image/jpeg" ? "JPEG" : "PNG"}</span><span>{formatBytes(props.track.cover.size_bytes)}</span><span>{coverSourceLabel(props.track.cover.source)}</span></div>}
              <input
                accept="image/jpeg,image/png,.jpg,.jpeg,.png"
                className="cover-file-input"
                onChange={(event) => {
                  const file = event.currentTarget.files?.item(0);
                  if (file) void upload(file);
                  event.currentTarget.value = "";
                }}
                ref={fileInput}
                type="file"
              />
              <button className="button secondary cover-action" disabled={coverBusy || props.saving} onClick={() => fileInput.current?.click()} type="button"><Icon name="upload" size={15} /> {props.track.cover ? "Sostituisci" : "Scegli immagine"}</button>
              {props.track.release_group_id && <button className="button ghost cover-action" disabled={coverBusy || props.saving} onClick={() => void fetchCover()} type="button"><Icon name="download" size={15} /> Cerca online</button>}
              {props.track.cover && <button className="button ghost cover-remove" disabled={coverBusy || props.saving} onClick={() => void removeCover()} type="button"><Icon name="trash" size={15} /> Rimuovi</button>}
              <p>JPEG o PNG, massimo 10 MB. La ricerca online usa il release-group ottenuto dal riconoscimento.</p>
            </section>

            <section className="metadata-fields" aria-label="Metadati traccia">
              <label className="field"><span>Titolo</span><input maxLength={300} onChange={(event) => setField("title", event.target.value)} value={form.title} /></label>
              <label className="field"><span>Artista</span><input maxLength={300} onChange={(event) => setField("artist", event.target.value)} value={form.artist} /></label>
              <label className="field"><span>Album</span><input maxLength={300} onChange={(event) => setField("album", event.target.value)} value={form.album} /></label>
              <label className="field"><span>Album Artist</span><input maxLength={300} onChange={(event) => setField("albumArtist", event.target.value)} value={form.albumArtist} /></label>
              <label className="field"><span>Numero traccia</span><input inputMode="numeric" max="9999" min="1" onChange={(event) => setField("trackNumber", event.target.value)} type="number" value={form.trackNumber} /></label>
              <label className="field"><span>Numero disco</span><input inputMode="numeric" max="999" min="1" onChange={(event) => setField("discNumber", event.target.value)} placeholder="—" type="number" value={form.discNumber} /></label>
              <label className="field"><span>Anno / Data</span><input maxLength={32} onChange={(event) => setField("date", event.target.value)} placeholder="2026 oppure 2026-08-02" value={form.date} /></label>
              <label className="field"><span>Genere</span><input maxLength={150} onChange={(event) => setField("genre", event.target.value)} value={form.genre} /></label>
              <label className="field span-2"><span>Compositore</span><input maxLength={300} onChange={(event) => setField("composer", event.target.value)} value={form.composer} /></label>
              <label className="field span-2"><span>Commento</span><textarea maxLength={2000} onChange={(event) => setField("comment", event.target.value)} rows={3} value={form.comment} /></label>
            </section>
          </div>

          {error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
          <div className="metadata-note"><Icon name="info" size={16} /> I valori restano modificabili e verranno incorporati soltanto se scegli l’opzione corrispondente durante l’esportazione.</div>
          <footer className="dialog-footer">
            <button className="button secondary" disabled={props.saving || coverBusy} onClick={props.onClose} type="button">Annulla</button>
            <button className="button primary" disabled={props.saving || coverBusy} type="submit"><Icon name="save" size={16} /> Salva metadati</button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function coverSourceLabel(source: CoverInfo["source"]): string {
  if (source === "manual") return "Manuale";
  if (source === "source") return "File sorgente";
  return "Cover Art Archive";
}
