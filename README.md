## OVSA API

This repository provides a small FastAPI-based service that serves Sun ephemeris information for the **OVRO** site, an OVRO-LWA flare nowcast, and a simple benchmarking script for the API.

The API is intended to be reachable under bases like:

- **Production**: `http://ovsa.njit.edu/api`
- **Local testing**: `http://localhost:8012`

Below, all paths are relative to these bases and use `/ephm/...`. In production the
reverse proxy typically maps `/api/ephm/...` to the same FastAPI app paths as
`http://localhost:8012/ephm/...`.

### Endpoints

- **`GET /ephm/el`**
  - **Description**: Returns the current Sun elevation (altitude) in degrees at OVRO.
  - **Response**: Plain text, a floating-point number with 6 decimal places.
    - Example: `37.123456`

- **`GET /ephm/az`**
  - **Description**: Returns the current Sun azimuth in degrees at OVRO.
  - **Response**: Plain text, a floating-point number with 6 decimal places.
    - Example: `145.987654`

- **`GET /ephm/sunup`**
  - **Description**: Indicates whether the Sun is above the horizon.
  - **Logic**: `1` if Sun altitude \(> 0^\circ\), otherwise `0`.
  - **Response**: Plain text, either `0` or `1`.

- **`GET /ephm/info`**
  - **Description**: Returns a single human-readable summary string of current Sun ephemeris values at OVRO.
  - **Response**: Plain text string containing:
    - Current UTC time (`time=...`)
    - Sun altitude and azimuth in degrees (`alt=...deg az=...deg`)
    - Sun-up flag (`sunup=0` or `1`)
    - Sunrise time (`sunrise=...`)
    - Sunset time (`sunset=...`)
  - **Example**:
    - `time=2026-03-04T12:34:56+00:00 alt=37.12deg az=145.98deg sunup=1 sunrise=2026-03-04T06:25:00+00:00 sunset=2026-03-04T18:05:00+00:00`

- **`POST /flare/nowcast`**
  - **Description**: Returns the probability that GOES XRS-B reaches `>M1`, `>M5`, or `>X1` within the model's nowcast horizon.
  - **Request**: JSON containing exactly three current flux values in SFU, ordered as 40, 60, and 80 MHz:
    ```json
    {"flux3ch": [100, 200, 300]}
    ```
  - **Response**: JSON with the combined radio feature, model metadata, and each class's empirical probability, 95% Wilson interval, and training-bin sample count:
    ```json
    {
      "feature_sfu": 260.0,
      "horizon_min": 5.0,
      ">M1": {
        "probability": 0.30735175744566673,
        "p_low": 0.2969786648439013,
        "p_high": 0.3179233196659332,
        "n_total": 7454,
        "feature_sfu": 260.0
      },
      ">M5": {
        "probability": 0.07351757445666757,
        "p_low": 0.06780988763473715,
        "p_high": 0.07966463099810696,
        "n_total": 7454,
        "feature_sfu": 260.0
      },
      ">X1": {
        "probability": 0.01998926750737859,
        "p_low": 0.017050310904535508,
        "p_high": 0.02342273963598549,
        "n_total": 7454,
        "feature_sfu": 260.0
      },
      "frequencies_mhz": [40, 60, 80],
      "model_version": "v0.1",
      "created_utc": "2026-08-29T16:56:30+00:00"
    }
    ```
  - Values outside the model's valid SFU range produce `null` for the feature and class results.
  - The exported model uses a trailing 20-second feature window. This endpoint holds each supplied current value constant over that window; callers that have full 1-second rolling buffers can use `flare_nowcast.nowcast` directly.

### Caching behavior

- **Update cadence**:
  - All endpoints share a common in-memory ephemeris calculation.
  - The full Sun ephemeris is recomputed at most **once per second**.
  - Subsequent requests within that 1-second window read from the cached values.

### Running the API server

- **Development run**:
  ```bash
  pip install -r requirements.txt
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
    - `/ephm/el`
    - `/ephm/az`
    - `/ephm/sunup`
    - `/ephm/info`
  - Reports latency statistics (**avg**, **p50**, **p95**, **min**, **max**) in milliseconds for each endpoint.
