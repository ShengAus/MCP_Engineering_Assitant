from pydantic import ValidationError
import pytest

from elek_mcp_demo.domain.calculations import calculate_voltage_drop
from elek_mcp_demo.domain.models import VoltageDropInput


def test_calculate_voltage_drop_demo_values() -> None:
    result = calculate_voltage_drop(
        VoltageDropInput(
            current_a=80,
            length_m=50,
            line_voltage_v=415,
            resistance_ohm_per_km=0.524,
            reactance_ohm_per_km=0.08,
            power_factor=0.85,
            threshold_percent=5.0,
        )
    )

    assert result.voltage_drop_v == pytest.approx(3.3778)
    assert result.voltage_drop_percent == pytest.approx(0.8139)
    assert result.is_within_threshold is True


def test_voltage_drop_rejects_invalid_current() -> None:
    with pytest.raises(ValidationError):
        VoltageDropInput(
            current_a=0,
            length_m=50,
            line_voltage_v=415,
            resistance_ohm_per_km=0.524,
            reactance_ohm_per_km=0.08,
            power_factor=0.85,
        )
