"""
Fuel calculation module for aircraft operations.

This module provides functions for calculating various components of fuel requirements,
including trip fuel, contingency fuel, reserves, and additional burn due to extra weight.
It supports the optimization process by providing accurate fuel consumption estimates.
"""
from typing import Dict, Any, Optional, Tuple
from src.models.aircraft import Aircraft
from src.models.route import Route


def calculate_trip_fuel(
    aircraft: Aircraft,
    route: Route,
    extra_weight: float = 0.0
) -> float:
    """
    Calculate trip fuel required for a route, accounting for extra weight.
    
    Args:
        aircraft: Aircraft instance with specifications
        route: Route instance with distance and baseline fuel requirements
        extra_weight: Extra weight being carried (cargo + tankering fuel) in kg
    
    Returns:
        float: Trip fuel required in kg
    """
    # Base trip fuel from the route
    base_trip_fuel = route.min_trip_fuel
    
    # Calculate additional burn due to extra weight
    additional_burn = aircraft.calculate_additional_burn(extra_weight, route.distance)
    
    # Total trip fuel is base plus additional burn
    return base_trip_fuel + additional_burn


def calculate_contingency_fuel(trip_fuel: float, contingency_pct: float = 0.05) -> float:
    """
    Calculate contingency fuel based on trip fuel.
    
    Args:
        trip_fuel: Trip fuel in kg
        contingency_pct: Contingency percentage (default 5%)
    
    Returns:
        float: Contingency fuel in kg
    """
    return trip_fuel * contingency_pct


def calculate_alternate_fuel(route: Route, extra_weight: float = 0.0) -> float:
    """
    Calculate fuel required to reach alternate airport.
    
    Args:
        route: Route instance with alternate airport information
        extra_weight: Extra weight carried in kg
    
    Returns:
        float: Alternate fuel in kg
    """
    # If route has a specific alternate fuel calculation, use it
    # Otherwise return a default value or 0
    # This would need to be enhanced with actual alternate fuel calculation
    # based on the alternate distance and aircraft performance
    return getattr(route, 'alternate_fuel', 0.0)


def calculate_reserve_fuel(route: Route) -> float:
    """
    Calculate final reserve fuel.
    
    Args:
        route: Route instance with reserve requirements
    
    Returns:
        float: Reserve fuel in kg
    """
    # Final reserve is typically a fixed value depending on regulations
    # Usually equivalent to 30 minutes holding time
    return route.reserve_fuel


def calculate_total_fuel_requirement(
    aircraft: Aircraft,
    route: Route,
    extra_weight: float = 0.0,
) -> Dict[str, float]:
    """
    Calculate total fuel requirement with breakdown of components.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        extra_weight: Extra weight in kg (cargo + tankering fuel)
    
    Returns:
        Dict[str, float]: Dictionary with all fuel components in kg
    """
    # Trip fuel calculation
    trip_fuel = calculate_trip_fuel(aircraft, route, extra_weight)
    
    # Contingency fuel
    contingency_fuel = calculate_contingency_fuel(trip_fuel, route.contingency_fuel_pct)
    
    # Alternate fuel (if applicable)
    alternate_fuel = calculate_alternate_fuel(route, extra_weight)
    
    # Reserve fuel
    reserve_fuel = calculate_reserve_fuel(route)
    
    # Total minimum fuel required
    min_required_fuel = trip_fuel + contingency_fuel + alternate_fuel + reserve_fuel
    
    return {
        "trip_fuel": trip_fuel,
        "contingency_fuel": contingency_fuel,
        "alternate_fuel": alternate_fuel,
        "reserve_fuel": reserve_fuel,
        "min_required_fuel": min_required_fuel
    }


def calculate_fuel_weight_impact(
    aircraft: Aircraft,
    route: Route,
    cargo_weight: float,
    tankering_fuel: float
) -> Dict[str, float]:
    """
    Calculate complete fuel requirements accounting for both cargo and tankering.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        cargo_weight: Weight of cargo in kg
        tankering_fuel: Extra fuel for tankering in kg
    
    Returns:
        Dict[str, float]: Complete fuel breakdown and impact assessment
    """
    # Calculate the extra weight being carried
    extra_weight = cargo_weight + tankering_fuel
    
    # First iteration - get initial fuel requirements
    fuel_reqs = calculate_total_fuel_requirement(aircraft, route, extra_weight)
    
    # For more accurate results, we should iteratively recalculate since the
    # extra fuel affects the burn which affects the required contingency
    # which affects the total fuel... etc.
    
    # For simplicity, we'll do just one more iteration
    # This could be extended to continue until convergence
    trip_fuel = fuel_reqs["trip_fuel"]
    min_required_fuel = fuel_reqs["min_required_fuel"]
    
    # Calculate the additional burn specifically due to tankering
    additional_burn_tankering = aircraft.calculate_additional_burn(tankering_fuel, route.distance)
    
    # Calculate effective tankered fuel (accounting for additional burn)
    effective_tankered_fuel = tankering_fuel - additional_burn_tankering
    
    return {
        **fuel_reqs,
        "total_fuel": min_required_fuel + tankering_fuel,
        "additional_burn_tankering": additional_burn_tankering,
        "effective_tankered_fuel": effective_tankered_fuel
    }


