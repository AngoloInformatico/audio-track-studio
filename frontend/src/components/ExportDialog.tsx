import { useEffect, useState, type FormEvent, type MouseEvent } from "react";

import { cancelJob, getExportConfig, getJob, getTracks, startExport } from "../services/api";
import type { AudioSession, ExportConfig, ExportResult, JobView, TrackCollection } from "../types/audio";
import { formatTime } from "../utils/format";
import { Icon } from "./Icon";
import { JobProgress } from "./JobProgress";

interface ExportDialogProps {
  session: AudioSession;
  onClose: () => void;
}

export function ExportDialog({ session, onClose }: ExportDialogProps) {
  const [config, setConfig] = useState<ExportConfig>();
  const [tracks, setTracks] = useState<TrackCollection>();
  const [destination, setDestination] = useState("");
  const [template, setTemplate] = useState("{track:02d} - {artist} - {title}.flac");
  const [overwrite, setOverwrite] = useState(false);
  const [embedMetadata, setEmbedMetadata] = useState(true);
  const [embedCover, setEmbedCover] = useState(true);
  const [saveCoverFile, setSaveCoverFile] = useState(false);
  const [compression, setCompression] = useState(8);
  const [job, setJob] = useState<JobView<ExportResult>>();
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const jobId = job?.id;
  const jobStatus = job?.status;

  useEffect(() => {
    let active = true;
    Promise.all([getExportConfig(), getTracks(session.id)])
      .then(([nextConfig, nextTracks]) => {
        if (!active) return;
        setConfig(nextConfig);
        setTracks(nextTracks);
        setDestination(nextConfig.default_directory);
        setTemplate(nextConfig.default_template);
      })
      .catch((reason: unknown) => { if (active) setError(readMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [session.id]);

  useEffect(() => {
    if (!jobId || !jobStatus || !isActive(jobStatus)) return;
    let active = true;
    const refresh = async () => {
      try {
        const updated = await getJob<ExportResult>(jobId);
        if (active) setJob(updated);
      } catch (reason) {
        if (active) setError(readMessage(reason));
      }
    };
    const interval = window.setInterval(() => void refresh(), 450);
    void refresh();
    return () => { active = false; window.clearInterval(interval); };
  }, [jobId, jobStatus]);

  const active = job ? isActive(job.status) : false;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    try {
      const started = await startExport({
        audio_id: session.id,
        destination,
        format: "flac",
        filename_template: template,
        overwrite,
        embed_metadata: embedMetadata,
        embed_cover: embedCover,
        save_cover_file: saveCoverFile,
        compression_level: compression,
      });
      setJob(started);
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const cancel = async () => {
    if (!job) return;
    try {
      setJob(await cancelJob<ExportResult>(job.id));
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !active) onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="export-title" aria-modal="true" className="export-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon"><Icon name="download" size={22} /></div>
          <div><span className="section-kicker"><span /> FASE 3</span><h2 id="export-title">Esporta tracce FLAC</h2><p>{session.info.name}</p></div>
          <button aria-label="Chiudi esportazione" className="dialog-close" disabled={active} onClick={onClose} type="button"><Icon name="x" /></button>
        </header>

        {loading ? (
          <div className="dialog-loading"><Icon name="activity" /> Preparazione riepilogo…</div>
        ) : job?.status === "completed" && job.result ? (
          <ExportCompleted job={job} onClose={onClose} />
        ) : (
          <form onSubmit={(event) => void submit(event)}>
            <div className="export-summary-strip">
              <div><span>Tracce</span><strong>{tracks?.tracks.length ?? 0}</strong></div>
              <div><span>Durata totale</span><strong>{formatTime(session.info.duration_seconds, false)}</strong></div>
              <div><span>Formato</span><strong>FLAC lossless</strong></div>
              <div><span>Qualità</span><strong>Nessuna perdita aggiuntiva</strong></div>
            </div>

            <div className="export-form-grid">
              <label className="field span-2"><span>Cartella di destinazione</span><div className="path-field"><Icon name="folder" size={17} /><input disabled={active} onChange={(event) => setDestination(event.target.value)} required value={destination} /></div><small>Inserisci un percorso assoluto. Il selettore nativo arriverà con il wrapper desktop.</small></label>
              <label className="field span-2"><span>Schema nome file</span><input disabled={active} onChange={(event) => setTemplate(event.target.value)} required value={template} /><small>Placeholder disponibili: {"{track}"}, {"{artist}"}, {"{title}"}</small></label>
              <label className="field"><span>Formato</span><select disabled value="flac"><option value="flac">FLAC</option></select></label>
              <label className="field"><span>Compressione FLAC</span><select disabled={active} onChange={(event) => setCompression(Number(event.target.value))} value={compression}><option value="5">5 · Veloce</option><option value="8">8 · Consigliata</option><option value="12">12 · Massima</option></select><small>La compressione non modifica la qualità.</small></label>
            </div>

            <div className="export-options">
              <label><input checked={embedMetadata} disabled={active} onChange={(event) => setEmbedMetadata(event.target.checked)} type="checkbox" /><span><strong>Incorpora metadati</strong><small>Tag FLAC completi tramite Mutagen</small></span></label>
              <label><input checked={embedCover} disabled={active} onChange={(event) => setEmbedCover(event.target.checked)} type="checkbox" /><span><strong>Incorpora copertine</strong><small>Solo per le tracce che dispongono di un’immagine</small></span></label>
              <label><input checked={saveCoverFile} disabled={active} onChange={(event) => setSaveCoverFile(event.target.checked)} type="checkbox" /><span><strong>Salva anche cover.*</strong><small>JPEG come cover.jpg; PNG mantiene il proprio formato</small></span></label>
              <label><input checked={overwrite} disabled={active} onChange={(event) => setOverwrite(event.target.checked)} type="checkbox" /><span><strong>Consenti sovrascrittura</strong><small>Disattivata per sicurezza</small></span></label>
            </div>

            <div className="lossless-note"><Icon name="info" size={18} /><div><strong>Taglio preciso, sempre lossless</strong><span>{config?.mode_note ?? "Ricodifica FLAC lossless per garantire tagli precisi."}</span></div></div>

            {error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
            {job && <JobProgress cancelledText="L’operazione è stata annullata; nessun file parziale è stato mantenuto." job={job} />}

            <footer className="dialog-footer">
              <button className="button secondary" disabled={active} onClick={onClose} type="button">Annulla</button>
              {active ? (
                <button className="button danger-button" onClick={() => void cancel()} type="button"><Icon name="square" size={14} /> Interrompi esportazione</button>
              ) : (
                <button className="button primary export-start" disabled={!tracks?.tracks.length} type="submit"><Icon name="download" size={17} /> Esporta {tracks?.tracks.length ?? 0} tracce</button>
              )}
            </footer>
          </form>
        )}
      </section>
    </div>
  );
}

function ExportCompleted({ job, onClose }: { job: JobView<ExportResult>; onClose: () => void }) {
  const result = job.result!;
  return (
    <div className="export-completed">
      <div className="completion-mark"><Icon name="check" size={33} /></div>
      <span className="section-kicker"><span /> COMPLETATA</span>
      <h3>{result.count} tracce esportate</h3>
      <p>I file FLAC sono stati creati senza perdita di qualità.</p>
      <div className="completion-destination"><Icon name="folder" size={18} /><span><small>DESTINAZIONE</small><strong>{result.destination}</strong></span></div>
      <div className="exported-files">{result.files.map((file) => <div key={file}><Icon name="fileAudio" size={16} /><span>{file.split(/[\\/]/).pop()}</span><Icon name="check" size={15} /></div>)}</div>
      {result.cover_files.length > 0 && <p className="cover-export-summary">{result.cover_files.length} file copertina salvati accanto alle tracce.</p>}
      <button className="button primary large" onClick={onClose} type="button">Chiudi</button>
    </div>
  );
}

function isActive(status: JobView<unknown>["status"]): boolean {
  return status === "pending" || status === "running";
}

function readMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Errore durante l’esportazione.";
}
