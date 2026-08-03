import type { Track, TrackMetadataUpdate } from "../types/audio";

export interface MetadataFormValue {
  title: string;
  artist: string;
  album: string;
  albumArtist: string;
  trackNumber: string;
  discNumber: string;
  date: string;
  genre: string;
  comment: string;
  composer: string;
}

export function metadataFormFromTrack(track: Track): MetadataFormValue {
  return {
    title: track.title,
    artist: track.artist,
    album: track.album,
    albumArtist: track.album_artist,
    trackNumber: track.track_number ? String(track.track_number) : "",
    discNumber: track.disc_number ? String(track.disc_number) : "",
    date: track.date,
    genre: track.genre,
    comment: track.comment,
    composer: track.composer,
  };
}

export function metadataUpdateFromForm(form: MetadataFormValue): TrackMetadataUpdate {
  return {
    title: form.title.trim(),
    artist: form.artist.trim(),
    album: form.album.trim(),
    album_artist: form.albumArtist.trim(),
    track_number: parseOptionalNumber(form.trackNumber),
    disc_number: parseOptionalNumber(form.discNumber),
    date: form.date.trim(),
    genre: form.genre.trim(),
    comment: form.comment.trim(),
    composer: form.composer.trim(),
  };
}

function parseOptionalNumber(value: string): number | null {
  return value ? Number(value) : null;
}
