import { useEffect, useState, type FormEvent, type MouseEvent } from "react";

import { cancelJob, getAnalysisConfig, getJob, startAnalysis } from "../services/api";
import type {
  AnalysisConfig,
  AnalysisResult,
  AudioSession,
  BoundarySuggestion,
  JobView,
} from "../types/audio";
import { formatTime } from "../utils/format";
import { Icon } from "./Icon";
import { JobProgress } from "./JobProgress";

interface AnalysisDialogProps {
  session: AudioSession;
  existingMarkers: number[];
  onApply: (timestamps: number[]) => Promise<boolean>;
  onClose: () => void;
}

export function AnalysisDialog({ session, existingMarkers, onApply, onClose }: AnalysisDialogProps) {
  const [config, setConfig] = useState<AnalysisConfig>();
  const [sensitivity, setSensitivity] = useState(55);
  const [minimumTrackSeconds, setMinimumTrackSeconds] = useState(20);
  const [job, setJob] = useState<JobView<AnalysisResult>>();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(true);
  const jobId = job?.id;
  const jobStatus = job?.status;

  useEffect(() => {
    let active = true;
    getAnalysisConfig()
      .then((value) => {
        if (!active) return;
        setConfig(value);
        setSensitivity(value.default_sensitivity);
        setMinimumTrackSeconds(value.default_minimum_track_seconds);
      })
      .catch((reason: unknown) => { if (active) setError(readMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!jobId || !jobStatus || !isActive(jobStatus)) return;
    let active = true;
    const refresh = async () => {
      try {
        const updated = await getJob<AnalysisResult>(jobId);
        if (!active) return;
        setJob(updated);
        if (updated.status === "completed" && updated.result) {
          setSelected(new Set(updated.result.suggestions.map((_, index) => index)));
        }
      } catch (reason) {
        if (active) setError(readMessage(reason));
      }
    };
    const interval = window.setInterval(() => void refresh(), 450);
    void refresh();
    return () => { active = false; window.clearInterval(interval); };
  }, [jobId, jobStatus]);

  const active = job ? isActive(job.status) : false;
  const result = job?.status === "completed" ? job.result : null;
  const start = async (event: FormEvent) => {
    event.preventDefault();
    setError(undefined);
    setSelected(new Set());
    try {
      setJob(await startAnalysis({
        audio_id: session.id,
        sensitivity,
        minimum_track_seconds: minimumTrackSeconds,
      }));
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const cancel = async () => {
    if (!job) return;
    try {
      setJob(await cancelJob<AnalysisResult>(job.id));
    } catch (reason) {
      setError(readMessage(reason));
    }
  };
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !active) onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="analysis-title" aria-modal="true" className="export-dialog analysis-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon analysis-icon"><Icon name="activity" size={22} /></div>
          <div><span className="section-kicker"><span /> FASE 4</span><h2 id="analysis-title">Analisi automatica confini</h2><p>{session.info.name}</p></div>
          <button aria-label="Chiudi analisi" className="dialog-close" disabled={active} onClick={onClose} type="button"><Icon name="x" /></button>
        </header>

        {loading ? (
          <div className="dialog-loading"><Icon name="activity" /> Preparazione motore di analisi…</div>
        ) : result ? (
          <AnalysisResults
            existingMarkers={existingMarkers}
            onApply={onApply}
            onClose={onClose}
            onError={setError}
            onRestart={() => { setJob(undefined); setSelected(new Set()); setError(undefined); }}
            result={result}
            selected={selected}
            setSelected={setSelected}
          />
        ) : (
          <form onSubmit={(event) => void start(event)}>
            <div className="analysis-intro">
              <div><Icon name="sparkles" size={20} /></div>
              <span><strong>Suggerimenti, non modifiche definitive</strong><small>L’analisi non sposta né crea marker finché non scegli esplicitamente quali applicare.</small></span>
            </div>

            <div className="analysis-settings">
              <label className="sensitivity-field">
                <span><strong>Sensibilità</strong><output>{sensitivity}%</output></span>
                <input disabled={active} max="100" min="0" onChange={(event) => setSensitivity(Number(event.target.value))} type="range" value={sensitivity} />
                <small>Più alta: più candidati e maggiore attenzione ai cambiamenti deboli.</small>
              </label>
              <label className="field"><span>Distanza minima tra confini</span><select disabled={active} onChange={(event) => setMinimumTrackSeconds(Number(event.target.value))} value={minimumTrackSeconds}><option value="5">5 secondi</option><option value="10">10 secondi</option><option value="20">20 secondi</option><option value="30">30 secondi</option><option value="60">60 secondi</option></select><small>Riduce suggerimenti troppo ravvicinati.</small></label>
            </div>

            <div className="analysis-method"><Icon name="info" size={18} /><span><strong>Analisi locale e offline</strong><small>{config?.method_note}</small></span></div>
            {error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
            {job && <JobProgress cancelledText="Analisi annullata. I marker esistenti non sono stati modificati." job={job} />}

            <footer className="dialog-footer">
              <button className="button secondary" disabled={active} onClick={onClose} type="button">Chiudi</button>
              {active ? (
                <button className="button danger-button" onClick={() => void cancel()} type="button"><Icon name="square" size={14} /> Interrompi analisi</button>
              ) : (
                <button className="button primary analysis-start" type="submit"><Icon name="activity" size={17} /> Avvia analisi</button>
              )}
            </footer>
          </form>
        )}
      </section>
    </div>
  );
}

interface AnalysisResultsProps {
  result: AnalysisResult;
  selected: Set<number>;
  setSelected: (value: Set<number>) => void;
  existingMarkers: number[];
  onApply: (timestamps: number[]) => Promise<boolean>;
  onRestart: () => void;
  onClose: () => void;
  onError: (message: string) => void;
}

function AnalysisResults(props: AnalysisResultsProps) {
  const { result, selected, setSelected } = props;
  const [applying, setApplying] = useState(false);
  const toggle = (index: number) => {
    const next = new Set(selected);
    if (next.has(index)) next.delete(index); else next.add(index);
    setSelected(next);
  };
  const apply = async () => {
    setApplying(true);
    const timestamps = result.suggestions
      .filter((_, index) => selected.has(index))
      .map((suggestion) => suggestion.timestamp_seconds);
    try {
      if (await props.onApply(timestamps)) props.onClose();
      else props.onError("Non è stato possibile applicare i confini selezionati.");
    } finally {
      setApplying(false);
    }
  };
  const allSelected = selected.size === result.suggestions.length && result.suggestions.length > 0;

  return (
    <div className="analysis-results">
      <div className="analysis-result-summary">
        <div><span>Confini suggeriti</span><strong>{result.suggestions.length}</strong></div>
        <div><span>Finestre analizzate</span><strong>{result.analyzed_windows}</strong></div>
        <div><span>Sensibilità</span><strong>{result.sensitivity}%</strong></div>
        <div><span>Marker attuali</span><strong>{props.existingMarkers.length}</strong></div>
      </div>
      {result.suggestions.length ? (
        <>
          <div className="suggestion-toolbar"><span>Seleziona i confini da aggiungere alla suddivisione corrente.</span><button onClick={() => setSelected(allSelected ? new Set() : new Set(result.suggestions.map((_, index) => index)))} type="button">{allSelected ? "Deseleziona tutti" : "Seleziona tutti"}</button></div>
          <div className="suggestion-list">
            {result.suggestions.map((suggestion, index) => (
              <SuggestionRow checked={selected.has(index)} index={index} key={`${suggestion.timestamp_seconds}-${index}`} onToggle={toggle} suggestion={suggestion} />
            ))}
          </div>
        </>
      ) : (
        <div className="no-suggestions"><Icon name="waveform" size={30} /><strong>Nessun confine affidabile trovato</strong><p>Aumenta la sensibilità o riduci la distanza minima, poi esegui una nuova analisi.</p></div>
      )}
      <div className="analysis-result-note"><Icon name="info" size={16} /> Le confidenze esprimono la forza degli indizi audio, non la certezza che inizi un nuovo brano.</div>
      <footer className="dialog-footer analysis-result-footer">
        <button className="button secondary" disabled={applying} onClick={props.onRestart} type="button">Nuova analisi</button>
        <button className="button primary" disabled={!selected.size || applying} onClick={() => void apply()} type="button"><Icon name="check" size={16} /> Applica selezionati ({selected.size})</button>
      </footer>
    </div>
  );
}

function SuggestionRow({ suggestion, index, checked, onToggle }: { suggestion: BoundarySuggestion; index: number; checked: boolean; onToggle: (index: number) => void }) {
  const percent = Math.round(suggestion.confidence * 100);
  return (
    <label className={`suggestion-row ${checked ? "selected" : ""}`}>
      <input checked={checked} onChange={() => onToggle(index)} type="checkbox" />
      <span className="suggestion-number">{String(index + 1).padStart(2, "0")}</span>
      <span className="suggestion-time"><small>TIMESTAMP</small><strong>{formatTime(suggestion.timestamp_seconds, true)}</strong></span>
      <span className="suggestion-signals">{suggestion.signals.map((signal) => <small key={signal}>{signal}</small>)}</span>
      <span className="suggestion-confidence"><span><small>CONFIDENZA</small><strong>{percent}%</strong></span><span className="confidence-track"><i style={{ width: `${percent}%` }} /></span></span>
    </label>
  );
}

function isActive(status: JobView<unknown>["status"]): boolean {
  return status === "pending" || status === "running";
}

function readMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Errore durante l’analisi automatica.";
}
