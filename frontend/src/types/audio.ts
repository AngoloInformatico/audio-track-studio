export interface AudioInfo {
  name: string;
  format: string;
  codec: string | null;
  duration_seconds: number;
  sample_rate: number | null;
  bit_depth: number | null;
  channels: number | null;
  channel_layout: string | null;
  bitrate: number | null;
  size_bytes: number;
}

export interface AudioSession {
  id: string;
  info: AudioInfo;
  stream_url: string;
}

export interface Track {
  id: string;
  number: number;
  start_seconds: number;
  end_seconds: number;
  artist: string;
  title: string;
  album: string;
  album_artist: string;
  track_number: number | null;
  disc_number: number | null;
  date: string;
  genre: string;
  comment: string;
  composer: string;
  release_group_id: string | null;
  recognition_provider: string | null;
  recognition_external_id: string | null;
  recognition_recording_id: string | null;
  recognition_confidence: number | null;
  cover: CoverInfo | null;
}

export interface CoverInfo {
  url: string;
  mime_type: "image/jpeg" | "image/png";
  size_bytes: number;
  source: "manual" | "cover_art_archive" | "source";
}

export interface TrackMetadataUpdate {
  artist?: string;
  title?: string;
  album?: string;
  album_artist?: string;
  track_number?: number | null;
  disc_number?: number | null;
  date?: string;
  genre?: string;
  comment?: string;
  composer?: string;
}

export interface TrackCollection {
  markers: number[];
  tracks: Track[];
}

export interface ProjectSettings {
  theme: "light" | "dark" | "system";
  autosave_enabled: boolean;
}

export interface ProjectSource {
  name: string;
  size_bytes: number;
  duration_seconds: number;
  format: string;
  sha256: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  source_name: string;
  created_at: string;
  updated_at: string;
  track_count: number;
  has_covers: boolean;
  kind: "saved" | "recovery";
  download_url: string | null;
}

export interface ProjectPreview {
  token: string;
  name: string;
  source: ProjectSource;
  track_count: number;
  has_covers: boolean;
  settings: ProjectSettings;
  persisted_project_id: string | null;
}

export interface ProjectApplyResult {
  project: ProjectSummary;
  persisted_project_id: string | null;
  markers: number[];
  track_count: number;
}

export interface ProjectSaveResult {
  project: ProjectSummary;
  path: string;
}

export interface ActiveProject {
  id: string | null;
  name: string;
  path?: string;
  updated_at?: string;
}

export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface ExportResult {
  destination: string;
  files: string[];
  count: number;
  format: "flac";
  audio_strategy: "lossless_reencode";
  cover_files: string[];
}

export interface BoundarySuggestion {
  timestamp_seconds: number;
  confidence: number;
  signals: string[];
}

export interface AnalysisResult {
  suggestions: BoundarySuggestion[];
  duration_seconds: number;
  analyzed_windows: number;
  sensitivity: number;
  minimum_track_seconds: number;
  method: "silence_energy_spectral";
}

export interface AnalysisConfig {
  default_sensitivity: number;
  default_minimum_track_seconds: number;
  sample_rate: number;
  window_seconds: number;
  method_note: string;
}

export interface AnalysisOptions {
  audio_id: string;
  sensitivity: number;
  minimum_track_seconds: number;
}

export interface RecognitionConfig {
  provider: "acoustid";
  available: boolean;
  fpcalc_available: boolean;
  fpcalc_version: string | null;
  api_key_configured: boolean;
  online_required: boolean;
  maximum_sample_seconds: number;
  message: string;
}

export interface RecognitionCandidate {
  artist: string;
  title: string;
  album: string | null;
  date: string | null;
  confidence: number;
  provider: string;
  external_id: string | null;
  recording_id: string | null;
  release_group_id: string | null;
}

export interface TrackRecognition {
  track_id: string;
  track_number: number;
  status: "matched" | "unmatched" | "error";
  candidates: RecognitionCandidate[];
  error: string | null;
}

export interface RecognitionResult {
  provider: string;
  tracks: TrackRecognition[];
  matched_count: number;
  unmatched_count: number;
  error_count: number;
}

export interface RecognitionOptions {
  audio_id: string;
  track_ids?: string[];
  max_candidates: number;
}

export interface RecognitionMetadataItem {
  track_id: string;
  artist: string;
  title: string;
  album?: string | null;
  date?: string | null;
  release_group_id?: string | null;
  provider?: string | null;
  external_id?: string | null;
  recording_id?: string | null;
  confidence?: number | null;
}

export interface JobView<TResult = ExportResult | AnalysisResult | RecognitionResult> {
  id: string;
  kind: string;
  status: JobStatus;
  progress: number;
  message: string;
  result: TResult | null;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface ExportConfig {
  default_directory: string;
  default_template: string;
  formats: string[];
  mode_note: string;
}

export interface ExportOptions {
  audio_id: string;
  destination: string;
  format: "flac";
  filename_template: string;
  overwrite: boolean;
  embed_metadata: boolean;
  embed_cover: boolean;
  save_cover_file: boolean;
  compression_level: number;
}

export interface ToolStatus {
  available: boolean;
  version: string | null;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  tools: Record<string, ToolStatus>;
}

export type UploadState =
  | { status: "idle" }
  | { status: "uploading"; progress: number }
  | { status: "error"; message: string };
