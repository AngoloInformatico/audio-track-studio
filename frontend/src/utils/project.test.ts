import { describe, expect, it } from "vitest";

import { projectNameFromAudio } from "../hooks/useProjectAutosave";

describe("projectNameFromAudio", () => {
  it("removes only the final audio extension", () => {
    expect(projectNameFromAudio("live.mix.2026.flac")).toBe("live.mix.2026");
  });

  it("keeps a useful fallback for an empty stem", () => {
    expect(projectNameFromAudio(".wav")).toBe("Nuovo progetto");
  });
});
