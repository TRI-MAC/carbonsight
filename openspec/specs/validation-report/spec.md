## ADDED Requirements

### Requirement: Generated validation report
The system SHALL produce a markdown validation report at `docs/validation-report.md` summarizing all validation results.

#### Scenario: Report contains regression results
- **WHEN** the validation report is generated
- **THEN** it SHALL include a table of CarbonSight vs Ekiden v1 Total GHG per year with absolute and percentage differences

#### Scenario: Report contains GREET spot-check results
- **WHEN** the validation report is generated
- **THEN** it SHALL include per-vehicle ICEV and BEV production and usage emissions compared against GREET reference values with citations

#### Scenario: Report contains VISION spot-check results
- **WHEN** the validation report is generated
- **THEN** it SHALL include fleet size and BEV share compared against VISION reference case

#### Scenario: Report includes source citations
- **WHEN** any reference value is listed in the report
- **THEN** it SHALL include the source name, year, and specific table/figure reference where applicable
