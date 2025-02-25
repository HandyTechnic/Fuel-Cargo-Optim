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
| Parameter                   | Value | Unit     | Source/Notes                                       |
|-----------------------------|-------|----------|----------------------------------------------------|
| Fuel Density                | 0.785 | kg/liter | FCOM                                               |
| Additional Fuel Burn Factor |       | kg/kg/nm | Extra fuel burn per kg of additional weight per nm |

### Passenger Configuration
| Parameter                                | Value | Unit   | Source/Notes                       |
|------------------------------------------|-------|--------|------------------------------------|
| Standard Passenger Count                 | 237   | pax    | Guaranteed capacity (90%)          |
| Standard Passenger Weight (with baggage) | 102   | kg/pax |                                    |
| Total Passenger Weight                   | 24174 | kg     | Calculated: Pax Count × Std Weight |

## Route Data

### TFU-MLE Route (No Extra Fuel)
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    | 2662  | nm    | JETPLAN CFP                              |
| Typical Flight Time         | 6.08  | hours | JETPLAN CFP                              |
| Standard Flight Level       | 380   | FL    | JETPLAN CFP (NIL EXTRA)                  |
| Average Wind Component      | -22   | knots | Negative for headwind                    |
| Minimum Trip Fuel           | 32841 | kg    | Standard flight plan                     |
| Contingency Fuel            | 1642  | kg    |                                          |
| Reserve Fuel                | 2500  | kg    |                                          |
| Total Minimum Fuel Required | 42545 | kg    | Calculated: Trip + Contingency + Reserve |

### PEK-MLE Route
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    |       | nm    |                                          |
| Typical Flight Time         |       | hours |                                          |
| Standard Flight Level       |       | FL    |                                          |
| Average Wind Component      |       | knots | Negative for headwind                    |
| Minimum Trip Fuel           |       | kg    | Standard flight plan                     |
| Contingency Fuel            |       | kg    |                                          |
| Reserve Fuel                |       | kg    |                                          |
| Total Minimum Fuel Required |       | kg    | Calculated: Trip + Contingency + Reserve |

### PVG-MLE Route
| Parameter                   | Value | Unit  | Source/Notes                             |
|-----------------------------|-------|-------|------------------------------------------|
| Distance                    |       | nm    |                                          |
| Typical Flight Time         |       | hours |                                          |
| Standard Flight Level       |       | FL    |                                          |
| Average Wind Component      |       | knots | Negative for headwind                    |
| Minimum Trip Fuel           |       | kg    | Standard flight plan                     |
| Contingency Fuel            |       | kg    |                                          |
| Reserve Fuel                |       | kg    |                                          |
| Total Minimum Fuel Required |       | kg    | Calculated: Trip + Contingency + Reserve |

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