# Voltage Drop Demo Report

## User Question

For a 50 m three-phase cable carrying 80 A at 415 V, estimate the voltage drop using the available assumptions, check it against the demo acceptance threshold, and generate a short engineering report.

## Inputs

- `current_a`: 80
- `length_m`: 50
- `line_voltage_v`: 415
- `resistance_ohm_per_km`: 0.524
- `reactance_ohm_per_km`: 0.08
- `power_factor`: 0.85
- `threshold_percent`: 5.0

## Assumptions

- Balanced three-phase load.
- Cable impedance values are mock demo assumptions.
- The acceptance threshold is a demo threshold, not a compliance claim.
- Formula source: voltage_drop_assumptions.md / voltage_drop_assumptions:demo-voltage-drop-formula.

## Retrieved Evidence

- `voltage_drop_assumptions.md` / `voltage_drop_assumptions:demo-acceptance-threshold`: The demo acceptance threshold is 5 percent voltage drop. A result below or equal to this threshold is marked acceptable for the sample workflow. A result above this threshold is marked as requiring review. This threshold is not a compliance statement.
- `cable_selection_checklist.md` / `cable_selection_checklist:required-inputs-before-sizing`: Before selecting a cable size, an engineering workflow should collect at least: - system voltage and phase configuration - design current or load profile - route length - conductor material - installation method - ambient temperature assumptions - grouping...
- `cable_selection_checklist.md` / `cable_selection_checklist:review-steps`: A complete cable selection workflow should review current capacity, voltage drop, short-circuit withstand, protection coordination, installation constraints, and relevant standards. This sample does not perform those checks.

## Calculation Result

- `voltage_drop_v`: 3.3778
- `voltage_drop_percent`: 0.8139
- `threshold_percent`: 5.0
- `is_within_threshold`: True
- `formula`: V_drop = sqrt(3) * I * L_km * (R cos(phi) + X sin(phi))
- `inputs`: {'current_a': 80.0, 'length_m': 50.0, 'line_voltage_v': 415.0, 'resistance_ohm_per_km': 0.524, 'reactance_ohm_per_km': 0.08, 'power_factor': 0.85, 'threshold_percent': 5.0}

## Acceptance Check

The estimated voltage drop is 0.8139%, which is within the 5.0% demo threshold.

## Limitations

- This is a demonstration workflow only and is not certified electrical design software.
- No cable derating, thermal modelling, protection coordination, or standards compliance check is performed.
- The mock documentation is included for MCP orchestration demonstration only.

## Suggested Next Checks

- Confirm cable catalogue impedance values.
- Check installation method and derating factors.
- Review protection coordination and applicable standards with a qualified engineer.

## Tool Trace

- docs_server.search_docs
- docs_server.get_doc_section
- calc_server.calculate_voltage_drop
- report_server.generate_engineering_report
