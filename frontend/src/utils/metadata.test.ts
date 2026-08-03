import { describe, expect, it } from "vitest";

import type { Track } from "../types/audio";
import { metadataFormFromTrack, metadataUpdateFromForm } from "./metadata";

const track: Track = {
  id: "track",
  number: 1,
  start_seconds: 0,
  end_seconds: 10,
  artist: "Artist",
  title: "Title",
  album: "Album",
  album_artist: "Album Artist",
  track_number: 4,
  disc_number: null,
  date: "2026",
  genre: "Electronic",
  comment: "Comment",
  composer: "Composer",
  release_group_id: null,
  recognition_provider: null,
  recognition_external_id: null,
  recognition_recording_id: null,
  recognition_confidence: null,
  cover: null,
};

describe("advanced metadata form", () => {
  it("maps a track without inventing a disc number", () => {
    const form = metadataFormFromTrack(track);

    expect(form.trackNumber).toBe("4");
    expect(form.discNumber).toBe("");
    expect(form.albumArtist).toBe("Album Artist");
  });

  it("trims text and converts optional numeric fields", () => {
    const form = metadataFormFromTrack(track);
    const update = metadataUpdateFromForm({
      ...form,
      title: "  New title  ",
      discNumber: "2",
      genre: "  Rock  ",
    });

    expect(update.title).toBe("New title");
    expect(update.track_number).toBe(4);
    expect(update.disc_number).toBe(2);
    expect(update.genre).toBe("Rock");
  });
});