def calculate_tankering_efficiency(
    aircraft: Aircraft,
    route: Route,
    tankering_fuel: float
) -> Dict[str, float]:
    """
    Calculate the efficiency of tankering fuel.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        tankering_fuel: Amount of extra fuel for tankering in kg
    
    Returns:
        Dict[str, float]: Tankering efficiency metrics
    """
    if tankering_fuel <= 0:
        return {
            "tankering_fuel": 0,
            "additional_burn": 0,
            "effective_tankered_fuel": 0,
            "tankering_efficiency_pct": 0,
            "cost_at_origin": 0,
            "savings_at_dest": 0,
            "net_savings": 0
        }

    # Calculate additional burn due to tankering considering route distance
    additional_burn = aircraft.calculate_additional_burn(tankering_fuel, route.distance)
    
    # Calculate effective tankered fuel (what actually arrives at destination)
    effective_tankered_fuel = max(0, tankering_fuel - additional_burn)
    
    # Calculate tankering efficiency as percentage
    efficiency = (effective_tankered_fuel / tankering_fuel * 100)
    
    # Calculate cost savings if price information is available
    if route.fuel_price_origin is not None and route.fuel_price_dest is not None:
        # Convert kg to liters using aircraft's fuel density
        effective_tankered_liters = effective_tankered_fuel / aircraft.fuel_density
        tankering_liters = tankering_fuel / aircraft.fuel_density
        
        # Calculate costs considering both uplift and savings
        cost_at_origin = tankering_liters * route.fuel_price_origin
        savings_at_dest = effective_tankered_liters * route.fuel_price_dest
        
        # Calculate net savings (can be negative if tankering is not profitable)
        net_savings = savings_at_dest - cost_at_origin
    else:
        cost_at_origin = 0
        savings_at_dest = 0
        net_savings = 0
    
    return {
        "tankering_fuel": tankering_fuel,
        "additional_burn": additional_burn,
        "effective_tankered_fuel": effective_tankered_fuel,
        "tankering_efficiency_pct": efficiency,
        "cost_at_origin": cost_at_origin,
        "savings_at_dest": savings_at_dest,
        "net_savings": net_savings
    }


def analyze_fuel_tankering(
    aircraft: Aircraft,
    route: Route,
    tankering_fuel_options: list
) -> Dict[str, Any]:
    """
    Analyze multiple tankering options to find the most profitable.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        tankering_fuel_options: List of tankering fuel amounts to analyze
    
    Returns:
        Dict[str, Any]: Analysis of all tankering options with the optimal choice
    """
    results = []
    best_option = {"net_savings": 0, "tankering_fuel": 0}
    
    for fuel_amount in tankering_fuel_options:
        efficiency = calculate_tankering_efficiency(aircraft, route, fuel_amount)
        results.append(efficiency)
        
        # Track the most profitable option
        if efficiency["net_savings"] > best_option["net_savings"]:
            best_option = efficiency
    
    return {
        "all_options": results,
        "best_option": best_option
    }


def calculate_tankering_factor(
    price_origin: float,
    price_destination: float,
    route_distance: float,
    aircraft_burn_factor: float
) -> float:
    """
    Calculate the tankering factor for quick decision making.
    A factor > 1.0 indicates tankering may be beneficial.
    
    Args:
        price_origin: Fuel price at origin in price per liter
        price_destination: Fuel price at destination in price per liter
        route_distance: Distance in nautical miles
        aircraft_burn_factor: Aircraft's additional burn factor
    
    Returns:
        float: Tankering factor
    """
    # Basic price ratio
    price_ratio = price_destination / price_origin
    
    # The final tankering factor combines price ratio and efficiency impact
    return price_ratio


def examine_fuel_weight_tradeoff(
    aircraft: Aircraft,
    route: Route,
    available_payload: float
) -> Dict[str, Any]:
    """
    Examine the tradeoff between carrying extra fuel vs cargo.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        available_payload: Available payload capacity in kg
    
    Returns:
        Dict[str, Any]: Analysis of fuel vs cargo weight tradeoff
    """
    # Define sampling points for the tradeoff curve
    fuel_ratios = [i/10 for i in range(11)]  # 0%, 10%, 20%, ... 100%
    
    tradeoff_points = []
    for ratio in fuel_ratios:
        # Allocate weight between fuel and cargo
        tankering_fuel = ratio * available_payload
        cargo_weight = (1 - ratio) * available_payload
        
        # Calculate economics
        tankering_analysis = calculate_tankering_efficiency(
            aircraft, route, tankering_fuel
        )
        
        # Calculate cargo revenue
        if route.cargo_revenue_rate is not None:
            cargo_revenue = cargo_weight * route.cargo_revenue_rate
        else:
            cargo_revenue = 0
        
        # Calculate total profit
        total_profit = tankering_analysis["net_savings"] + cargo_revenue
        
        tradeoff_points.append({
            "tankering_fuel": tankering_fuel,
            "cargo_weight": cargo_weight,
            "fuel_savings": tankering_analysis["net_savings"],
            "cargo_revenue": cargo_revenue,
            "total_profit": total_profit
        })
    
    # Find the most profitable point
    best_point = max(tradeoff_points, key=lambda x: x["total_profit"])
    
    return {
        "tradeoff_curve": tradeoff_points,
        "optimal_point": best_point
    }