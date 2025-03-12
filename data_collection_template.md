# Data Collection Template for A330-203 Optimization

## Aircraft Data (A330-203)

### Basic Specifications
| Parameter                       | Value  | Unit   | Source/Notes |
|---------------------------------|--------|--------|--------------|
| Maximum Take-Off Weight (MTOW)  | 233000 | kg     | FCOM LIM     |
| Maximum Landing Weight (MLW)    | 182000 | kg     | FCOM LIM     |
| Maximum Zero Fuel Weight (MZFW) | 170000 | kg     | FCOM LIM     |
| Operating Empty Weight (OEW)    | 120310 | kg     | OWE 28/12/24 |
| Maximum Fuel Capacity           | 109186 | kg     | FCOM DSC     |
| Maximum Fuel Capacity           | 139090 | liters | FCOM DSC     |
| Maximum Structural Payload      | 49717  | kg     | JETPLAN CFP  |

### Performance Data
| Parameter                   | Value    | Unit     | Source/Notes                                       |
|-----------------------------|----------|----------|----------------------------------------------------|
| Fuel Density                | 0.785    | kg/liter | FCOM                                               |
| Additional Fuel Burn Factor | 0.00022  | kg/kg/nm | Based on TFU Study (5,404 kg burn for 23,000 kg extra over 2,662 nm) |

### Passenger Configuration
| Parameter                                | Value | Unit   | Source/Notes                       |
|------------------------------------------|-------|--------|------------------------------------|
| Standard Passenger Count                 | 237   | pax    | Guaranteed capacity (90%)          |
| Standard Passenger Weight (with baggage) | 102   | kg/pax |                                    |
| Total Passenger Weight                   | 24174 | kg     | Calculated: Pax Count × Std Weight |

## Route Data

### MLE-TFU Route (No Extra Fuel)
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    | 2662  | nm    | JETPLAN CFP                              |
| Typical Flight Time         | 6.08  | hours | JETPLAN CFP                              |
| Standard Flight Level       | 380   | FL    | JETPLAN CFP (NIL EXTRA)                  |
| Average Wind Component      | -22   | knots | Negative for headwind                    |
| Minimum Trip Fuel           | 32841 | kg    | Standard flight plan                     |
| Contingency Fuel            | 1642  | kg    | JETPLAN CFP                              |
| Final Reserve Fuel          | 2500  | kg    | OM-A                                     |
| Total Minimum Fuel Required | 42545 | kg    | Calculated: Trip + Contingency + Reserve |

### MLE-PEK Route
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    | 3800  | nm    | Placeholder - needs confirmation         |
| Typical Flight Time         | 8.5   | hours | Placeholder - needs confirmation         |
| Standard Flight Level       | 380   | FL    | Placeholder - needs confirmation         |
| Average Wind Component      | -25   | knots | Negative for headwind                    |
| Minimum Trip Fuel           | 45000 | kg    | Placeholder - needs confirmation         |
| Contingency Fuel            | 2250  | kg    | Calculated: 5% of trip fuel              |
| Reserve Fuel                | 2500  | kg    | Standard value                           |
| Total Minimum Fuel Required | 49750 | kg    | Calculated: Trip + Contingency + Reserve |

### MLE-PVG Route
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    | 4000  | nm    | Placeholder - needs confirmation         |
| Typical Flight Time         | 9.0   | hours | Placeholder - needs confirmation         |
| Standard Flight Level       | 380   | FL    | Placeholder - needs confirmation         |
| Average Wind Component      | -25   | knots | Negative for headwind                    |
| Minimum Trip Fuel           | 47000 | kg    | Placeholder - needs confirmation         |
| Contingency Fuel            | 2350  | kg    | Calculated: 5% of trip fuel              |
| Reserve Fuel                | 2500  | kg    | Standard value                           |
| Total Minimum Fuel Required | 51850 | kg    | Calculated: Trip + Contingency + Reserve |

## Economic Data

### Fuel Prices
| Airport | Price  | Currency/Unit | Date Updated | Source/Notes |
|---------|--------|---------------|--------------|--------------|
| MLE     | 0.9974 | USD/liter     | 21/02/2025   | NASIF        |
| TFU     | 0.6875 | USD/liter     | 21/02/2025   | NASIF        |
| PEK     | 0.6853 | USD/liter     | 21/02/2025   | NASIF        |
| PVG     | 0.5914 | USD/liter     | 21/02/2025   | NASIF        |

### Cargo Revenue
| Route   | Revenue Rate | Currency/Unit | Source/Notes |
|---------|--------------|---------------|--------------|
| MLE-TFU | 2.6          | USD/kg        |              |
| MLE-PEK | 2.6          | USD/kg        |              |
| MLE-PVG | 2.6          | USD/kg        |              |

## Operational Constraints
| Constraint                 | Value | Unit | Source/Notes                |
|----------------------------|-------|------|-----------------------------|
| Minimum Contingency Fuel % | 5     | %    |                             |
| Alternate Fuel             | -     | kg   | If applicable               |
| Final Reserve Fuel         | 2500  | kg   | Typically 30 min holding    |
| Company Fuel Policy Extras | -     | kg   | Any additional requirements |

## TFU Study Results
Based on the TFU Study CSV data, we can see the relationship between extra fuel carried and additional fuel burn:

| Extra Fuel (kg) | Trip Fuel (kg) | Extra Burn (kg) | Burn Rate (kg/kg) |
|-----------------|----------------|-----------------|-------------------|
| 0               | 32841          | 0               | -                 |
| 1000            | 33032          | 215             | 0.215             |
| 5000            | 33913          | 1235            | 0.247             |
| 10000           | 34923          | 2410            | 0.241             |
| 15000           | 35847          | 3489            | 0.233             |
| 20000           | 36803          | 4611            | 0.231             |
| 23000           | 37499          | 5404            | 0.235             |

This gives an average additional burn factor of approximately 0.22 kg of extra fuel burn per kg of extra weight carried, which can be used in our model as a simplification.