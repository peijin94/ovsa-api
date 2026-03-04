## OVSA Ephemeris API

This repository provides a small FastAPI-based service that serves Sun ephemeris information for the **OVRO** site and a simple benchmarking script for the API.

The API is intended to be reachable under a base like:

- **Base URL**: `http://ovsa.njit.edu:8012`
- **API root**: `/api/ephm`

Below, all paths are relative to the base URL.

### Endpoints

- **`GET /api/ephm/el`**
  - **Description**: Returns the current Sun elevation (altitude) in degrees at OVRO.
  - **Response**: Plain text, a floating-point number with 6 decimal places.
    - Example: `37.123456`

- **`GET /api/ephm/az`**
  - **Description**: Returns the current Sun azimuth in degrees at OVRO.
  - **Response**: Plain text, a floating-point number with 6 decimal places.
    - Example: `145.987654`

- **`GET /api/ephm/sunup`**
  - **Description**: Indicates whether the Sun is above the horizon.
  - **Logic**: `1` if Sun altitude \(> 0^\circ\), otherwise `0`.
  - **Response**: Plain text, either `0` or `1`.

- **`GET /api/ephm/info`**
  - **Description**: Returns a single human-readable summary string of current Sun ephemeris values at OVRO.
  - **Response**: Plain text string containing:
    - Current UTC time (`time=...`)
    - Sun altitude and azimuth in degrees (`alt=...deg az=...deg`)
    - Sun-up flag (`sunup=0` or `1`)
    - Sunrise time (`sunrise=...`)
    - Sunset time (`sunset=...`)
  - **Example**:
    - `time=2026-03-04T12:34:56+00:00 alt=37.12deg az=145.98deg sunup=1 sunrise=2026-03-04T06:25:00+00:00 sunset=2026-03-04T18:05:00+00:00`

### Caching behavior

- **Update cadence**:
  - All endpoints share a common in-memory ephemeris calculation.
  - The full Sun ephemeris is recomputed at most **once per second**.
  - Subsequent requests within that 1-second window read from the cached values.

### Running the API server

- **Development run**:
  ```bash
  pip install fastapi uvicorn ephem pytz
  python api_server.py
  ```
  - The server listens on `0.0.0.0:8012`.

### Benchmarking the API

- **Script**: `benchmark.py`
- **Usage**:
  ```bash
  pip install requests
  python benchmark.py --base-url http://localhost:8012 --iterations 100
  ```
  - Benchmarks:
    - `/api/ephm/el`
    - `/api/ephm/az`
    - `/api/ephm/sunup`
    - `/api/ephm/info`
  - Reports latency statistics (**avg**, **p50**, **p95**, **min**, **max**) in milliseconds for each endpoint.

