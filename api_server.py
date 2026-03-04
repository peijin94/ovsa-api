from datetime import datetime, timedelta

import ephem
import pytz
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


app = FastAPI()


# Observer location for OVRO (update lat/lon/elevation here if needed)
OVRO_LAT = "37.2332"  # degrees North, positive
OVRO_LON = "-118.2872"  # degrees East, negative for West
OVRO_ELEV_M = 1222  # meters


# Simple in-memory cache for ephemeris data
_EPHM_CACHE: dict | None = None


def _get_observer() -> ephem.Observer:
    """Return an ephem.Observer configured for OVRO at current UTC."""
    obs = ephem.Observer()
    obs.lat = OVRO_LAT
    obs.lon = OVRO_LON
    obs.elevation = OVRO_ELEV_M
    obs.date = datetime.now(pytz.UTC)
    return obs


def _sun_alt_az(observer: ephem.Observer | None = None) -> tuple[float, float, ephem.Observer, ephem.Sun]:
    """Compute Sun altitude and azimuth in degrees for the given observer."""
    if observer is None:
        observer = _get_observer()

    sun = ephem.Sun()
    sun.compute(observer)

    alt_deg = float(sun.alt) * 180.0 / ephem.pi
    az_deg = float(sun.az) * 180.0 / ephem.pi
    return alt_deg, az_deg, observer, sun


def _compute_ephm_all() -> dict:
    """
    Compute all Sun ephemeris values once.

    This is relatively expensive, so callers should use _get_ephm_all()
    which applies a short (1 s) cache.
    """
    alt_deg, az_deg, observer, sun = _sun_alt_az()

    # Current time at the observer (UTC)
    current_utc = observer.date.datetime().replace(tzinfo=pytz.UTC)

    # Sunrise / sunset around current day
    next_sunrise = observer.next_rising(sun).datetime().replace(tzinfo=pytz.UTC)
    next_sunset = observer.next_setting(sun).datetime().replace(tzinfo=pytz.UTC)
    prev_sunrise = observer.previous_rising(sun).datetime().replace(tzinfo=pytz.UTC)
    prev_sunset = observer.previous_setting(sun).datetime().replace(tzinfo=pytz.UTC)

    # Use today's sunrise if it already happened, otherwise the upcoming one
    sunrise_time = prev_sunrise if prev_sunrise.date() == current_utc.date() else next_sunrise
    # For simplicity, report the upcoming sunset
    sunset_time = next_sunset

    sunup_flag = 1 if alt_deg > 0.0 else 0

    info = (
        f"time={current_utc.isoformat()} "
        f"alt={alt_deg:.2f}deg az={az_deg:.2f}deg "
        f"sunup={sunup_flag} "
        f"sunrise={sunrise_time.isoformat()} "
        f"sunset={sunset_time.isoformat()}"
    )

    return {
        "current_utc": current_utc,
        "alt_deg": alt_deg,
        "az_deg": az_deg,
        "sunup_flag": sunup_flag,
        "sunrise_time": sunrise_time,
        "sunset_time": sunset_time,
        "info": info,
    }


def _get_ephm_all() -> dict:
    """
    Return cached Sun ephemeris, recomputing at most once per second.
    """
    global _EPHM_CACHE

    now = datetime.now(pytz.UTC)
    if not _EPHM_CACHE:
        data = _compute_ephm_all()
        _EPHM_CACHE = {
            "expires_at": now + timedelta(seconds=1),
            "data": data,
        }
        return data

    expires_at = _EPHM_CACHE.get("expires_at")
    if expires_at is None or now >= expires_at:
        data = _compute_ephm_all()
        _EPHM_CACHE = {
            "expires_at": now + timedelta(seconds=1),
            "data": data,
        }
        return data

    return _EPHM_CACHE["data"]


@app.get("/api/ephm/el", response_class=PlainTextResponse)
async def ephm_el() -> str:
    """Return current Sun elevation (altitude) in degrees at OVRO."""
    ephm = _get_ephm_all()
    return f"{ephm['alt_deg']:.6f}"


@app.get("/api/ephm/az", response_class=PlainTextResponse)
async def ephm_az() -> str:
    """Return current Sun azimuth in degrees at OVRO."""
    ephm = _get_ephm_all()
    return f"{ephm['az_deg']:.6f}"


@app.get("/api/ephm/sunup", response_class=PlainTextResponse)
async def ephm_sunup() -> str:
    """
    Check if the Sun is above the horizon.

    Returns "1" if Sun altitude > 0 degrees, otherwise "0".
    """
    ephm = _get_ephm_all()
    return "1" if ephm["sunup_flag"] == 1 else "0"


@app.get("/api/ephm/info", response_class=PlainTextResponse)
async def ephm_info() -> str:
    """
    Return a human-readable string summarizing current Sun ephemeris at OVRO.
    """
    ephm = _get_ephm_all()
    return ephm["info"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8012)

