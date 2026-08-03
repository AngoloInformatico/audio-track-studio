import { useCallback, useEffect, useState } from "react";

import { autosaveProject } from "../services/api";
import type { ActiveProject, AudioSession, ProjectSettings } from "../types/audio";
import type { ThemePreference } from "./useTheme";

const STORAGE_KEY = "ats-autosave-enabled";

export type ProjectActivity = "saving" | "saved" | "autosaved" | "error";

export function useProjectAutosave(
  session: AudioSession | undefined,
  project: ActiveProject | undefined,
  theme: ThemePreference,
) {
  const [enabled, setEnabledState] = useState(() => localStorage.getItem(STORAGE_KEY) === "true");
  const [activity, setActivity] = useState<ProjectActivity>();

  const setEnabled = useCallback((value: boolean) => {
    setEnabledState(value);
    localStorage.setItem(STORAGE_KEY, String(value));
  }, []);

  useEffect(() => {
    if (!session || !enabled) return;
    let active = true;
    const save = async () => {
      if (!active) return;
      setActivity("saving");
      const settings: ProjectSettings = { theme, autosave_enabled: true };
      try {
        await autosaveProject({
          audio_id: session.id,
          name: project?.name ?? projectNameFromAudio(session.info.name),
          project_id: project?.id ?? undefined,
          settings,
        });
        if (active) setActivity("autosaved");
      } catch {
        if (active) setActivity("error");
      }
    };
    const initial = window.setTimeout(() => void save(), 5_000);
    const interval = window.setInterval(() => void save(), 60_000);
    return () => {
      active = false;
      window.clearTimeout(initial);
      window.clearInterval(interval);
    };
  }, [enabled, project?.id, project?.name, session, theme]);

  return { enabled, setEnabled, activity, setActivity };
}

export function projectNameFromAudio(filename: string): string {
  return filename.replace(/\.[^.]+$/, "") || "Nuovo progetto";
}
