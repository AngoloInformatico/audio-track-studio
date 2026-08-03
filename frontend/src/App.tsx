import { useEffect, useRef, useState } from "react";

import { AudioWorkspace } from "./components/AudioWorkspace";
import { AboutDialog } from "./components/AboutDialog";
import { CopyrightLink } from "./components/CopyrightLink";
import { ExportDialog } from "./components/ExportDialog";
import { Icon } from "./components/Icon";
import { ImportPanel } from "./components/ImportPanel";
import { ProjectsDialog } from "./components/ProjectsDialog";
import { SaveProjectDialog } from "./components/SaveProjectDialog";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { projectNameFromAudio, useProjectAutosave } from "./hooks/useProjectAutosave";
import { useTheme } from "./hooks/useTheme";
import { closeAudio, getHealth, openAudio, saveProject } from "./services/api";
import type {
  ActiveProject,
  AudioSession,
  HealthResponse,
  ProjectApplyResult,
  ProjectPreview,
  UploadState,
} from "./types/audio";

const ACCEPTED_AUDIO = ".flac,.wav,.mp3,.m4a,.aac,audio/flac,audio/wav,audio/mpeg,audio/mp4,audio/aac";

export default function App() {
  const { preference, setPreference } = useTheme();
  const [health, setHealth] = useState<HealthResponse>();
  const [session, setSession] = useState<AudioSession>();
  const [upload, setUpload] = useState<UploadState>({ status: "idle" });
  const [exportOpen, setExportOpen] = useState(false);
  const [analysisOpen, setAnalysisOpen] = useState(false);
  const [recognitionOpen, setRecognitionOpen] = useState(false);
  const [projectsOpen, setProjectsOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [saveDialog, setSaveDialog] = useState<{ saveAs: boolean }>();
  const [activeProject, setActiveProject] = useState<ActiveProject>();
  const [projectError, setProjectError] = useState<string>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const autosave = useProjectAutosave(session, activeProject, preference);

  useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      try {
        const value = await getHealth();
        if (active) setHealth(value);
      } catch {
        if (active) setHealth(undefined);
      }
    };
    void checkHealth();
    const interval = window.setInterval(() => void checkHealth(), 10_000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => () => { if (session) void closeAudio(session.id); }, [session]);

  const handleFile = async (file: File) => {
    setUpload({ status: "uploading", progress: 0 });
    try {
      const next = await openAudio(file, (progress) => setUpload({ status: "uploading", progress }));
      setSession(next);
      setActiveProject(undefined);
      setProjectError(undefined);
      setUpload({ status: "idle" });
    } catch (error) {
      setUpload({ status: "error", message: error instanceof Error ? error.message : "Errore inatteso." });
    }
  };

  const saveCurrentProject = async (name: string, autosaveEnabled: boolean, saveAs: boolean) => {
    if (!session) return;
    autosave.setEnabled(autosaveEnabled);
    autosave.setActivity("saving");
    setProjectError(undefined);
    try {
      const result = await saveProject({
        audio_id: session.id,
        name,
        project_id: activeProject?.id ?? undefined,
        save_as: saveAs,
        settings: { theme: preference, autosave_enabled: autosaveEnabled },
      });
      setActiveProject({ id: result.project.id, name: result.project.name, path: result.path, updated_at: result.project.updated_at });
      autosave.setActivity("saved");
      setSaveDialog(undefined);
    } catch (error) {
      autosave.setActivity("error");
      setProjectError(error instanceof Error ? error.message : "Impossibile salvare il progetto.");
    }
  };

  const quickSave = async () => {
    if (!session) return;
    if (!activeProject?.id) {
      setSaveDialog({ saveAs: false });
      setProjectError(undefined);
      return;
    }
    await saveCurrentProject(activeProject.name, autosave.enabled, false);
  };

  const openAudioPicker = () => {
    if (!session || window.confirm("Aprire un altro audio? Le modifiche non salvate potrebbero andare perse.")) {
      fileInputRef.current?.click();
    }
  };

  const projectOpened = (
    nextSession: AudioSession,
    applied: ProjectApplyResult,
    preview: ProjectPreview,
  ) => {
    setSession(nextSession);
    setProjectError(undefined);
    setActiveProject({ id: applied.persisted_project_id, name: preview.name, updated_at: applied.project.updated_at });
    setPreference(preview.settings.theme);
    autosave.setEnabled(preview.settings.autosave_enabled);
    autosave.setActivity("saved");
    setUpload({ status: "idle" });
  };

  const backendOnline = health?.status === "ok" && health.tools.ffprobe?.available === true;
  const anyModalOpen = exportOpen || analysisOpen || recognitionOpen || projectsOpen || aboutOpen || Boolean(saveDialog);
  return (
    <div className="app-shell">
      <input
        accept={ACCEPTED_AUDIO}
        aria-label="Scegli file audio"
        className="global-file-input"
        disabled={!backendOnline || upload.status === "uploading" || anyModalOpen}
        onChange={(event) => {
          const file = event.currentTarget.files?.item(0);
          if (file) void handleFile(file);
          event.currentTarget.value = "";
        }}
        ref={fileInputRef}
        type="file"
      />
      <Sidebar backendOnline={backendOnline} onAbout={() => setAboutOpen(true)} onProjects={() => setProjectsOpen(true)} />
      <div className={`app-main ${session ? "has-session" : "empty"}`}>
        <Topbar
          canAnalyze={Boolean(session)}
          canExport={Boolean(session)}
          canRecognize={Boolean(session)}
          canSave={Boolean(session)}
          fileName={session?.info.name}
          modalOpen={anyModalOpen}
          onAnalyze={() => setAnalysisOpen(true)}
          onExport={() => setExportOpen(true)}
          onOpen={openAudioPicker}
          onRecognize={() => setRecognitionOpen(true)}
          onSave={() => void quickSave()}
          projectActivity={autosave.activity}
          projectName={activeProject?.name}
          onThemeChange={setPreference}
          preference={preference}
        />
        <main className="content">
          {projectError && !saveDialog && <div className="editor-notice" role="alert"><Icon name="info" size={17} /><span>{projectError}</span><button onClick={() => setProjectError(undefined)} type="button">Chiudi</button></div>}
          {session ? (
            <AudioWorkspace
              analysisOpen={analysisOpen}
              key={session.id}
              onCloseAnalysis={() => setAnalysisOpen(false)}
              onCloseRecognition={() => setRecognitionOpen(false)}
              recognitionOpen={recognitionOpen}
              session={session}
            />
          ) : (
            <ImportPanel
              backendOnline={backendOnline}
              onFile={handleFile}
              onOpen={openAudioPicker}
              upload={upload}
            />
          )}
        </main>
        <footer className="main-copyright-footer">
          <CopyrightLink className="main-copyright" />
        </footer>
      </div>
      {session && exportOpen && <ExportDialog onClose={() => setExportOpen(false)} session={session} />}
      {aboutOpen && <AboutDialog onClose={() => setAboutOpen(false)} />}
      {projectsOpen && (
        <ProjectsDialog
          hasSession={Boolean(session)}
          onClose={() => setProjectsOpen(false)}
          onNew={() => { setSession(undefined); setActiveProject(undefined); setProjectError(undefined); autosave.setActivity(undefined); }}
          onOpened={projectOpened}
          onSaveAs={() => { setProjectsOpen(false); setProjectError(undefined); setSaveDialog({ saveAs: true }); }}
        />
      )}
      {session && saveDialog && (
        <SaveProjectDialog
          autosaveEnabled={autosave.enabled}
          error={projectError}
          initialName={activeProject?.name ?? projectNameFromAudio(session.info.name)}
          onClose={() => { setSaveDialog(undefined); setProjectError(undefined); }}
          onSave={(name, enabled) => saveCurrentProject(name, enabled, saveDialog.saveAs)}
          saveAs={saveDialog.saveAs}
          saving={autosave.activity === "saving"}
        />
      )}
    </div>
  );
}
