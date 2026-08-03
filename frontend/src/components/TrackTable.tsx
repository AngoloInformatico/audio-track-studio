import { useState, type FocusEvent, type MouseEvent } from "react";

import type { Track, TrackCollection } from "../types/audio";
import { formatTime } from "../utils/format";
import { Icon } from "./Icon";
import { TimestampInput } from "./TimestampInput";

interface TrackTableProps {
  collection: TrackCollection;
  selectedTrackId?: string;
  saving: boolean;
  onSelect: (track: Track) => void;
  onPlay: (track: Track) => void;
  onRecognize: (track: Track) => void;
  onEditMetadata: (track: Track) => void;
  onSplit: (track: Track) => void;
  onMerge: (track: Track) => void;
  onMoveMarker: (index: number, seconds: number) => void;
  onUpdateMetadata: (trackId: string, artist: string, title: string) => void;
}

export function TrackTable({
  collection,
  selectedTrackId,
  saving,
  onSelect,
  onPlay,
  onRecognize,
  onEditMetadata,
  onSplit,
  onMerge,
  onMoveMarker,
  onUpdateMetadata,
}: TrackTableProps) {
  return (
    <div className="track-table-wrap">
      <table className="track-table">
        <thead><tr><th>#</th><th>Inizio</th><th>Fine</th><th>Durata</th><th>Artista</th><th>Titolo</th><th>Stato</th><th><span className="sr-only">Azioni</span></th></tr></thead>
        <tbody>
          {collection.tracks.map((track, index) => (
            <TrackRow
              disabled={saving}
              isLast={index === collection.tracks.length - 1}
              key={`${track.id}-${track.artist}-${track.title}`}
              onMerge={onMerge}
              onMoveMarker={onMoveMarker}
              onPlay={onPlay}
              onRecognize={onRecognize}
              onEditMetadata={onEditMetadata}
              onSelect={onSelect}
              onSplit={onSplit}
              onUpdateMetadata={onUpdateMetadata}
              selected={selectedTrackId === track.id}
              track={track}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface TrackRowProps {
  track: Track;
  selected: boolean;
  isLast: boolean;
  disabled: boolean;
  onSelect: (track: Track) => void;
  onPlay: (track: Track) => void;
  onRecognize: (track: Track) => void;
  onEditMetadata: (track: Track) => void;
  onSplit: (track: Track) => void;
  onMerge: (track: Track) => void;
  onMoveMarker: (index: number, seconds: number) => void;
  onUpdateMetadata: (trackId: string, artist: string, title: string) => void;
}

function TrackRow(props: TrackRowProps) {
  const { track, selected, isLast, disabled } = props;
  const [artist, setArtist] = useState(track.artist);
  const [title, setTitle] = useState(track.title);

  const stop = (event: MouseEvent) => event.stopPropagation();
  const saveMetadata = () => {
    const cleanArtist = artist.trim();
    const cleanTitle = title.trim();
    setArtist(cleanArtist);
    setTitle(cleanTitle);
    if (cleanArtist !== track.artist || cleanTitle !== track.title) {
      props.onUpdateMetadata(track.id, cleanArtist, cleanTitle);
    }
  };
  const handleRowBlur = (event: FocusEvent<HTMLTableRowElement>) => {
    if (!(event.relatedTarget instanceof Node) || !event.currentTarget.contains(event.relatedTarget)) {
      saveMetadata();
    }
  };
  return (
    <tr className={selected ? "selected" : ""} onBlur={handleRowBlur} onClick={() => props.onSelect(track)}>
      <td><span className="track-number">{String(track.number).padStart(2, "0")}</span></td>
      <td onClick={stop}>
        <TimestampInput
          disabled={disabled || track.number === 1}
          label={`Inizio traccia ${track.number}`}
          onCommit={track.number > 1 ? (seconds) => props.onMoveMarker(track.number - 2, seconds) : undefined}
          value={track.start_seconds}
        />
      </td>
      <td onClick={stop}>
        <TimestampInput
          disabled={disabled || isLast}
          label={`Fine traccia ${track.number}`}
          onCommit={!isLast ? (seconds) => props.onMoveMarker(track.number - 1, seconds) : undefined}
          value={track.end_seconds}
        />
      </td>
      <td className="duration-cell">{formatTime(track.end_seconds - track.start_seconds, true)}</td>
      <td onClick={stop}><input className="metadata-cell" disabled={disabled} onChange={(event) => setArtist(event.target.value)} placeholder="Artista" value={artist} /></td>
      <td onClick={stop}><input className="metadata-cell title" disabled={disabled} onChange={(event) => setTitle(event.target.value)} placeholder={`Traccia ${track.number}`} value={title} /></td>
      <td><span className={`track-status ${artist || title ? "edited" : "manual"}`}><span />{artist || title ? "Modificata" : "Manuale"}</span></td>
      <td onClick={stop}>
        <div className="row-actions">
          <button aria-label={`Riproduci traccia ${track.number}`} onClick={() => props.onPlay(track)} title="Riproduci solo questa traccia" type="button"><Icon name="play" size={15} /></button>
          <button aria-label={`Riconosci traccia ${track.number}`} disabled={disabled} onClick={() => props.onRecognize(track)} title="Riconosci questa traccia" type="button"><Icon name="search" size={15} /></button>
          <button aria-label={`Modifica metadati traccia ${track.number}`} disabled={disabled} onClick={() => props.onEditMetadata(track)} title="Metadati e copertina" type="button"><Icon name="settings" size={15} /></button>
          <button aria-label={`Dividi traccia ${track.number}`} disabled={disabled} onClick={() => props.onSplit(track)} title="Dividi al cursore" type="button"><Icon name="split" size={15} /></button>
          <button aria-label={`Unisci traccia ${track.number} alla successiva`} disabled={disabled || isLast} onClick={() => props.onMerge(track)} title="Unisci alla successiva" type="button"><Icon name="trash" size={15} /></button>
        </div>
      </td>
    </tr>
  );
}
