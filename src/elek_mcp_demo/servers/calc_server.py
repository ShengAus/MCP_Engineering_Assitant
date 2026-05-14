from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from elek_mcp_demo.domain.calculations import calculate_voltage_drop as calculate
from elek_mcp_demo.domain.models import VoltageDropInput


mcp = FastMCP("engineering-calculations")


@mcp.tool()
def calculate_voltage_drop(
    current_a: float,
    length_m: float,
    line_voltage_v: float,
    resistance_ohm_per_km: float = 0.524,
    reactance_ohm_per_km: float = 0.08,
    power_factor: float = 0.85,
    threshold_percent: float = 5.0,
) -> dict:
    """Estimate simplified balanced three-phase voltage drop."""
    input_data = VoltageDropInput(
        current_a=current_a,
        length_m=length_m,
        line_voltage_v=line_voltage_v,
        resistance_ohm_per_km=resistance_ohm_per_km,
        reactance_ohm_per_km=reactance_ohm_per_km,
        power_factor=power_factor,
        threshold_percent=threshold_percent,
    )
    return calculate(input_data).model_dump()


if __name__ == "__main__":
    mcp.run()
