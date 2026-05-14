from __future__ import annotations

from math import acos, sin, sqrt

from elek_mcp_demo.domain.models import VoltageDropInput, VoltageDropResult


FORMULA = "V_drop = sqrt(3) * I * L_km * (R cos(phi) + X sin(phi))"


def calculate_voltage_drop(input_data: VoltageDropInput) -> VoltageDropResult:
    """Calculate a simplified balanced three-phase voltage drop."""
    length_km = input_data.length_m / 1000
    cos_phi = input_data.power_factor
    phi = acos(cos_phi)
    sin_phi = sin(phi)

    impedance_term = (
        input_data.resistance_ohm_per_km * cos_phi
        + input_data.reactance_ohm_per_km * sin_phi
    )
    voltage_drop_v = sqrt(3) * input_data.current_a * length_km * impedance_term
    voltage_drop_percent = voltage_drop_v / input_data.line_voltage_v * 100

    return VoltageDropResult(
        voltage_drop_v=round(voltage_drop_v, 4),
        voltage_drop_percent=round(voltage_drop_percent, 4),
        threshold_percent=input_data.threshold_percent,
        is_within_threshold=voltage_drop_percent <= input_data.threshold_percent,
        formula=FORMULA,
        inputs=input_data,
    )
