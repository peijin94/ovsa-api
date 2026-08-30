import math

import pytest
from fastapi.testclient import TestClient

from api_server import app
from flare_nowcast import load_model, nowcast_from_flux3ch


client = TestClient(app)


def test_nowcast_from_three_channels_returns_all_model_classes():
    model = load_model()
    result = nowcast_from_flux3ch([100.0, 200.0, 300.0], model)

    assert result["frequencies_mhz"] == [40, 60, 80]
    assert result["model_version"] == "v0.1"
    assert result["horizon_min"] == 5.0
    assert math.isclose(result["feature_sfu"], 260.0)
    for class_name in (">M1", ">M5", ">X1"):
        assert 0.0 <= result[class_name]["probability"] <= 1.0
        assert result[class_name]["p_low"] <= result[class_name]["p_high"]
        assert result[class_name]["n_total"] > 0


def test_out_of_model_range_flux_returns_json_null_probabilities():
    response = client.post("/flare/nowcast", json={"flux3ch": [0, 0, 0]})

    assert response.status_code == 200
    result = response.json()
    assert result["feature_sfu"] is None
    assert result[">M1"] is None
    assert result[">M5"] is None
    assert result[">X1"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"flux3ch": [1, 2]},
        {"flux3ch": [1, 2, 3, 4]},
        {"flux3ch": [1, "not-a-number", 3]},
    ],
)
def test_endpoint_rejects_invalid_flux_arrays(payload):
    response = client.post("/flare/nowcast", json=payload)

    assert response.status_code == 422
