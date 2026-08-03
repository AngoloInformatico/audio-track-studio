import numpy as np

from backend.analysis.service import AnalysisService, _Features


def test_analysis_detects_separated_quiet_transitions() -> None:
    times = np.arange(0.25, 60.0, 0.5)
    rms = np.full(len(times), -12.0)
    centroid = np.full(len(times), 0.2)
    flux = np.zeros(len(times))
    rms[38:42] = -78.0
    rms[78:82] = -72.0
    centroid[42:] = 0.65
    centroid[82:] = 0.35
    flux[42] = 0.9
    flux[82] = 0.8
    features = _Features(times, rms, centroid, flux)

    suggestions = AnalysisService()._detect_candidates(
        features,
        duration=60.0,
        sensitivity=60,
        minimum_track_seconds=10.0,
    )

    assert len(suggestions) == 2
    assert abs(suggestions[0].timestamp_seconds - 20.0) < 1.5
    assert abs(suggestions[1].timestamp_seconds - 40.0) < 1.5
    assert all(suggestion.confidence >= 0.58 for suggestion in suggestions)
    assert all("silenzio/calo di volume" in suggestion.signals for suggestion in suggestions)


def test_analysis_returns_no_candidate_for_steady_audio() -> None:
    times = np.arange(0.25, 40.0, 0.5)
    features = _Features(
        times,
        np.full(len(times), -14.0),
        np.full(len(times), 0.3),
        np.zeros(len(times)),
    )

    suggestions = AnalysisService()._detect_candidates(
        features,
        duration=40.0,
        sensitivity=100,
        minimum_track_seconds=5.0,
    )

    assert suggestions == []
