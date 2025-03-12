"""
Weight calculation module for aircraft operations.

This module handles detailed weight calculations for aircraft including weight and balance,
payload distribution, and other weight-related optimizations for the fuel and cargo system.
"""
from typing import Dict, Any, Optional, List

from src.models.aircraft import Aircraft


def calculate_payload_distribution(
    aircraft: Aircraft,
    pax_count: int,
    cargo_weight: float,
    pax_distribution: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate the distribution of payload throughout the aircraft.
    
    Args:
        aircraft: Aircraft instance
        pax_count: Number of passengers
        cargo_weight: Weight of cargo in kg
        pax_distribution: Optional distribution of passengers (e.g. {'forward': 0.4, 'mid': 0.4, 'aft': 0.2})
    
    Returns:
        Dict[str, float]: Detailed payload distribution by zones
    """
    # Default passenger distribution if not provided
    if pax_distribution is None:
        pax_distribution = {'forward': 0.3, 'mid': 0.5, 'aft': 0.2}
    
    # Calculate passenger weight distribution
    total_pax_weight = pax_count * aircraft.std_pax_weight
    pax_weight_by_zone = {
        zone: total_pax_weight * ratio
        for zone, ratio in pax_distribution.items()
    }
    
    # Simplified cargo distribution (could be expanded based on aircraft specifics)
    cargo_distribution = {'forward_cargo': 0.4, 'aft_cargo': 0.6}
    cargo_weight_by_zone = {
        zone: cargo_weight * ratio
        for zone, ratio in cargo_distribution.items()
    }
    
    # Combine passenger and cargo distributions
    weight_distribution = {
        **pax_weight_by_zone,
        **cargo_weight_by_zone,
        'total_pax_weight': total_pax_weight,
        'total_cargo_weight': cargo_weight,
        'total_payload': total_pax_weight + cargo_weight
    }
    
    return weight_distribution


def calculate_weight_and_balance(
    aircraft: Aircraft,
    pax_count: int,
    cargo_weight: float,
    fuel_weight: float,
    pax_distribution: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate weight and balance metrics for the aircraft.
    
    Args:
        aircraft: Aircraft instance
        pax_count: Number of passengers
        cargo_weight: Weight of cargo in kg
        fuel_weight: Weight of fuel in kg
        pax_distribution: Optional distribution of passengers
    
    Returns:
        Dict[str, Any]: Weight and balance metrics
    """
    # Calculate payload distribution
    payload_distribution = calculate_payload_distribution(
        aircraft, pax_count, cargo_weight, pax_distribution
    )
    
    # Calculate key weights
    dom = aircraft.dom
    zfm = aircraft.calculate_zfm(pax_count, cargo_weight)
    tom = zfm + fuel_weight
    
    # Simple weight breakdown
    weight_breakdown = {
        'dom': dom,
        'payload': payload_distribution['total_payload'],
        'zfm': zfm,
        'fuel': fuel_weight,
        'tom': tom
    }
    
    # In a real implementation, this would include center of gravity calculations
    # based on the moment arms of each weight component
    
    return {
        'weight_distribution': payload_distribution,
        'weight_breakdown': weight_breakdown,
        # This is a placeholder for CG calculations which would be specific to aircraft type
        'cg_position': 25.0  # Simplified CG position as % of MAC
    }


def calculate_max_cargo_by_compartment(
    aircraft: Aircraft,
    pax_count: int,
    available_payload: float
) -> Dict[str, float]:
    """
    Calculate maximum cargo weight by compartment.
    
    Args:
        aircraft: Aircraft instance
        pax_count: Number of passengers
        available_payload: Available payload capacity in kg
    
    Returns:
        Dict[str, float]: Maximum cargo by compartment
    """
    # Calculate passenger weight
    pax_weight = pax_count * aircraft.std_pax_weight
    
    # Calculate remaining payload for cargo
    available_cargo = available_payload - pax_weight
    
    # A330-203 cargo compartment capacities (simplified)
    # These would be actual values in a real implementation
    compartment_capacities = {
        'forward_lower_deck': 10000,  # kg, placeholder
        'aft_lower_deck': 15000,      # kg, placeholder
        'bulk_cargo': 2000            # kg, placeholder
    }
    
    # Calculate max cargo by compartment based on structural limits
    max_cargo_by_compartment = {}
    for compartment, capacity in compartment_capacities.items():
        max_cargo_by_compartment[compartment] = min(capacity, available_cargo)
    
    # Add total available cargo
    max_cargo_by_compartment['total_available'] = available_cargo
    
    return max_cargo_by_compartment


def analyze_weight_tradeoffs(
    aircraft: Aircraft,
    pax_count: int,
    route_distance: float,
    available_payload: float,
    steps: int = 10
) -> List[Dict[str, float]]:
    """
    Analyze the tradeoff between cargo weight and fuel weight.
    
    Args:
        aircraft: Aircraft instance
        pax_count: Number of passengers
        route_distance: Distance in nautical miles
        available_payload: Available payload in kg
        steps: Number of points to analyze
    
    Returns:
        List[Dict[str, float]]: List of cargo-fuel tradeoff points
    """
    tradeoffs = []
    
    # Calculate passenger weight
    pax_weight = pax_count * aircraft.std_pax_weight
    
    # Calculate payload available for cargo
    available_for_cargo = available_payload - pax_weight
    
    # Calculate MZFW and DOM
    mzfw = aircraft.mzfw
    dom = aircraft.dom
    
    # Available payload based on MZFW
    mzfw_payload = mzfw - dom
    available_cargo = mzfw_payload - pax_weight
    
    # Analyze tradeoffs at different cargo/fuel ratios
    for i in range(steps + 1):
        ratio = i / steps
        cargo_weight = available_cargo * ratio
        
        # Calculate remaining payload capacity for additional fuel
        remaining_capacity = available_for_cargo - cargo_weight
        
        # Calculate potential additional fuel (excluding required minimum)
        potential_additional_fuel = remaining_capacity
        
        # Additional fuel burn due to cargo weight
        additional_burn = aircraft.calculate_additional_burn(cargo_weight, route_distance)
        
        # Record this tradeoff point
        tradeoffs.append({
            'cargo_ratio': ratio,
            'cargo_weight': cargo_weight,
            'potential_additional_fuel': potential_additional_fuel,
            'additional_burn_due_to_cargo': additional_burn
        })
    
    return tradeoffs


def calculate_weight_limited_payload(
    aircraft: Aircraft,
    pax_count: int,
    route_distance: float,
    min_fuel_required: float
) -> Dict[str, float]:
    """
    Calculate the maximum payload limited by weight constraints.
    
    Args:
        aircraft: Aircraft instance
        pax_count: Number of passengers
        route_distance: Distance in nautical miles
        min_fuel_required: Minimum required fuel in kg
    
    Returns:
        Dict[str, float]: Maximum payload and limiting factors
    """
    # Calculate passenger weight
    pax_weight = pax_count * aircraft.std_pax_weight
    
    # Calculate DOM
    dom = aircraft.dom
    
    # Calculate payload limitations
    mzfw_limit = aircraft.mzfw - dom - pax_weight
    mtow_limit = aircraft.mtow - dom - pax_weight - min_fuel_required
    mlw_limit = aircraft.mlw - dom - pax_weight - (min_fuel_required - min_fuel_required * 0.9)  # Estimate remaining fuel at landing
    
    # Find most restrictive limit
    max_payload = min(mzfw_limit, mtow_limit, mlw_limit)
    
    # Determine limiting factor
    limiting_factor = "Unknown"
    if max_payload == mzfw_limit:
        limiting_factor = "MZFW"
    elif max_payload == mtow_limit:
        limiting_factor = "MTOW"
    elif max_payload == mlw_limit:
        limiting_factor = "MLW"
    
    return {
        'max_payload': max_payload,
        'mzfw_limit': mzfw_limit,
        'mtow_limit': mtow_limit,
        'mlw_limit': mlw_limit,
        'limiting_factor': limiting_factor
    }