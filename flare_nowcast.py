"""Flare probability lookup backed by the exported OVRO-LWA model."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


MODEL_PATH = (
    Path(__file__).resolve().parent
    / "models"
    / "lwa_nowcast_probability_v0.1.npz"
)


@lru_cache(maxsize=1)
def load_model(path: str | Path = MODEL_PATH) -> dict[str, Any]:
    """Load and cache the empirical probability model."""
    with np.load(path, allow_pickle=False) as archive:
        model = {key: archive[key] for key in archive.files}

    for key in (
        "window_s",
        "horizon_min",
        "flux_clip_min_sfu",
        "flux_clip_max_sfu",
        "min_valid_frac",
        "stat",
        "label_mode",
        "combine",
        "model_version",
        "created_utc",
    ):
        value = model.get(key)
        if getattr(value, "shape", None) == ():
            model[key] = value.item()

    model["class_names"] = [str(name) for name in model["class_names"].tolist()]
    for key in ("stat", "model_version", "created_utc"):
        if key in model:
            model[key] = str(model[key])
    return model


def feature_from_bands(
    band_flux: Mapping[int, Sequence[float]], model: Mapping[str, Any]
) -> float:
    """Build the model's weighted radio feature from recent 1-second fluxes."""
    frequencies = model["frequencies_mhz"]
    weights = model["weights"]
    window_s = int(model["window_s"])
    clip_low = float(model["flux_clip_min_sfu"])
    clip_high = float(model["flux_clip_max_sfu"])
    min_valid_fraction = float(model["min_valid_frac"])
    statistic = str(model["stat"])

    features: list[float] = []
    valid_weights: list[float] = []
    for frequency, weight in zip(frequencies, weights):
        if weight <= 0:
            continue

        samples = np.asarray(band_flux[int(frequency)], dtype=np.float64)
        if samples.size < window_s:
            continue

        window = samples[-window_s:]
        valid = (
            np.isfinite(window)
            & (window > 0)
            & (window >= clip_low)
            & (window <= clip_high)
        )
        if valid.sum() < min_valid_fraction * window_s:
            continue

        valid_samples = window[valid]
        feature = (
            float(np.nanmax(valid_samples))
            if statistic == "peak"
            else float(np.nanmedian(valid_samples))
        )
        features.append(feature)
        valid_weights.append(float(weight))

    if not features:
        return float("nan")

    normalized_weights = np.asarray(valid_weights)
    return float(
        np.sum(normalized_weights * np.asarray(features))
        / normalized_weights.sum()
    )


def lookup(
    feature_sfu: float, model: Mapping[str, Any], class_name: str
) -> dict[str, float | int]:
    """Look up one GOES class's probability and confidence interval."""
    class_index = model["class_names"].index(class_name)
    left = model["bin_left"][class_index]
    right = model["bin_right"][class_index]
    edges = np.concatenate([left, right[-1:]])
    bin_index = int(np.digitize([feature_sfu], edges)[0] - 1)
    bin_index = max(0, min(bin_index, left.size - 1))

    return {
        "probability": float(model["probability"][class_index, bin_index]),
        "p_low": float(model["p_low"][class_index, bin_index]),
        "p_high": float(model["p_high"][class_index, bin_index]),
        "n_total": int(model["n_total"][class_index, bin_index]),
        "feature_sfu": float(feature_sfu),
    }


def nowcast(
    band_flux: Mapping[int, Sequence[float]], model: Mapping[str, Any]
) -> dict[str, Any]:
    """Return nowcast probabilities for all GOES classes in the model."""
    feature = feature_from_bands(band_flux, model)
    result: dict[str, Any] = {
        "feature_sfu": float(feature) if np.isfinite(feature) else None,
        "horizon_min": float(model["horizon_min"]),
    }
    for class_name in model["class_names"]:
        result[class_name] = (
            lookup(feature, model, class_name) if np.isfinite(feature) else None
        )
    return result


def nowcast_from_flux3ch(
    flux3ch: Sequence[float], model: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Nowcast from one current SFU value at each of 40, 60, and 80 MHz.

    The exported model expects a trailing window. Because this API accepts a
    single current value per channel, each value is held constant over that
    window before applying the model's normal validity and lookup rules.
    """
    if len(flux3ch) != 3:
        raise ValueError("flux3ch must contain exactly three values")

    if model is None:
        model = load_model()

    frequencies = [int(value) for value in model["frequencies_mhz"]]
    window_s = int(model["window_s"])
    band_flux = {
        frequency: np.full(window_s, flux, dtype=np.float64)
        for frequency, flux in zip(frequencies, flux3ch)
    }
    result = nowcast(band_flux, model)
    result.update(
        {
            "frequencies_mhz": frequencies,
            "model_version": model.get("model_version"),
            "created_utc": model.get("created_utc"),
        }
    )
    return result
