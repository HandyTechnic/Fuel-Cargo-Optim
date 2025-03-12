"""
Optimization engine for cargo and fuel tankering.

This module implements the core optimization logic using linear programming to find
the optimal balance between cargo load and fuel tankering to maximize profit
while respecting all operational constraints.
"""
from dataclasses import dataclass
from typing import Dict, Optional, List
import copy

import numpy as np
import pulp

from src.models.aircraft import Aircraft
from src.models.economics import Economics
from src.models.route import Route
from src.optimization.constraints import OptimizationConstraints


@dataclass
class OptimizationResult:
    """
    Result of the optimization process.
    
    Attributes:
        optimal_cargo (float): Optimal cargo weight in kg
        optimal_tankering (float): Optimal tankering fuel in kg
        total_fuel (float): Total fuel onboard in kg
        trip_fuel (float): Trip fuel in kg with optimal solution
        total_profit (float): Total profit in USD
        cargo_revenue (float): Revenue from cargo in USD
        fuel_savings (float): Savings from tankering in USD
        additional_burn (float): Additional fuel burn in kg
        tom (float): Take-off mass in kg
        zfm (float): Zero fuel mass in kg
        lm (float): Landing mass in kg
        constraints_violated (bool): Whether any constraints are violated
        violations (Dict[str, float]): Dictionary of constraint violations
        limiting_factor (str): The limiting factor for the solution
        status (str): Status of the optimization process
    """
    optimal_cargo: float
    optimal_tankering: float
    total_fuel: float
    trip_fuel: float
    total_profit: float
    cargo_revenue: float
    fuel_savings: float
    additional_burn: float
    tom: float
    zfm: float
    lm: float
    constraints_violated: bool
    violations: Dict[str, float]
    limiting_factor: str
    status: str


