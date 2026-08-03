import { useEffect, useMemo, useState, type FormEvent, type MouseEvent } from "react";

import {
  cancelJob,
  getJob,
  getRecognitionConfig,
  startRecognition,
} from "../services/api";
import type {
  AudioSession,
  JobView,
  RecognitionCandidate,
  RecognitionConfig,
  RecognitionMetadataItem,
  RecognitionResult,
  Track,
} from "../types/audio";
import { Icon } from "./Icon";
import { JobProgress } from "./JobProgress";

interface RecognitionDialogProps {
  session: AudioSession;
  tracks: Track[];
  trackIds?: string[];
  onApply: (items: RecognitionMetadataItem[]) => Promise<boolean>;
  onClose: () => void;
}

export function RecognitionDialog(props: RecognitionDialogProps) {
  const [config, setConfig] = useState<RecognitionConfig>();
  const [job, setJob] = useState<JobView<RecognitionResult>>();
  const [selectedTracks, setSelectedTracks] = useState<Set<string>>(new Set());
  const [candidateIndexes, setCandidateIndexes] = useState<Record<string, number>>({});
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const targetTracks = useMemo(() => {
    if (!props.trackIds) return props.tracks;
    const targets = new Set(props.trackIds);
    return props.tracks.filter((track) => targets.has(track.id));
  }, [props.trackIds, props.tracks]);
  const jobId = job?.id;
  const jobStatus = job?.status;
  const active = job ? isActive(job.status) : false;
  const result = job?.status === "completed" ? job.result : null;

  useEffect(() => {
    let mounted = true;
    getRecognitionConfig()
      .then((value) => { if (mounted) setConfig(value); })
      .catch((reason: unknown) => { if (mounted) setError(readMessage(reason)); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!jobId || !jobStatus || !isActive(jobStatus)) return;
    let mounted = true;
    const refresh = async () => {
      try {
        const updated = await getJob<RecognitionResult>(jobId);
        if (!mounted) return;
        setJob(updated);
        if (updated.status === "completed" && updated.result) {
          const matched = updated.result.tracks.filter((track) => track.status === "matched");
          setSelectedTracks(new Set(matched.map((track) => track.track_id)));
          setCandidateIndexes(Object.fromEntries(matched.map((track) => [track.track_id, 0])));
        }
      } catch (reason) {
        if (mounted) setError(readMessage(reason));
      }
    };
    const interval = window.setInterval(() => void refresh(), 500);
    void refresh();
    return () => { mounted = false; window.clearInterval(interval); };
  }, [jobId, jobStatus]);

  const start = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    try {
      setJob(await startRecognition({
        audio_id: props.session.id,
        track_ids: props.trackIds,
        max_candidates: 3,
      }));
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const cancel = async () => {
    if (!job) return;
    try {
      setJob(await cancelJob<RecognitionResult>(job.id));
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !active) props.onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="recognition-title" aria-modal="true" className="export-dialog recognition-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon recognition-icon"><Icon name="search" size={22} /></div>
          <div>
            <span className="section-kicker"><span /> FASE 5</span>
            <h2 id="recognition-title">Riconoscimento musicale</h2>
            <p>{props.trackIds ? `Traccia ${targetTracks[0]?.number ?? ""}` : `${targetTracks.length} tracce · ${props.session.info.name}`}</p>
          </div>
          <button aria-label="Chiudi riconoscimento" className="dialog-close" disabled={active} onClick={props.onClose} type="button"><Icon name="x" /></button>
        </header>

        {loading ? (
          <div className="dialog-loading"><Icon name="activity" /> Verifica di Chromaprint e AcoustID…</div>
        ) : result ? (
          <RecognitionResults
            candidateIndexes={candidateIndexes}
            onApply={props.onApply}
            onClose={props.onClose}
            onError={setError}
            result={result}
            selectedTracks={selectedTracks}
            setCandidateIndexes={setCandidateIndexes}
            setSelectedTracks={setSelectedTracks}
          />
        ) : (
          <form onSubmit={(event) => void start(event)}>
            <div className="recognition-intro">
              <div><Icon name="waveform" size={21} /></div>
              <span><strong>Fingerprint breve, sorgente invariato</strong><small>Per ogni traccia viene provato prima un campione centrale fino a {config?.maximum_sample_seconds ?? 120} secondi, con fallback iniziale/finale. Le proposte non modificano i dati finché non le confermi.</small></span>
            </div>

            {config && !config.available && <RecognitionPrerequisites config={config} />}
            {config?.available && (
              <div className="recognition-ready">
                <Icon name="check" size={19} />
                <span><strong>Provider AcoustID pronto</strong><small>{config.message} È necessaria una connessione Internet.</small></span>
              </div>
            )}
            {error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
            {job && <JobProgress cancelledText="Riconoscimento annullato. I metadati non sono stati modificati." job={job} />}

            <footer className="dialog-footer">
              <button className="button secondary" disabled={active} onClick={props.onClose} type="button">Chiudi</button>
              {active ? (
                <button className="button danger-button" onClick={() => void cancel()} type="button"><Icon name="square" size={14} /> Interrompi</button>
              ) : (
                <button className="button primary" disabled={!config?.available} type="submit"><Icon name="search" size={16} /> Riconosci {targetTracks.length === 1 ? "traccia" : `${targetTracks.length} tracce`}</button>
              )}
            </footer>
          </form>
        )}
      </section>
    </div>
  );
}

function RecognitionPrerequisites({ config }: { config: RecognitionConfig }) {
  return (
    <div className="recognition-prerequisites" role="status">
      <div className="prerequisite-heading"><Icon name="info" size={18} /><span><strong>Configurazione richiesta</strong><small>{config.message}</small></span></div>
      <div className="prerequisite-grid">
        <div className={config.fpcalc_available ? "ready" : "missing"}><span>{config.fpcalc_available ? "Pronto" : "Manca"}</span><strong>Chromaprint / fpcalc</strong><code>ATS_FPCALC_BINARY</code></div>
        <div className={config.api_key_configured ? "ready" : "missing"}><span>{config.api_key_configured ? "Pronta" : "Manca"}</span><strong>Chiave applicazione AcoustID</strong><code>ACOUSTID_API_KEY</code></div>
      </div>
      <p>Il riconoscimento richiede il servizio online AcoustID. Puoi chiudere questa finestra e continuare a modificare artista e titolo manualmente.</p>
    </div>
  );
}

interface ResultsProps {
  result: RecognitionResult;
  selectedTracks: Set<string>;
  candidateIndexes: Record<string, number>;
  setSelectedTracks: (value: Set<string>) => void;
  setCandidateIndexes: (value: Record<string, number>) => void;
  onApply: (items: RecognitionMetadataItem[]) => Promise<boolean>;
  onError: (message: string) => void;
  onClose: () => void;
}

function RecognitionResults(props: ResultsProps) {
  const [applying, setApplying] = useState(false);
  const chooseTrack = (trackId: string) => {
    const next = new Set(props.selectedTracks);
    if (next.has(trackId)) next.delete(trackId); else next.add(trackId);
    props.setSelectedTracks(next);
  };
  const chooseCandidate = (trackId: string, index: number) => {
    props.setCandidateIndexes({ ...props.candidateIndexes, [trackId]: index });
  };
  const apply = async () => {
    const items = props.result.tracks.flatMap((track) => {
      if (!props.selectedTracks.has(track.track_id)) return [];
      const candidate = track.candidates[props.candidateIndexes[track.track_id] ?? 0];
      return candidate ? [{
        track_id: track.track_id,
        artist: candidate.artist,
        title: candidate.title,
        album: candidate.album,
        date: candidate.date,
        release_group_id: candidate.release_group_id,
        provider: candidate.provider,
        external_id: candidate.external_id,
        recording_id: candidate.recording_id,
        confidence: candidate.confidence,
      }] : [];
    });
    setApplying(true);
    try {
      if (await props.onApply(items)) props.onClose();
      else props.onError("Non è stato possibile applicare i metadati selezionati.");
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="recognition-results">
      <div className="recognition-summary">
        <div><span>Corrispondenze</span><strong>{props.result.matched_count}</strong></div>
        <div><span>Senza risultato</span><strong>{props.result.unmatched_count}</strong></div>
        <div><span>Errori</span><strong>{props.result.error_count}</strong></div>
        <div><span>Provider</span><strong>AcoustID</strong></div>
      </div>
      <div className="recognition-result-list">
        {props.result.tracks.map((track) => (
          <RecognitionTrackRow
            candidateIndex={props.candidateIndexes[track.track_id] ?? 0}
            checked={props.selectedTracks.has(track.track_id)}
            key={track.track_id}
            onCandidate={(index) => chooseCandidate(track.track_id, index)}
            onToggle={() => chooseTrack(track.track_id)}
            track={track}
          />
        ))}
      </div>
      <div className="analysis-result-note"><Icon name="info" size={16} /> Controlla sempre i risultati: confidence e corrispondenze multiple non garantiscono un’identificazione certa.</div>
      <footer className="dialog-footer analysis-result-footer">
        <button className="button secondary" disabled={applying} onClick={props.onClose} type="button">Mantieni dati attuali</button>
        <button className="button primary" disabled={!props.selectedTracks.size || applying} onClick={() => void apply()} type="button"><Icon name="check" size={16} /> Applica selezionati ({props.selectedTracks.size})</button>
      </footer>
    </div>
  );
}

function RecognitionTrackRow({ track, checked, candidateIndex, onToggle, onCandidate }: {
  track: RecognitionResult["tracks"][number];
  checked: boolean;
  candidateIndex: number;
  onToggle: () => void;
  onCandidate: (index: number) => void;
}) {
  const candidate = track.candidates[candidateIndex];
  if (!candidate) {
    return <div className={`recognition-track-result ${track.status}`}><span className="recognition-track-number">{String(track.track_number).padStart(2, "0")}</span><div><strong>{track.status === "error" ? "Riconoscimento non disponibile" : "Nessuna corrispondenza affidabile"}</strong><small>{track.error ?? "Inserisci artista e titolo manualmente nella tabella tracce."}</small></div></div>;
  }
  return (
    <div className={`recognition-track-result matched ${checked ? "selected" : ""}`}>
      <input aria-label={`Applica risultato traccia ${track.track_number}`} checked={checked} onChange={onToggle} type="checkbox" />
      <span className="recognition-track-number">{String(track.track_number).padStart(2, "0")}</span>
      <div className="recognition-candidate">
        <strong>{candidate.artist} — {candidate.title}</strong>
        <small>{describeRelease(candidate)}</small>
        {track.candidates.length > 1 && <select aria-label={`Candidato traccia ${track.track_number}`} onChange={(event) => onCandidate(Number(event.target.value))} value={candidateIndex}>{track.candidates.map((item, index) => <option key={`${item.recording_id ?? item.title}-${index}`} value={index}>{candidateLabel(item)}</option>)}</select>}
      </div>
      <span className="recognition-confidence"><small>CONFIDENZA</small><strong>{Math.round(candidate.confidence * 100)}%</strong></span>
    </div>
  );
}

function describeRelease(candidate: RecognitionCandidate): string {
  return [candidate.album, candidate.date, candidate.provider].filter(Boolean).join(" · ") || "Pubblicazione non indicata";
}

function candidateLabel(candidate: RecognitionCandidate): string {
  return `${Math.round(candidate.confidence * 100)}% · ${candidate.artist} — ${candidate.title}`;
}

function isActive(status: JobView<unknown>["status"]): boolean {
  return status === "pending" || status === "running";
}

function readMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Errore durante il riconoscimento musicale.";
}
