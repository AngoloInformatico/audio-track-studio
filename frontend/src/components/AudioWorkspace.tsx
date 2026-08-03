import { useRef, useState } from "react";

import { useTrackEditor } from "../hooks/useTrackEditor";
import type { AudioInfo, AudioSession, Track } from "../types/audio";
import { formatBytes, formatTime } from "../utils/format";
import { Icon } from "./Icon";
import { AnalysisDialog } from "./AnalysisDialog";
import { RecognitionDialog } from "./RecognitionDialog";
import { MetadataDialog } from "./MetadataDialog";
import { TrackTable } from "./TrackTable";
import { WaveformEditor, type WaveformEditorHandle } from "./WaveformEditor";

interface AudioWorkspaceProps {
  session: AudioSession;
  analysisOpen: boolean;
  onCloseAnalysis: () => void;
  recognitionOpen: boolean;
  onCloseRecognition: () => void;
}

export function AudioWorkspace({ session, analysisOpen, onCloseAnalysis, recognitionOpen, onCloseRecognition }: AudioWorkspaceProps) {
  const editor = useTrackEditor(session.id, session.info.duration_seconds);
  const waveformRef = useRef<WaveformEditorHandle>(null);
  const [selectedMarkerIndex, setSelectedMarkerIndex] = useState<number>();
  const [selectedTrackId, setSelectedTrackId] = useState<string>();
  const [recognitionTrackId, setRecognitionTrackId] = useState<string>();
  const [metadataTrackId, setMetadataTrackId] = useState<string>();

  const validMarkerIndex = editor.collection && selectedMarkerIndex !== undefined
    && selectedMarkerIndex < editor.collection.markers.length ? selectedMarkerIndex : undefined;
  const validTrackId = editor.collection?.tracks.some((track) => track.id === selectedTrackId)
    ? selectedTrackId
    : editor.collection?.tracks[0]?.id;
  const metadataTrack = editor.collection?.tracks.find((track) => track.id === metadataTrackId);

  const addMarker = async (seconds: number) => editor.addMarker(seconds);
  const moveMarker = async (index: number, seconds: number) => editor.moveMarker(index, seconds);
  const removeMarker = async (index: number) => editor.removeMarker(index);
  const playTrack = (track: Track) => {
    setSelectedTrackId(track.id);
    waveformRef.current?.playRange(track.start_seconds, track.end_seconds);
  };
  const splitTrack = (track: Track) => {
    setSelectedTrackId(track.id);
    const currentTime = waveformRef.current?.getCurrentTime() ?? 0;
    void editor.splitTrack(track, currentTime).then((index) => {
      if (index !== undefined) setSelectedMarkerIndex(index);
    });
  };
  const mergeTrack = (track: Track) => {
    const confirmed = window.confirm(
      `Unire la traccia ${track.number} alla successiva? Il marker tra le due tracce verrà rimosso.`,
    );
    if (confirmed) {
      setSelectedMarkerIndex(undefined);
      void editor.mergeWithNext(track);
    }
  };

  return (
    <div className="workspace">
      <FileSummary info={session.info} />
      {editor.error && (
        <div className="editor-notice" role="alert">
          <Icon name="info" size={17} />
          <span>{editor.error}</span>
          <button onClick={editor.clearError} type="button">Chiudi</button>
        </div>
      )}
      {editor.loading ? (
        <div className="editor-loading"><Icon name="activity" /> Preparazione editor tracce…</div>
      ) : !editor.collection ? (
        <div className="editor-loading unavailable"><Icon name="info" /> Editor tracce non disponibile per questa sessione.</div>
      ) : (
        <>
          <WaveformEditor
            markers={editor.collection.markers}
            onAddMarker={addMarker}
            onDeleteMarker={removeMarker}
            onMoveMarker={moveMarker}
            onSelectMarker={setSelectedMarkerIndex}
            ref={waveformRef}
            saving={editor.saving}
            selectedMarkerIndex={validMarkerIndex}
            session={session}
          />
          <section className="tracks-card">
            <div className="card-heading tracks-heading">
              <div><span className="section-kicker"><span /> TRACCE</span><h2>Suddivisione del mix</h2></div>
              <div className="track-summary">
                {editor.saving && <span className="saving-indicator"><Icon name="activity" size={14} /> Salvataggio…</span>}
                <span className="phase-badge">{editor.collection.tracks.length} tracce · {editor.collection.markers.length} marker</span>
              </div>
            </div>
            <TrackTable
              collection={editor.collection}
              onMerge={mergeTrack}
              onEditMetadata={(track) => setMetadataTrackId(track.id)}
              onMoveMarker={(index, seconds) => void moveMarker(index, seconds)}
              onPlay={playTrack}
              onRecognize={(track) => setRecognitionTrackId(track.id)}
              onSelect={(track) => setSelectedTrackId(track.id)}
              onSplit={splitTrack}
              onUpdateMetadata={(trackId, artist, title) => void editor.updateMetadata(trackId, artist, title)}
              saving={editor.saving}
              selectedTrackId={validTrackId}
            />
            <div className="track-table-help">
              <Icon name="info" size={15} />
              Trascina i marker sulla waveform o modifica i timestamp. Gli estremi delle tracce adiacenti si aggiornano insieme.
            </div>
          </section>
        </>
      )}
      {analysisOpen && editor.collection && (
        <AnalysisDialog
          existingMarkers={editor.collection.markers}
          onApply={editor.applySuggestedMarkers}
          onClose={onCloseAnalysis}
          session={session}
        />
      )}
      {(recognitionOpen || recognitionTrackId) && editor.collection && (
        <RecognitionDialog
          onApply={editor.applyRecognitionMetadata}
          onClose={() => {
            if (recognitionOpen) onCloseRecognition();
            setRecognitionTrackId(undefined);
          }}
          session={session}
          trackIds={recognitionOpen ? undefined : [recognitionTrackId as string]}
          tracks={editor.collection.tracks}
        />
      )}
      {metadataTrack && (
        <MetadataDialog
          key={metadataTrack.id}
          onClose={() => setMetadataTrackId(undefined)}
          onFetchCover={editor.fetchCover}
          onRemoveCover={editor.removeCover}
          onUpdate={editor.updateAdvancedMetadata}
          onUploadCover={editor.uploadCover}
          saving={editor.saving}
          track={metadataTrack}
        />
      )}
    </div>
  );
}

function FileSummary({ info }: { info: AudioInfo }) {
  const facts = [
    ["Formato", [info.format, info.codec?.toUpperCase()].filter(Boolean).join(" · ")],
    ["Durata", formatTime(info.duration_seconds, false)],
    ["Sample rate", info.sample_rate ? `${(info.sample_rate / 1000).toFixed(info.sample_rate % 1000 ? 1 : 0)} kHz` : "—"],
    ["Profondità", info.bit_depth ? `${info.bit_depth} bit` : "—"],
    ["Canali", info.channel_layout ?? (info.channels ? String(info.channels) : "—")],
    ["Bitrate", info.bitrate ? `${Math.round(info.bitrate / 1000)} kbps` : "—"],
    ["Dimensione", formatBytes(info.size_bytes)],
  ];
  return (
    <section className="file-summary">
      <div className="file-identity"><div className="file-icon"><Icon name="fileAudio" size={26} /></div><div><span>FILE SORGENTE</span><strong title={info.name}>{info.name}</strong></div></div>
      <div className="file-facts">{facts.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
      <div className="source-safe"><span>✓</span> Originale protetto</div>
    </section>
  );
}