class Optimizer:
    """
    Optimizer for cargo and fuel tankering.
    
    This class implements the optimization logic using linear programming to find
    the optimal balance between cargo load and fuel tankering to maximize profit.
    """
    
    def __init__(
        self,
        aircraft: Aircraft,
        route: Route,
        pax_count: int,
        user_overrides: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the optimizer with aircraft, route, and passenger data.
        
        Args:
            aircraft: Aircraft instance with specifications
            route: Route instance with route information
            pax_count: Number of passengers
            user_overrides: Optional dictionary of user-specified values that override defaults
        """
        self.aircraft = aircraft
        self.route = route
        self.pax_count = pax_count
        self.user_overrides = user_overrides or {}
        
        # Apply any route-specific overrides
        if 'cargo_revenue_rate' in self.user_overrides:
            # Create a copy to avoid modifying the original route
            self.route = copy.deepcopy(route)
            self.route.cargo_revenue_rate = self.user_overrides['cargo_revenue_rate']
        
        # Initialize constraints manager
        self.constraints = OptimizationConstraints(
            aircraft, route, pax_count, self.user_overrides
        )
        
        # Initialize economics calculator
        self.economics = Economics()
        
        # Cache for optimization results
        self.cache = {}
    
    def optimize_linear(self) -> OptimizationResult:
        """
        Perform optimization using linear programming.
        
        This method creates a linear approximation of the problem and solves it
        using the PuLP linear programming solver.
        
        Returns:
            OptimizationResult: Result of the optimization
        """
        # Check if route has fuel price data
        if self.route.fuel_price_origin is None or self.route.fuel_price_dest is None:
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="Missing fuel price data",
                status="ERROR: Missing fuel price data"
            )
        
        # Check if route has cargo revenue rate
        if self.route.cargo_revenue_rate is None:
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="Missing cargo revenue data",
                status="ERROR: Missing cargo revenue data"
            )
        
        # Create the LP problem
        prob = pulp.LpProblem("CargoFuelOptimization", pulp.LpMaximize)
        
        # Calculate max available cargo based on MZFW
        max_cargo = self.constraints.max_cargo_weight()
        
        # Calculate max available extra fuel based on fuel capacity
        min_fuel_req = self.route.total_min_fuel
        max_extra_fuel = min(
            self.aircraft.fuel_capacity - min_fuel_req,
            # Also consider MTOW limitation
            self.aircraft.mtow - self.aircraft.dom - (self.pax_count * self.aircraft.std_pax_weight) - max_cargo - min_fuel_req
        )
        
        # Create decision variables
        cargo = pulp.LpVariable("cargo", lowBound=0, upBound=max_cargo, cat="Continuous")
        extra_fuel = pulp.LpVariable("extra_fuel", lowBound=0, upBound=max_extra_fuel, cat="Continuous")
        
        # Define additional burn factor - this is a linear approximation
        burn_factor = self.aircraft.additional_burn_factor * self.route.distance
        
        # Objective function: maximize profit
        # Profit = Cargo Revenue + Fuel Savings - Extra Burn Cost
        
        # Cargo revenue (USD)
        cargo_revenue = self.route.cargo_revenue_rate * cargo
        
        # Fuel price differential (USD/kg)
        price_diff_per_kg = (self.route.fuel_price_dest - self.route.fuel_price_origin) / self.aircraft.fuel_density
        
        # Fuel savings from tankering (USD)
        # We have to account for the additional burn
        fuel_savings = price_diff_per_kg * (extra_fuel - burn_factor * (cargo + extra_fuel))
        
        # Set objective function
        prob += cargo_revenue + fuel_savings, "Total Profit"
        
        # Define constraints
        
        # 1. MTOW constraint
        total_fuel = min_fuel_req + extra_fuel
        total_weight = self.aircraft.dom + (self.pax_count * self.aircraft.std_pax_weight) + cargo + total_fuel
        prob += total_weight <= self.aircraft.mtow, "MTOW_Constraint"
        
        # 2. MZFW constraint
        zero_fuel_weight = self.aircraft.dom + (self.pax_count * self.aircraft.std_pax_weight) + cargo
        prob += zero_fuel_weight <= self.aircraft.mzfw, "MZFW_Constraint"
        
        # 3. MLW constraint
        # Landing weight = take-off weight - trip fuel
        # Trip fuel includes additional burn due to extra weight
        trip_fuel_base = self.route.min_trip_fuel
        trip_fuel_additional = burn_factor * (cargo + extra_fuel)
        landing_weight = total_weight - (trip_fuel_base + trip_fuel_additional)
        prob += landing_weight <= self.aircraft.mlw, "MLW_Constraint"
        
        # 4. Fuel capacity constraint
        prob += total_fuel <= self.aircraft.fuel_capacity, "Fuel_Capacity_Constraint"
        
        # Solve the problem
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
        
        # Check if solution is optimal
        if pulp.LpStatus[prob.status] != "Optimal":
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="No optimal solution found",
                status=f"ERROR: {pulp.LpStatus[prob.status]}"
            )
        
        # Extract optimal values
        optimal_cargo = cargo.value()
        optimal_tankering = extra_fuel.value()
        
        # Validate the solution
        validation = self.constraints.validate_solution(optimal_cargo, optimal_tankering)
        
        # Calculate actual values for the solution
        trip_fuel_actual = validation["trip_fuel"]
        
        # Calculate economics
        if self.route.cargo_revenue_rate is not None and self.route.fuel_price_origin is not None and self.route.fuel_price_dest is not None:
            # Calculate additional burn for this combo
            additional_burn = self.aircraft.calculate_additional_burn(optimal_cargo + optimal_tankering, self.route.distance)
            
            # Calculate cargo revenue
            cargo_revenue_actual = optimal_cargo * self.route.cargo_revenue_rate
            
            # Calculate fuel savings using the corrected formula from Economics class
            tankering_savings = self.economics.calculate_tankering_savings(
                optimal_tankering,
                self.route.fuel_price_origin,
                self.route.fuel_price_dest,
                self.aircraft.fuel_density,
                additional_burn
            )
            
            # Calculate total profit
            total_profit = cargo_revenue_actual + tankering_savings
        else:
            additional_burn = 0
            total_profit = 0
            cargo_revenue_actual = 0
            tankering_savings = 0
        
        # Determine limiting factor
        limiting_tom, limiting_factor = self.aircraft.get_limiting_tom(
            validation["min_required_fuel"] + optimal_tankering,
            trip_fuel_actual
        )
        
        return OptimizationResult(
            optimal_cargo=optimal_cargo,
            optimal_tankering=optimal_tankering,
            total_fuel=validation["total_fuel"],
            trip_fuel=trip_fuel_actual,
            total_profit=total_profit,
            cargo_revenue=cargo_revenue_actual,
            fuel_savings=tankering_savings,
            additional_burn=burn_factor * (optimal_cargo + optimal_tankering),
            tom=validation["tom"],
            zfm=validation["zfm"],
            lm=validation["lm"],
            constraints_violated=not validation["valid"],
            violations=validation["violations"],
            limiting_factor=limiting_factor,
            status="Optimal solution found"
        )
    
    def optimize_grid_search(self, cargo_steps: int = 20, fuel_steps: int = 20) -> OptimizationResult:
        """
        Perform optimization using grid search.
        
        This method performs a grid search over the feasible region to find
        the optimal solution. This is useful when the problem is non-linear
        or when more accurate results are needed than linear approximation.
        
        Args:
            cargo_steps: Number of steps for cargo weight
            fuel_steps: Number of steps for extra fuel
            
        Returns:
            OptimizationResult: Result of the optimization
        """
        # Check if route has fuel price data
        if self.route.fuel_price_origin is None or self.route.fuel_price_dest is None:
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="Missing fuel price data",
                status="ERROR: Missing fuel price data"
            )
        
        # Check if route has cargo revenue rate
        if self.route.cargo_revenue_rate is None:
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="Missing cargo revenue data",
                status="ERROR: Missing cargo revenue data"
            )
        
        # Calculate max available cargo based on MZFW
        max_cargo = self.constraints.max_cargo_weight()
        
        # Calculate max available extra fuel based on fuel capacity
        min_fuel_req = self.route.total_min_fuel
        max_extra_fuel = min(
            self.aircraft.fuel_capacity - min_fuel_req,
            # Also consider MTOW limitation
            self.aircraft.mtow - self.aircraft.dom - (self.pax_count * self.aircraft.std_pax_weight) - min_fuel_req
        )
        
        # Create grid of cargo and fuel values
        cargo_values = np.linspace(0, max_cargo, cargo_steps)
        fuel_values = np.linspace(0, max_extra_fuel, fuel_steps)
        
        best_solution = None
        best_profit = float('-inf')
        
        # Iterate through grid points
        for cargo_val in cargo_values:
            for fuel_val in fuel_values:
                # Validate this solution
                validation = self.constraints.validate_solution(cargo_val, fuel_val)
                
                # Skip invalid solutions
                if not validation["valid"]:
                    continue
                
                # Calculate profit
                if self.route.cargo_revenue_rate is not None and self.route.fuel_price_origin is not None and self.route.fuel_price_dest is not None:
                    # Calculate additional burn for this combo
                    extra_weight = cargo_val + fuel_val
                    add_burn = self.aircraft.calculate_additional_burn(extra_weight, self.route.distance)
                    
                    econ_calc = self.economics.calculate_total_profit(
                        cargo_val,
                        self.route.cargo_revenue_rate,
                        fuel_val,
                        self.route.fuel_price_origin,
                        self.route.fuel_price_dest,
                        self.aircraft.fuel_density,
                        add_burn
                    )
                    
                    total_profit = econ_calc["total_profit"]
                    
                    # Update best solution if this is better
                    if total_profit > best_profit:
                        best_profit = total_profit
                        
                        # Calculate limiting factor
                        limiting_tom, limiting_factor = self.aircraft.get_limiting_tom(
                            validation["min_required_fuel"] + fuel_val,
                            validation["trip_fuel"]
                        )
                        
                        best_solution = OptimizationResult(
                            optimal_cargo=cargo_val,
                            optimal_tankering=fuel_val,
                            total_fuel=validation["total_fuel"],
                            trip_fuel=validation["trip_fuel"],
                            total_profit=total_profit,
                            cargo_revenue=econ_calc["cargo_revenue"],
                            fuel_savings=econ_calc["tankering_savings"],
                            additional_burn=add_burn,
                            tom=validation["tom"],
                            zfm=validation["zfm"],
                            lm=validation["lm"],
                            constraints_violated=False,
                            violations={},
                            limiting_factor=limiting_factor,
                            status="Optimal solution found"
                        )
        
        # Check if a valid solution was found
        if best_solution is None:
            return OptimizationResult(
                optimal_cargo=0,
                optimal_tankering=0,
                total_fuel=0,
                trip_fuel=0,
                total_profit=0,
                cargo_revenue=0,
                fuel_savings=0,
                additional_burn=0,
                tom=0,
                zfm=0,
                lm=0,
                constraints_violated=False,
                violations={},
                limiting_factor="No feasible solution found",
                status="ERROR: No feasible solution found"
            )
        
        return best_solution
    
    def optimize(self, method: str = "linear") -> OptimizationResult:
        """
        Perform optimization using the specified method.
        
        Args:
            method: Optimization method to use ('linear' or 'grid_search')
            
        Returns:
            OptimizationResult: Result of the optimization
        """
        # Check cache
        if method in self.cache:
            return self.cache[method]
        
        # Perform optimization based on method
        if method == "linear":
            result = self.optimize_linear()
        elif method == "grid_search":
            result = self.optimize_grid_search()
        else:
            raise ValueError(f"Unknown optimization method: {method}")
        
        # Cache result
        self.cache[method] = result
        
        return result
    
    def analyze_tradeoff(self, steps: int = 10) -> List[Dict[str, float]]:
        """
        Analyze the tradeoff between cargo and fuel tankering.
        
        This method examines various combinations of cargo and fuel to
        understand the tradeoff between them in terms of profit.
        
        Args:
            steps: Number of steps to analyze
            
        Returns:
            List[Dict[str, float]]: List of profit points at different combinations
        """
        # Calculate max available cargo based on MZFW
        max_cargo = self.constraints.max_cargo_weight()
        
        # Calculate max available payload
        max_payload = self.aircraft.mzfw - self.aircraft.dom - (self.pax_count * self.aircraft.std_pax_weight)
        
        # Define ratios of cargo to total payload
        ratios = [i / steps for i in range(steps + 1)]
        
        results = []
        for ratio in ratios:
            # Calculate cargo and extra fuel for this ratio
            cargo_val = ratio * max_payload
            fuel_val = (1 - ratio) * max_payload
            
            # Validate solution
            validation = self.constraints.validate_solution(cargo_val, fuel_val)
            
            # Calculate profit if valid
            if validation["valid"]:
                # Calculate additional burn
                extra_weight = cargo_val + fuel_val
                add_burn = self.aircraft.calculate_additional_burn(extra_weight, self.route.distance)
                
                # Calculate economics
                if self.route.cargo_revenue_rate is not None and self.route.fuel_price_origin is not None and self.route.fuel_price_dest is not None:
                    econ_calc = self.economics.calculate_total_profit(
                        cargo_val,
                        self.route.cargo_revenue_rate,
                        fuel_val,
                        self.route.fuel_price_origin,
                        self.route.fuel_price_dest,
                        self.aircraft.fuel_density,
                        add_burn
                    )
                    
                    results.append({
                        "ratio": ratio,
                        "cargo": cargo_val,
                        "extra_fuel": fuel_val,
                        "total_profit": econ_calc["total_profit"],
                        "cargo_revenue": econ_calc["cargo_revenue"],
                        "fuel_savings": econ_calc["tankering_savings"],
                        "additional_burn": add_burn,
                        "valid": True
                    })
                else:
                    results.append({
                        "ratio": ratio,
                        "cargo": cargo_val,
                        "extra_fuel": fuel_val,
                        "total_profit": 0,
                        "cargo_revenue": 0,
                        "fuel_savings": 0,
                        "additional_burn": add_burn,
                        "valid": True
                    })
            else:
                results.append({
                    "ratio": ratio,
                    "cargo": cargo_val,
                    "extra_fuel": fuel_val,
                    "total_profit": float('-inf'),
                    "cargo_revenue": 0,
                    "fuel_savings": 0,
                    "additional_burn": 0,
                    "valid": False,
                    "violations": validation["violations"]
                })
        
        return results
    
    def sensitivity_analysis(
        self,
        parameter: str,
        values: List[float],
        method: str = "linear"
    ) -> Dict[float, OptimizationResult]:
        """
        Perform sensitivity analysis on a parameter.
        
        This method analyzes how changes in a parameter affect the optimal solution.
        
        Args:
            parameter: Parameter to analyze ('fuel_price_origin', 'fuel_price_dest', 'cargo_revenue_rate')
            values: List of values to test
            method: Optimization method to use
            
        Returns:
            Dict[float, OptimizationResult]: Dictionary mapping parameter values to optimization results
        """
        results = {}
        
        # Store original value
        original_value = None
        
        # Iterate through values
        for value in values:
            # Set parameter value
            if parameter == "fuel_price_origin":
                original_value = self.route.fuel_price_origin
                self.route.fuel_price_origin = value
            elif parameter == "fuel_price_dest":
                original_value = self.route.fuel_price_dest
                self.route.fuel_price_dest = value
            elif parameter == "cargo_revenue_rate":
                original_value = self.route.cargo_revenue_rate
                self.route.cargo_revenue_rate = value
            else:
                raise ValueError(f"Unknown parameter: {parameter}")
            
            # Clear cache
            self.cache = {}
            
            # Optimize with new parameter value
            result = self.optimize(method)
            
            # Store result
            results[value] = result
            
            # Restore original value
            if parameter == "fuel_price_origin":
                self.route.fuel_price_origin = original_value
            elif parameter == "fuel_price_dest":
                self.route.fuel_price_dest = original_value
            elif parameter == "cargo_revenue_rate":
                self.route.cargo_revenue_rate = original_value
        
        return results


def optimize_for_route(
    aircraft: Aircraft,
    route: Route,
    pax_count: int,
    user_overrides: Optional[Dict[str, float]] = None,
    method: str = "linear"
) -> OptimizationResult:
    """
    Convenience function to optimize a route.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        pax_count: Number of passengers
        user_overrides: Optional user overrides
        method: Optimization method to use
        
    Returns:
        OptimizationResult: Result of the optimization
    """
    optimizer = Optimizer(aircraft, route, pax_count, user_overrides)
    return optimizer.optimize(method)