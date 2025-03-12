# Optimization Framework for Cargo and Fuel Tankering

## Weight Definitions and Relationships
- OWE: Basic Empty Mass (aircraft structure, engines, etc.)
- Variable Load: Crew, catering, water, etc.
- DOM: Dry Operating Mass = OWE + Variable Load
- Traffic Load: Passengers + Cargo
- ZFM: Zero Fuel Mass = DOM + Traffic Load
- TOF: Take-off Fuel = Trip Fuel + Contingency + Alternate + Reserve + Extra Fuel
- TOM: Take-off Mass = ZFM + TOF
- LM: Landing Mass = TOM - Trip Fuel

## Decision Variables
- cargo: Amount of cargo to carry (kg)
- extra_fuel: Amount of extra fuel to tanker (kg)

## Key Parameters
- DOM: Dry Operating Mass (kg)
- PAX_weight: Total passenger weight (kg)
- min_trip_fuel: Minimum trip fuel without extra weight (kg)
- contingency_pct: Contingency fuel percentage (typically 5%)
- alternate_fuel: Fuel required to reach alternate airport (kg)
- reserve_fuel: Final reserve fuel (kg)
- MTOW: Maximum Take-Off Weight (kg)
- MLW: Maximum Landing Weight (kg)
- MZFW: Maximum Zero Fuel Weight (kg)
- FUEL_CAPACITY: Maximum fuel capacity (kg)
- PRICE_ORIGIN: Fuel price at origin (per liter)
- PRICE_DEST: Fuel price at destination (per liter)
- FUEL_DENSITY: Conversion factor kg to liters
- CARGO_REVENUE: Revenue per kg of cargo
- add_burn_factor: Additional fuel burn factor (kg/kg/nm)
- distance: Flight distance (nm)

## Comprehensive Fuel Components
1. **Trip Fuel**:
   - Base trip fuel based on standard flight conditions
   - Adjusted for extra weight and mission profile
   - Includes wind, altitude, and performance corrections

2. **Contingency Fuel**:
   - Percentage of trip fuel (typically 5-10%)
   - Covers unexpected route changes, wind variations
   - Dynamically calculated based on current trip fuel

3. **Alternate Fuel**:
   - Fuel required to reach the alternate airport
   - Accounts for approach, landing, and potential go-around
   - Based on alternate airport distance and aircraft performance

4. **Reserve Fuel**:
   - Minimum fuel required at destination
   - Typically 30 minutes holding at standard conditions
   - Ensures safe landing with sufficient margin

## Detailed Fuel Calculation Methodology
```
# Base Calculations
min_trip_fuel = baseline_fuel_estimate(route_profile)
extra_weight = cargo + extra_fuel

# Performance-Adjusted Trip Fuel
trip_fuel = min_trip_fuel * (1 + performance_factor(extra_weight, distance))
           + add_burn_factor * extra_weight * distance

# Contingency Calculation
contingency_fuel = trip_fuel * contingency_pct

# Total Required Fuel Compilation
total_required_fuel = trip_fuel
                      + contingency_fuel
                      + alternate_fuel
                      + reserve_fuel
```

## Take-off Weight Limiting Factors
TOM is constrained by the most restrictive of:
1. Maximum structural take-off weight (MTOW)
2. Maximum zero fuel weight plus total required fuel
3. Maximum landing weight plus trip fuel

```
limiting_TOM = min(
    MTOW,
    MZFW + total_required_fuel + extra_fuel,
    MLW + trip_fuel
)
```

## Economic Optimization Objective
**Maximize Profit = Cargo Revenue + Fuel Cost Savings - Extra Burn Cost**

Detailed Components:
- Cargo Revenue: `CARGO_REVENUE × cargo`
- Fuel Cost Savings: `(PRICE_DEST - PRICE_ORIGIN) × (extra_fuel - additional_burn) / FUEL_DENSITY`
- Extra Burn Cost: `Additional fuel consumed × PRICE_ORIGIN / FUEL_DENSITY`

## Advanced Constraints

1. **Take-off Weight Constraint**:
   `DOM + PAX_weight + cargo + total_required_fuel + extra_fuel ≤ limiting_TOM`

2. **Zero Fuel Weight Constraint**:
   `DOM + PAX_weight + cargo ≤ MZFW`

3. **Landing Weight Constraint**:
   `DOM + PAX_weight + cargo + (total_required_fuel + extra_fuel - trip_fuel) ≤ MLW`

4. **Fuel Capacity Constraint**:
   `total_required_fuel + extra_fuel ≤ FUEL_CAPACITY`

5. **Non-negativity Constraints**:
   `cargo, extra_fuel ≥ 0`

## Flexible User Overrides
Supports custom inputs for:
- Regulated MTOW
- Regulated MLW
- Actual Zero Fuel Weight
- Block Fuel
- Taxi Fuel

## Iterative Convergence Algorithm
```
while not converged:
    1. Calculate baseline trip_fuel
    2. Estimate total_required_fuel
    3. Determine limiting_TOM
    4. Optimize cargo and extra_fuel
    5. Recalculate trip_fuel with new weights
    6. Update contingency_fuel
    7. Check convergence criteria
```

## Route and Aircraft Adaptability
Framework designed for flexible application across:
- Different aircraft types
- Varying route profiles
- Diverse operational constraints

Customizable parameters include:
- Distance calculations
- Minimum trip fuel estimates
- Alternate fuel requirements
- Local fuel pricing
- Cargo economic models

## Performance Modeling Considerations
- Empirical data integration
- Machine learning predictive models
- Physics-based performance calculations
- Historical operational data analysis

## Conclusion
A dynamic, adaptable optimization framework for intelligent fuel and cargo management, balancing operational efficiency, economic benefits, and safety margins.