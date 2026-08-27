import { useEffect, useState, type MouseEvent } from "react";

import { getAcoustIDSetup, installFpcalc, updateAcoustIDSetup } from "../services/api";
import type { AcoustIDSetupStatus } from "../types/audio";
import { Icon } from "./Icon";

interface AcoustIDSetupDialogProps {
  onClose: () => void;
}

type BusyAction = "key" | "path" | "install";

export function AcoustIDSetupDialog({ onClose }: AcoustIDSetupDialogProps) {
  const [status, setStatus] = useState<AcoustIDSetupStatus>();
  const [apiKey, setApiKey] = useState("");
  const [fpcalcPath, setFpcalcPath] = useState("");
  const [busy, setBusy] = useState<BusyAction>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    getAcoustIDSetup()
      .then((value) => {
        if (!active) return;
        setStatus(value);
        setFpcalcPath(value.fpcalc_path === "fpcalc" ? "" : value.fpcalc_path);
      })
      .catch((reason: unknown) => {
        if (active) setError(readMessage(reason, "Impossibile leggere la configurazione AcoustID."));
      });
    return () => { active = false; };
  }, []);

  const apply = async (action: BusyAction, operation: () => Promise<AcoustIDSetupStatus>) => {
    setBusy(action);
    setError(undefined);
    try {
      const value = await operation();
      setStatus(value);
      setFpcalcPath(value.fpcalc_path === "fpcalc" ? "" : value.fpcalc_path);
      if (action === "key") setApiKey("");
    } catch (reason) {
      setError(readMessage(reason, "Configurazione non completata."));
    } finally {
      setBusy(undefined);
    }
  };

  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && !busy) onClose();
  };

  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="acoustid-setup-title" aria-modal="true" className="export-dialog acoustid-setup-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon acoustid-setup-icon"><Icon name="settings" size={22} /></div>
          <div><span className="section-kicker"><span /> RICONOSCIMENTO</span><h2 id="acoustid-setup-title">Imposta AcoustID</h2><p>Configura la chiave e Chromaprint direttamente dall’app.</p></div>
          <button aria-label="Chiudi configurazione AcoustID" className="dialog-close" disabled={Boolean(busy)} onClick={onClose} type="button"><Icon name="x" /></button>
        </header>

        {!status && !error ? (
          <div className="dialog-loading"><Icon name="activity" /> Lettura configurazione…</div>
        ) : (
          <div className="acoustid-setup-content">
            {status?.available && (
              <div className="acoustid-complete" role="status">
                <span><Icon name="check" size={28} /></span>
                <div><strong>Configurazione completata</strong><small>AcoustID e fpcalc sono pronti per riconoscere le tracce.</small></div>
              </div>
            )}

            <section className={`acoustid-step ${status?.api_key_configured ? "complete" : ""}`}>
              <div className="acoustid-step-heading">
                <span className="acoustid-step-number">1</span>
                <div><strong>Chiave API AcoustID</strong><small>Viene salvata solo nel file di configurazione locale e non viene mostrata nuovamente.</small></div>
                <span className="acoustid-step-state"><Icon name={status?.api_key_configured ? "check" : "clock"} size={17} /> {status?.api_key_configured ? "Configurata" : "Da impostare"}</span>
              </div>
              <label className="field">
                <span>Chiave applicazione</span>
                <input
                  autoComplete="off"
                  disabled={Boolean(busy)}
                  maxLength={200}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder={status?.api_key_configured ? "Chiave già configurata · inseriscine una nuova per sostituirla" : "Incolla la chiave AcoustID"}
                  type="password"
                  value={apiKey}
                />
              </label>
              <div className="acoustid-actions">
                <a href="https://acoustid.org/new-application" rel="noreferrer" target="_blank">Ottieni una chiave gratuita</a>
                <button className="button secondary" disabled={Boolean(busy) || !apiKey.trim()} onClick={() => void apply("key", () => updateAcoustIDSetup({ acoustid_api_key: apiKey.trim() }))} type="button">
                  <Icon name="save" size={16} /> {busy === "key" ? "Salvataggio…" : "Salva chiave"}
                </button>
              </div>
            </section>

            <section className={`acoustid-step ${status?.fpcalc_available ? "complete" : ""}`}>
              <div className="acoustid-step-heading">
                <span className="acoustid-step-number">2</span>
                <div><strong>fpcalc / Chromaprint</strong><small>Genera localmente l’impronta audio necessaria ad AcoustID.</small></div>
                <span className="acoustid-step-state"><Icon name={status?.fpcalc_available ? "check" : "clock"} size={17} /> {status?.fpcalc_available ? "Pronto" : "Mancante"}</span>
              </div>
              {status?.fpcalc_available && (
                <div className="acoustid-tool-details">
                  <Icon name="check" size={18} /><span><strong>{status.fpcalc_version ?? "fpcalc rilevato"}</strong><small>{status.fpcalc_path}{status.fpcalc_managed ? " · gestito da Audio Track Studio" : ""}</small></span>
                </div>
              )}
              <button className="button primary acoustid-install" disabled={Boolean(busy)} onClick={() => void apply("install", installFpcalc)} type="button">
                <Icon name="download" size={17} /> {busy === "install" ? "Download e verifica in corso…" : `Scarica e configura Chromaprint ${status?.chromaprint_version ?? ""}`}
              </button>
              <p className="acoustid-source-note">Download dalla release ufficiale AcoustID/Chromaprint per Windows x64. Non richiede un programma di installazione.</p>
              <details className="acoustid-manual">
                <summary>Ho già fpcalc: configura il percorso manualmente</summary>
                <label className="field">
                  <span>Percorso completo di fpcalc.exe</span>
                  <input disabled={Boolean(busy)} onChange={(event) => setFpcalcPath(event.target.value)} placeholder="C:\\percorso\\fpcalc.exe" value={fpcalcPath} />
                </label>
                <button className="button secondary" disabled={Boolean(busy) || !fpcalcPath.trim()} onClick={() => void apply("path", () => updateAcoustIDSetup({ fpcalc_path: fpcalcPath.trim() }))} type="button">
                  <Icon name="check" size={16} /> {busy === "path" ? "Verifica…" : "Verifica e usa percorso"}
                </button>
              </details>
            </section>

            {error && <div className="export-error" role="alert"><Icon name="info" size={17} /> {error}</div>}
            {!status?.available && status && <div className="acoustid-pending"><Icon name="info" size={17} /> {status.message}</div>}
            <footer className="dialog-footer"><button className="button primary" disabled={Boolean(busy)} onClick={onClose} type="button">Chiudi</button></footer>
          </div>
        )}
      </section>
    </div>
  );
}

function readMessage(reason: unknown, fallback: string): string {
  return reason instanceof Error ? reason.message : fallback;
}
