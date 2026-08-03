import { useState, type KeyboardEvent } from "react";

import { formatTime, parseTimestamp } from "../utils/format";

interface TimestampInputProps {
  value: number;
  label: string;
  disabled?: boolean;
  onCommit?: (seconds: number) => void;
}

export function TimestampInput({ value, label, disabled, onCommit }: TimestampInputProps) {
  const formatted = formatTime(value, true);
  const [draft, setDraft] = useState<string>();
  const [invalid, setInvalid] = useState(false);

  const commit = () => {
    if (draft === undefined) return;
    const parsed = parseTimestamp(draft);
    if (parsed === undefined) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setDraft(undefined);
    if (Math.abs(parsed - value) >= 0.0005) onCommit?.(parsed);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") event.currentTarget.blur();
    if (event.key === "Escape") {
      setDraft(undefined);
      setInvalid(false);
      event.currentTarget.blur();
    }
  };

  return (
    <input
      aria-invalid={invalid}
      aria-label={label}
      className={`timestamp-input ${invalid ? "invalid" : ""}`}
      disabled={disabled}
      onBlur={commit}
      onChange={(event) => { setDraft(event.target.value); setInvalid(false); }}
      onKeyDown={handleKeyDown}
      spellCheck={false}
      title="Formato: HH:MM:SS.mmm"
      value={draft ?? formatted}
    />
  );
}
