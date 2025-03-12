# Mathematical Model for Cargo and Fuel Tankering Optimization

## Decision Variables
- x: Amount of extra fuel to tanker (kg)
- y: Amount of cargo to carry (kg)

## Parameters
- MTOW: Maximum Take-Off Weight (kg)
- MLW: Maximum Landing Weight (kg)
- MZFW: Maximum Zero Fuel Weight (kg)
- OEW: Operating Empty Weight (kg)
- Pax_weight: Total passenger weight (kg)
- Min_trip_fuel: Minimum trip fuel without tankering (kg)
- Contingency_pct: Contingency fuel percentage (typically 5%)
- Reserve_fuel: Final reserve fuel (kg)
- Alternate_fuel: Fuel required to reach alternate airport (kg)
- P_o: Fuel price at origin (USD/liter)
- P_d: Fuel price at destination (USD/liter)
- R_c: Cargo revenue rate (USD/kg)
- ρ: Fuel density (kg/liter)
- D: Distance (nm)
- α: Additional fuel burn factor (kg/kg/nm)

## Fuel Components
1. Trip Fuel: Fuel consumed during the flight from origin to destination
2. Contingency Fuel: Safety margin (typically 5% of trip fuel)
3. Alternate Fuel: Fuel required to reach the alternate airport
4. Final Reserve: Minimum fuel required at destination (typically 30 min holding)

## Total Required Fuel
Min_required_fuel = Min_trip_fuel + Contingency_fuel + Alternate_fuel + Reserve_fuel

Where:
- Contingency_fuel = Min_trip_fuel × Contingency_pct

## Fuel Burn Model
The additional fuel burn due to extra weight (cargo + tankering fuel) can be modeled as:

Additional_burn(extra_weight) = α × extra_weight × D

Where:
- α is the additional burn factor (derived from operational data)
- D is the distance in nautical miles

This affects:
- Trip fuel directly
- Contingency fuel indirectly (as it's a percentage of trip fuel)

## Total Trip Fuel with Extra Weight
Trip_fuel(extra_weight) = Min_trip_fuel + Additional_burn(extra_weight)
                       = Min_trip_fuel + α × extra_weight × D

## Objective Function
Maximize Total Profit = Cargo Revenue + Fuel Cost Savings - Extra Burn Cost

Where:
- Cargo Revenue = R_c × y
- Fuel Cost Savings = (P_d - P_o) × (x - Additional_burn(x+y)) / ρ
- Extra Burn Cost = Additional_burn(x+y) × P_o / ρ

## Constraints
1. Take-Off Weight Constraint:
   OEW + Pax_weight + y + Min_required_fuel + x ≤ MTOW

2. Zero Fuel Weight Constraint:
   OEW + Pax_weight + y ≤ MZFW

3. Landing Weight Constraint:
   OEW + Pax_weight + y + (Min_required_fuel + x - Trip_fuel(x+y)) ≤ MLW

4. Fuel Capacity Constraint:
   Min_required_fuel + x ≤ Maximum Fuel Capacity

5. Non-negativity:
   x, y ≥ 0

## Iterative Solution Approach
Since trip fuel and contingency fuel depend on the extra weight carried (which includes both tankering fuel and cargo), we need an iterative approach:
1. Start with estimated extra fuel burn = 0
2. Calculate the total trip fuel and required fuel
3. Optimize cargo and tankering fuel
4. Recalculate the extra fuel burn, trip fuel, and contingency
5. Repeat until convergence

## Adaptability for Different Routes
This model is designed to work for any route with the following route-specific parameters:
- Distance
- Minimum trip fuel
- Alternate fuel
- Fuel prices at origin and destination
- Cargo revenue rate

The additional burn factor (α) may be calibrated based on available data for specific aircraft types and routes, but a general value can be derived from operational studies like the TFU study.