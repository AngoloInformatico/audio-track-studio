import type { MouseEvent } from "react";

import { CopyrightLink } from "./CopyrightLink";
import { Icon } from "./Icon";

interface AboutDialogProps {
  onClose: () => void;
}

export function AboutDialog({ onClose }: AboutDialogProps) {
  const closeFromBackdrop = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) onClose();
  };
  return (
    <div className="modal-backdrop" onMouseDown={closeFromBackdrop} role="presentation">
      <section aria-labelledby="about-title" aria-modal="true" className="export-dialog about-dialog" role="dialog">
        <header className="dialog-header">
          <div className="dialog-title-icon about-icon"><Icon name="waveform" size={23} /></div>
          <div><span className="section-kicker"><span /> RELEASE WINDOWS</span><h2 id="about-title">Audio Track Studio</h2><p>Versione 1.0.1 · Fasi 1–8 complete</p></div>
          <button aria-label="Chiudi informazioni" className="dialog-close" onClick={onClose} type="button"><Icon name="x" /></button>
        </header>
        <div className="about-content">
          <div className="about-release"><Icon name="check" size={24} /><span><strong>Applicazione desktop locale</strong><small>Frontend React, API FastAPI e strumenti audio vengono eseguiti sul tuo PC.</small></span></div>
          <div className="about-grid"><div><span>Audio</span><strong>FFmpeg incluso</strong></div><div><span>Progetti</span><strong>.atsproject v1</strong></div><div><span>Privacy</span><strong>Elaborazione locale</strong></div><div><span>Recognition</span><strong>AcoustID opzionale</strong></div></div>
          <p>Il file sorgente non viene mai modificato. Le funzioni online sono limitate al riconoscimento musicale e al recupero facoltativo delle copertine.</p>
          <CopyrightLink className="about-copyright" />
          <footer className="dialog-footer"><button className="button primary" onClick={onClose} type="button">Chiudi</button></footer>
        </div>
      </section>
    </div>
  );
}
