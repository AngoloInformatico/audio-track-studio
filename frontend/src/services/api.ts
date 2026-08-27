import type {
  AcoustIDSetupStatus,
  AcoustIDSetupUpdate,
  AnalysisConfig,
  AnalysisOptions,
  AnalysisResult,
  AudioSession,
  ExportConfig,
  ExportOptions,
  ExportResult,
  HealthResponse,
  JobView,
  ProjectApplyResult,
  ProjectPreview,
  ProjectSaveResult,
  ProjectSettings,
  ProjectSummary,
  RecognitionConfig,
  RecognitionMetadataItem,
  RecognitionOptions,
  RecognitionResult,
  TrackCollection,
  TrackMetadataUpdate,
} from "../types/audio";

const API_ROOT = "/api";

export class ApiError extends Error {}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(`${API_ROOT}/health`);
}

export function openAudio(file: File, onProgress: (progress: number) => void): Promise<AudioSession> {
  return new Promise((resolve, reject) => {
    const data = new FormData();
    data.append("file", file);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_ROOT}/audio/open`);
    xhr.responseType = "json";
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    });
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as AudioSession);
        return;
      }
      reject(new ApiError(readError(xhr.response) ?? "Impossibile aprire il file audio."));
    });
    xhr.addEventListener("error", () => reject(new ApiError("Il backend locale non è raggiungibile.")));
    xhr.send(data);
  });
}

export async function closeAudio(audioId: string): Promise<void> {
  const response = await fetch(`${API_ROOT}/audio/${encodeURIComponent(audioId)}`, { method: "DELETE" });
  if (!response.ok && response.status !== 404) throw new ApiError("Impossibile chiudere la sessione audio.");
}

export async function getTracks(audioId: string): Promise<TrackCollection> {
  return request<TrackCollection>(`${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks`);
}

export async function replaceMarkers(audioId: string, markers: number[]): Promise<TrackCollection> {
  return request<TrackCollection>(`${API_ROOT}/audio/${encodeURIComponent(audioId)}/markers`, {
    method: "PUT",
    body: JSON.stringify({ markers }),
  });
}

export async function updateTrackMetadata(
  audioId: string,
  trackId: string,
  update: TrackMetadataUpdate,
): Promise<TrackCollection> {
  return request<TrackCollection>(
    `${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks/${encodeURIComponent(trackId)}`,
    { method: "PATCH", body: JSON.stringify(update) },
  );
}

export async function uploadTrackCover(
  audioId: string,
  trackId: string,
  file: File,
): Promise<TrackCollection> {
  const data = new FormData();
  data.append("file", file);
  return requestForm<TrackCollection>(
    `${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks/${encodeURIComponent(trackId)}/cover`,
    data,
  );
}

export async function fetchTrackCover(
  audioId: string,
  trackId: string,
  releaseGroupId: string,
): Promise<TrackCollection> {
  return request<TrackCollection>(
    `${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks/${encodeURIComponent(trackId)}/cover/from-release-group`,
    { method: "POST", body: JSON.stringify({ release_group_id: releaseGroupId }) },
  );
}

export async function removeTrackCover(audioId: string, trackId: string): Promise<TrackCollection> {
  return request<TrackCollection>(
    `${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks/${encodeURIComponent(trackId)}/cover`,
    { method: "DELETE" },
  );
}

export async function applyRecognitionMetadata(
  audioId: string,
  items: RecognitionMetadataItem[],
): Promise<TrackCollection> {
  return request<TrackCollection>(`${API_ROOT}/audio/${encodeURIComponent(audioId)}/tracks`, {
    method: "PATCH",
    body: JSON.stringify({ items }),
  });
}

export async function getRecentProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>(`${API_ROOT}/projects/recent`);
}

export async function getRecoveryProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>(`${API_ROOT}/projects/recovery`);
}

export async function inspectProject(file: File): Promise<ProjectPreview> {
  const data = new FormData();
  data.append("file", file);
  return requestForm<ProjectPreview>(`${API_ROOT}/projects/inspect`, data);
}

export async function prepareProject(
  projectId?: string,
  recoveryId?: string,
): Promise<ProjectPreview> {
  return request<ProjectPreview>(`${API_ROOT}/projects/prepare`, {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, recovery_id: recoveryId }),
  });
}

export async function applyProject(token: string, audioId: string): Promise<ProjectApplyResult> {
  return request<ProjectApplyResult>(`${API_ROOT}/projects/apply`, {
    method: "POST",
    body: JSON.stringify({ token, audio_id: audioId }),
  });
}

export async function saveProject(options: {
  audio_id: string;
  name: string;
  project_id?: string;
  save_as: boolean;
  settings: ProjectSettings;
}): Promise<ProjectSaveResult> {
  return request<ProjectSaveResult>(`${API_ROOT}/projects/save`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export async function autosaveProject(options: {
  audio_id: string;
  name: string;
  project_id?: string;
  settings: ProjectSettings;
}): Promise<ProjectSummary> {
  return request<ProjectSummary>(`${API_ROOT}/projects/autosave`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export async function getExportConfig(): Promise<ExportConfig> {
  return request<ExportConfig>(`${API_ROOT}/export/config`);
}

export async function startExport(options: ExportOptions): Promise<JobView<ExportResult>> {
  return request<JobView<ExportResult>>(`${API_ROOT}/export/start`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export async function getAnalysisConfig(): Promise<AnalysisConfig> {
  return request<AnalysisConfig>(`${API_ROOT}/analysis/config`);
}

export async function startAnalysis(options: AnalysisOptions): Promise<JobView<AnalysisResult>> {
  return request<JobView<AnalysisResult>>(`${API_ROOT}/analysis/start`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export async function getRecognitionConfig(): Promise<RecognitionConfig> {
  return request<RecognitionConfig>(`${API_ROOT}/recognition/config`);
}

export async function getAcoustIDSetup(): Promise<AcoustIDSetupStatus> {
  return request<AcoustIDSetupStatus>(`${API_ROOT}/recognition/setup`);
}

export async function updateAcoustIDSetup(
  update: AcoustIDSetupUpdate,
): Promise<AcoustIDSetupStatus> {
  return request<AcoustIDSetupStatus>(`${API_ROOT}/recognition/setup`, {
    method: "PUT",
    body: JSON.stringify(update),
  });
}

export async function installFpcalc(): Promise<AcoustIDSetupStatus> {
  return request<AcoustIDSetupStatus>(`${API_ROOT}/recognition/setup/install-fpcalc`, {
    method: "POST",
  });
}

export async function startRecognition(
  options: RecognitionOptions,
): Promise<JobView<RecognitionResult>> {
  return request<JobView<RecognitionResult>>(`${API_ROOT}/recognition/start`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export async function getJob<TResult>(jobId: string): Promise<JobView<TResult>> {
  return request<JobView<TResult>>(`${API_ROOT}/jobs/${encodeURIComponent(jobId)}`);
}

export async function cancelJob<TResult>(jobId: string): Promise<JobView<TResult>> {
  return request<JobView<TResult>>(`${API_ROOT}/jobs/${encodeURIComponent(jobId)}`, { method: "DELETE" });
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = undefined;
    }
    throw new ApiError(readError(payload) ?? `Errore API (${response.status}).`);
  }
  return (await response.json()) as T;
}

async function requestForm<T>(url: string, body: FormData): Promise<T> {
  const response = await fetch(url, { method: "POST", body, headers: { Accept: "application/json" } });
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = undefined;
    }
    throw new ApiError(readError(payload) ?? `Errore API (${response.status}).`);
  }
  return (await response.json()) as T;
}

function readError(payload: unknown): string | undefined {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) return undefined;
  const detail = payload.detail;
  return typeof detail === "string" ? detail : undefined;
}
