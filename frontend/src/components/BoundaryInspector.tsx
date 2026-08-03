import { Icon } from "./Icon";
import { TimestampInput } from "./TimestampInput";

interface BoundaryInspectorProps {
  index: number;
  time: number;
  disabled?: boolean;
  onChange: (seconds: number) => void;
  onDelete: () => void;
  onPreview: (start: number, end: number) => void;
  onZoom: () => void;
}

export function BoundaryInspector({
  index,
  time,
  disabled,
  onChange,
  onDelete,
  onPreview,
  onZoom,
}: BoundaryInspectorProps) {
  return (
    <div className="boundary-inspector">
      <div className="boundary-identity">
        <span className="marker-number">M{index + 1}</span>
        <div><span>CONFINE SELEZIONATO</span><strong>Fine traccia {index + 1} · Inizio traccia {index + 2}</strong></div>
      </div>
      <TimestampInput
        disabled={disabled}
        label={`Timestamp marker ${index + 1}`}
        onCommit={onChange}
        value={time}
      />
      <div className="boundary-preview" aria-label="Anteprima confine">
        <button disabled={disabled} onClick={() => onPreview(Math.max(0, time - 10), time)} title="Ascolta 10 secondi prima" type="button">−10s</button>
        <button className="around" disabled={disabled} onClick={() => onPreview(Math.max(0, time - 5), time + 5)} title="Ascolta intorno al confine" type="button"><Icon name="play" size={15} /> Confine</button>
        <button disabled={disabled} onClick={() => onPreview(time, time + 10)} title="Ascolta 10 secondi dopo" type="button">+10s</button>
      </div>
      <button className="icon-action" disabled={disabled} onClick={onZoom} title="Zoom preciso sul confine" type="button"><Icon name="search" size={17} /></button>
      <button className="icon-action danger" disabled={disabled} onClick={onDelete} title="Elimina marker e unisci le tracce" type="button"><Icon name="trash" size={17} /></button>
    </div>
  );
}
