import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";

import type { AudioSession } from "../types/audio";
import { formatTime } from "../utils/format";
import { BoundaryInspector } from "./BoundaryInspector";
import { Icon } from "./Icon";

const DEFAULT_VOLUME = 0.8;

export interface WaveformEditorHandle {
  getCurrentTime: () => number;
  playRange: (start: number, end: number) => void;
}

interface WaveformEditorProps {
  session: AudioSession;
  markers: number[];
  selectedMarkerIndex?: number;
  saving: boolean;
  onSelectMarker: (index?: number) => void;
  onAddMarker: (seconds: number) => Promise<number | undefined>;
  onMoveMarker: (index: number, seconds: number) => Promise<void>;
  onDeleteMarker: (index: number) => Promise<void>;
}

export const WaveformEditor = forwardRef<WaveformEditorHandle, WaveformEditorProps>(
  function WaveformEditor(
    {
      session,
      markers,
      selectedMarkerIndex,
      saving,
      onSelectMarker,
      onAddMarker,
      onMoveMarker,
      onDeleteMarker,
    },
    ref,
  ) {
    const containerRef = useRef<HTMLDivElement>(null);
    const waveRef = useRef<WaveSurfer | null>(null);
    const regionsRef = useRef<RegionsPlugin | null>(null);
    const callbacksRef = useRef({ onAddMarker, onMoveMarker, onSelectMarker });
    const [ready, setReady] = useState(false);
    const [playing, setPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [volume, setVolume] = useState(DEFAULT_VOLUME);
    const [zoom, setZoom] = useState(0);
    const [waveError, setWaveError] = useState<string>();

    useEffect(() => {
      callbacksRef.current = { onAddMarker, onMoveMarker, onSelectMarker };
    }, [onAddMarker, onMoveMarker, onSelectMarker]);

    useEffect(() => {
      if (!containerRef.current) return;
      const styles = getComputedStyle(document.documentElement);
      const regions = RegionsPlugin.create();
      const wave = WaveSurfer.create({
        container: containerRef.current,
        url: session.stream_url,
        waveColor: styles.getPropertyValue("--wave").trim(),
        progressColor: styles.getPropertyValue("--wave-progress").trim(),
        cursorColor: styles.getPropertyValue("--accent").trim(),
        cursorWidth: 2,
        height: 122,
        normalize: false,
        barWidth: 2,
        barGap: 1.5,
        barRadius: 2,
        plugins: [regions],
      });
      waveRef.current = wave;
      regionsRef.current = regions;
      const subscriptions = [
        wave.on("ready", () => { setReady(true); wave.setVolume(DEFAULT_VOLUME); }),
        wave.on("timeupdate", setCurrentTime),
        wave.on("play", () => setPlaying(true)),
        wave.on("pause", () => setPlaying(false)),
        wave.on("finish", () => setPlaying(false)),
        wave.on("error", () => setWaveError("La waveform non può essere caricata per questo file.")),
        wave.on("dblclick", (relativeX) => {
          const seconds = relativeX * wave.getDuration();
          void callbacksRef.current.onAddMarker(seconds).then((index) => {
            if (index !== undefined) callbacksRef.current.onSelectMarker(index);
          });
        }),
        regions.on("region-clicked", (region, event) => {
          event.stopPropagation();
          callbacksRef.current.onSelectMarker(markerIndex(region.id));
        }),
        regions.on("region-updated", (region) => {
          void callbacksRef.current.onMoveMarker(markerIndex(region.id), region.start);
        }),
      ];
      return () => {
        subscriptions.forEach((unsubscribe) => unsubscribe());
        wave.destroy();
        waveRef.current = null;
        regionsRef.current = null;
      };
    }, [session.id, session.stream_url]);

    useEffect(() => {
      const regions = regionsRef.current;
      if (!ready || !regions) return;
      regions.clearRegions();
      const styles = getComputedStyle(document.documentElement);
      markers.forEach((time, index) => {
        const selected = index === selectedMarkerIndex;
        const label = document.createElement("span");
        label.textContent = `M${index + 1}`;
        Object.assign(label.style, {
          display: "inline-block",
          minWidth: "29px",
          padding: "5px 7px",
          color: "white",
          borderRadius: "5px",
          background: styles.getPropertyValue(selected ? "--accent-strong" : "--accent").trim(),
          boxShadow: "0 3px 8px rgba(0, 0, 0, .2)",
          fontFamily: '"Segoe UI Variable", "Segoe UI", sans-serif',
          fontSize: "9px",
          fontWeight: "800",
          lineHeight: "1",
          textAlign: "center",
        });
        regions.addRegion({
          id: `marker-${index}`,
          start: time,
          drag: true,
          resize: false,
          color: styles.getPropertyValue(index === selectedMarkerIndex ? "--accent-strong" : "--accent").trim(),
          content: label,
        });
      });
    }, [markers, ready, selectedMarkerIndex]);

    useImperativeHandle(ref, () => ({
      getCurrentTime: () => waveRef.current?.getCurrentTime() ?? 0,
      playRange: (start, end) => playRange(start, end),
    }));

    const playRange = (start: number, end: number) => {
      const wave = waveRef.current;
      if (!wave) return;
      const safeStart = Math.max(0, start);
      const safeEnd = Math.min(session.info.duration_seconds, end);
      if (safeEnd > safeStart) void wave.play(safeStart, safeEnd);
    };
    const togglePlayback = () => void waveRef.current?.playPause();
    const stop = () => { waveRef.current?.pause(); waveRef.current?.setTime(0); };
    const skip = (seconds: number) => {
      const next = Math.max(0, Math.min(session.info.duration_seconds, currentTime + seconds));
      waveRef.current?.setTime(next);
    };
    const addAtCursor = () => {
      void onAddMarker(currentTime).then((index) => { if (index !== undefined) onSelectMarker(index); });
    };
    const zoomToSelected = () => {
      if (selectedMarkerIndex === undefined) return;
      setZoom(220);
      waveRef.current?.zoom(220);
      waveRef.current?.setScrollTime(markers[selectedMarkerIndex] ?? 0);
    };

    const selectedTime = selectedMarkerIndex === undefined ? undefined : markers[selectedMarkerIndex];
    return (
      <section className="wave-card">
        <div className="card-heading waveform-heading">
          <div><span className="section-kicker"><span /> WAVEFORM</span><h2>Timeline e confini</h2></div>
          <div className="wave-actions">
            <span className="interaction-hint">Doppio clic sulla waveform per aggiungere un marker</span>
            <button className="button secondary" disabled={!ready || saving} onClick={addAtCursor} type="button">
              <Icon name="plus" size={16} /> Marker al cursore
            </button>
            <label className="zoom-control">
              <span>Zoom</span>
              <input
                aria-label="Zoom waveform"
                max="240"
                min="0"
                onChange={(event) => { const value = Number(event.target.value); setZoom(value); waveRef.current?.zoom(value); }}
                type="range"
                value={zoom}
              />
            </label>
          </div>
        </div>
        <div className={`wave-shell ${ready ? "ready" : "loading"}`}>
          {!ready && !waveError && <div className="wave-loading"><Icon name="activity" /> Generazione waveform…</div>}
          {waveError && <div className="wave-error">{waveError}</div>}
          <div className="waveform-host" ref={containerRef} />
        </div>
        <div className="player-row">
          <div className="transport">
            <button aria-label="Indietro di 10 secondi" disabled={!ready} onClick={() => skip(-10)} type="button"><Icon name="skipBack" /></button>
            <button className="play-button" aria-label={playing ? "Pausa" : "Riproduci"} disabled={!ready} onClick={togglePlayback} type="button"><Icon name={playing ? "pause" : "play"} size={23} /></button>
            <button aria-label="Stop" disabled={!ready} onClick={stop} type="button"><Icon name="square" /></button>
            <button aria-label="Avanti di 10 secondi" disabled={!ready} onClick={() => skip(10)} type="button"><Icon name="skipForward" /></button>
          </div>
          <div className="timecode"><strong>{formatTime(currentTime, true)}</strong><span>/</span>{formatTime(session.info.duration_seconds, true)}</div>
          <label className="volume-control"><Icon name="volume" size={18} /><input aria-label="Volume" max="1" min="0" onChange={(event) => { const value = Number(event.target.value); setVolume(value); waveRef.current?.setVolume(value); }} step="0.01" type="range" value={volume} /></label>
        </div>
        {selectedTime !== undefined && selectedMarkerIndex !== undefined && (
          <BoundaryInspector
            disabled={!ready || saving}
            index={selectedMarkerIndex}
            onChange={(seconds) => void onMoveMarker(selectedMarkerIndex, seconds)}
            onDelete={() => void onDeleteMarker(selectedMarkerIndex).then(() => onSelectMarker(undefined))}
            onPreview={playRange}
            onZoom={zoomToSelected}
            time={selectedTime}
          />
        )}
      </section>
    );
  },
);

function markerIndex(id: string): number {
  const parsed = Number(id.replace("marker-", ""));
  return Number.isInteger(parsed) ? parsed : -1;
}
