import pytest

from backend.models.recognition import RecognitionMetadataItem
from backend.models.tracks import CoverInfo
from backend.tracks.store import TrackStore, TrackStoreError


def test_markers_create_contiguous_tracks_and_preserve_metadata() -> None:
    store = TrackStore()
    initial = store.initialize("audio", 600.0)
    store.update_metadata("audio", initial.tracks[0].id, "Artist", "Long Mix")

    split = store.replace_markers("audio", [120.25, 300.0])

    assert split.markers == [120.25, 300.0]
    assert [(track.start_seconds, track.end_seconds) for track in split.tracks] == [
        (0.0, 120.25),
        (120.25, 300.0),
        (300.0, 600.0),
    ]
    assert split.tracks[0].artist == "Artist"
    assert split.tracks[0].title == "Long Mix"

    moved = store.replace_markers("audio", [121.0, 300.0])
    assert moved.tracks[0].id == split.tracks[0].id
    assert moved.tracks[0].artist == "Artist"


def test_source_fallbacks_are_applied_to_new_tracks() -> None:
    store = TrackStore()
    source_cover = CoverInfo(
        url="/api/audio/audio/source-cover",
        mime_type="image/jpeg",
        size_bytes=123,
        source="source",
    )

    initial = store.initialize(
        "audio",
        90.0,
        default_artist="Source title",
        source_cover=source_cover,
    )
    split = store.replace_markers("audio", [30.0, 60.0])

    assert initial.tracks[0].artist == "Source title"
    assert all(track.artist == "Source title" for track in split.tracks)
    assert all(track.cover is not None for track in split.tracks)
    assert all(track.cover.source == "source" for track in split.tracks if track.cover)
    assert [track.cover.url for track in split.tracks if track.cover] == [
        f"/api/audio/audio/tracks/{track.id}/cover" for track in split.tracks
    ]


@pytest.mark.parametrize("markers", [[10.0, 5.0], [0.0], [100.0], [99.98]])
def test_invalid_markers_are_rejected(markers: list[float]) -> None:
    store = TrackStore()
    store.initialize("audio", 100.0)

    with pytest.raises(TrackStoreError):
        store.replace_markers("audio", markers)


def test_removing_marker_merges_tracks() -> None:
    store = TrackStore()
    store.initialize("audio", 90.0)
    store.replace_markers("audio", [30.0, 60.0])

    merged = store.replace_markers("audio", [60.0])

    assert len(merged.tracks) == 2
    assert merged.tracks[0].start_seconds == 0.0
    assert merged.tracks[0].end_seconds == 60.0


def test_recognition_metadata_batch_is_atomic() -> None:
    store = TrackStore()
    store.initialize("audio", 60.0)
    split = store.replace_markers("audio", [30.0])

    updated = store.update_metadata_batch(
        "audio",
        [
            RecognitionMetadataItem(
                track_id=split.tracks[0].id,
                artist=" Artist One ",
                title=" Song One ",
            ),
            RecognitionMetadataItem(
                track_id=split.tracks[1].id,
                artist="Artist Two",
                title="Song Two",
            ),
        ],
    )

    assert [(track.artist, track.title) for track in updated.tracks] == [
        ("Artist One", "Song One"),
        ("Artist Two", "Song Two"),
    ]

    with pytest.raises(TrackStoreError):
        store.update_metadata_batch(
            "audio",
            [
                RecognitionMetadataItem(
                    track_id=split.tracks[0].id,
                    artist="Changed",
                    title="Changed",
                ),
                RecognitionMetadataItem(track_id="missing", artist="X", title="Y"),
            ],
        )

    unchanged = store.get("audio")
    assert unchanged.tracks[0].artist == "Artist One"
