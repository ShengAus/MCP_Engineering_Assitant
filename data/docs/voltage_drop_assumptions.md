# Voltage Drop Assumptions

## demo-voltage-drop-formula

For this demonstration, voltage drop is estimated using a simplified balanced three-phase formula:

`V_drop = sqrt(3) * I * L_km * (R cos(phi) + X sin(phi))`

The formula is intended for MCP tool orchestration demonstration only. It does not replace a full engineering design workflow or standards-based assessment.

## demo-default-cable-values

The sample calculation may use these illustrative values when the user does not provide cable impedance data:

- resistance: 0.524 ohm/km
- reactance: 0.08 ohm/km
- power factor: 0.85

These values are mock assumptions for a reproducible demo, not a verified cable catalogue.

## demo-acceptance-threshold

The demo acceptance threshold is 5 percent voltage drop. A result below or equal to this threshold is marked acceptable for the sample workflow. A result above this threshold is marked as requiring review.

This threshold is not a compliance statement.
