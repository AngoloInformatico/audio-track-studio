export function formatTime(seconds: number, milliseconds: boolean): string {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const totalMilliseconds = Math.round(safe * 1000);
  const totalSeconds = milliseconds ? Math.floor(totalMilliseconds / 1000) : Math.floor(safe);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const wholeSeconds = totalSeconds % 60;
  const hourPart = hours > 0 ? `${String(hours).padStart(2, "0")}:` : "";
  const base = `${hourPart}${String(minutes).padStart(2, "0")}:${String(wholeSeconds).padStart(2, "0")}`;
  return milliseconds ? `${base}.${String(totalMilliseconds % 1000).padStart(3, "0")}` : base;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"] as const;
  let value = bytes / 1024;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[index]}`;
}

export function parseTimestamp(value: string): number | undefined {
  const trimmed = value.trim().replace(",", ".");
  if (!trimmed) return undefined;
  const parts = trimmed.split(":");
  if (parts.length > 3 || parts.some((part) => part.trim() === "")) return undefined;
  const numbers = parts.map(Number);
  if (numbers.some((part) => !Number.isFinite(part) || part < 0)) return undefined;
  const seconds = numbers.at(-1) ?? 0;
  const minutes = numbers.length >= 2 ? (numbers.at(-2) ?? 0) : 0;
  const hours = numbers.length === 3 ? (numbers[0] ?? 0) : 0;
  if (seconds >= 60 || minutes >= 60) return undefined;
  return Math.round((hours * 3600 + minutes * 60 + seconds) * 1000) / 1000;
}
