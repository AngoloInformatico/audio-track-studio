import { useCallback, useEffect, useState } from "react";

import {
  applyRecognitionMetadata as applyRecognitionMetadataRequest,
  fetchTrackCover,
  getTracks,
  replaceMarkers,
  removeTrackCover,
  updateTrackMetadata,
  uploadTrackCover,
} from "../services/api";
import type {
  RecognitionMetadataItem,
  Track,
  TrackCollection,
  TrackMetadataUpdate,
} from "../types/audio";

const MIN_TRACK_SECONDS = 0.05;

export function useTrackEditor(audioId: string, duration: number) {
  const [collection, setCollection] = useState<TrackCollection>();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    getTracks(audioId)
      .then((value) => { if (active) { setCollection(value); setError(undefined); } })
      .catch((reason: unknown) => { if (active) setError(readMessage(reason)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [audioId]);

  const commitMarkers = useCallback(async (markers: number[]) => {
    const previous = collection;
    if (!previous) return undefined;
    setSaving(true);
    try {
      const updated = await replaceMarkers(audioId, markers);
      setCollection(updated);
      setError(undefined);
      return updated;
    } catch (reason) {
      setCollection({ markers: [...previous.markers], tracks: [...previous.tracks] });
      setError(readMessage(reason));
      return undefined;
    } finally {
      setSaving(false);
    }
  }, [audioId, collection]);

  const addMarker = useCallback(async (seconds: number) => {
    if (!collection) return undefined;
    const marker = Math.round(seconds * 1000) / 1000;
    const points = [0, ...collection.markers, duration];
    if (points.some((point) => Math.abs(point - marker) < MIN_TRACK_SECONDS)) {
      setError("Il nuovo confine è troppo vicino a un confine esistente.");
      return undefined;
    }
    const updated = await commitMarkers([...collection.markers, marker].sort((a, b) => a - b));
    return updated?.markers.findIndex((value) => value === marker);
  }, [collection, commitMarkers, duration]);

  const moveMarker = useCallback(async (index: number, seconds: number) => {
    if (!collection || index < 0 || index >= collection.markers.length) return;
    const markers = [...collection.markers];
    markers[index] = Math.round(seconds * 1000) / 1000;
    await commitMarkers(markers);
  }, [collection, commitMarkers]);

  const removeMarker = useCallback(async (index: number) => {
    if (!collection || index < 0 || index >= collection.markers.length) return;
    await commitMarkers(collection.markers.filter((_, markerIndex) => markerIndex !== index));
  }, [collection, commitMarkers]);

  const splitTrack = useCallback(async (track: Track, seconds: number) => {
    if (seconds - track.start_seconds < MIN_TRACK_SECONDS || track.end_seconds - seconds < MIN_TRACK_SECONDS) {
      setError("Posiziona il cursore almeno 50 ms all’interno della traccia da dividere.");
      return undefined;
    }
    return addMarker(seconds);
  }, [addMarker]);

  const mergeWithNext = useCallback(async (track: Track) => {
    await removeMarker(track.number - 1);
  }, [removeMarker]);

  const updateMetadata = useCallback(async (trackId: string, artist: string, title: string) => {
    setSaving(true);
    try {
      const updated = await updateTrackMetadata(audioId, trackId, { artist, title });
      setCollection(updated);
      setError(undefined);
    } catch (reason) {
      setError(readMessage(reason));
    } finally {
      setSaving(false);
    }
  }, [audioId]);

  const updateAdvancedMetadata = useCallback(async (trackId: string, update: TrackMetadataUpdate) => {
    setSaving(true);
    try {
      const updated = await updateTrackMetadata(audioId, trackId, update);
      setCollection(updated);
      setError(undefined);
      return true;
    } catch (reason) {
      setError(readMessage(reason));
      return false;
    } finally {
      setSaving(false);
    }
  }, [audioId]);

  const changeCover = useCallback(async (
    operation: () => Promise<TrackCollection>,
  ) => {
    setSaving(true);
    try {
      const updated = await operation();
      setCollection(updated);
      setError(undefined);
      return true;
    } catch (reason) {
      setError(readMessage(reason));
      return false;
    } finally {
      setSaving(false);
    }
  }, []);

  const uploadCover = useCallback(
    (trackId: string, file: File) => changeCover(() => uploadTrackCover(audioId, trackId, file)),
    [audioId, changeCover],
  );
  const fetchCover = useCallback(
    (trackId: string, releaseGroupId: string) => changeCover(
      () => fetchTrackCover(audioId, trackId, releaseGroupId),
    ),
    [audioId, changeCover],
  );
  const removeCover = useCallback(
    (trackId: string) => changeCover(() => removeTrackCover(audioId, trackId)),
    [audioId, changeCover],
  );

  const applySuggestedMarkers = useCallback(async (suggestions: number[]) => {
    if (!collection) return false;
    const merged = [...collection.markers];
    for (const suggestion of suggestions) {
      if (!merged.some((marker) => Math.abs(marker - suggestion) < MIN_TRACK_SECONDS)) {
        merged.push(Math.round(suggestion * 1000) / 1000);
      }
    }
    const updated = await commitMarkers(merged.sort((a, b) => a - b));
    return Boolean(updated);
  }, [collection, commitMarkers]);

  const applyRecognitionMetadata = useCallback(async (items: RecognitionMetadataItem[]) => {
    setSaving(true);
    try {
      const updated = await applyRecognitionMetadataRequest(audioId, items);
      setCollection(updated);
      setError(undefined);
      return true;
    } catch (reason) {
      setError(readMessage(reason));
      return false;
    } finally {
      setSaving(false);
    }
  }, [audioId]);

  return {
    collection,
    loading,
    saving,
    error,
    clearError: () => setError(undefined),
    addMarker,
    moveMarker,
    removeMarker,
    splitTrack,
    mergeWithNext,
    updateMetadata,
    updateAdvancedMetadata,
    uploadCover,
    fetchCover,
    removeCover,
    applySuggestedMarkers,
    applyRecognitionMetadata,
  };
}

function readMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Impossibile aggiornare l’editor delle tracce.";
}
