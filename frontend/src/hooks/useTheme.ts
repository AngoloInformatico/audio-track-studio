import { useEffect, useState } from "react";

export type ThemePreference = "light" | "dark" | "system";

const STORAGE_KEY = "ats-theme";

function initialPreference(): ThemePreference {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "light" || stored === "dark" || stored === "system" ? stored : "system";
}

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(initialPreference);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
      const resolved = preference === "system" ? (media.matches ? "dark" : "light") : preference;
      document.documentElement.dataset.theme = resolved;
      document.documentElement.style.colorScheme = resolved;
      localStorage.setItem(STORAGE_KEY, preference);
    };
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [preference]);

  return { preference, setPreference };
}
