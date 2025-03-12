"""
Constraints module for the fuel and cargo optimization problem.

This module defines all weight and operational constraints that must be satisfied
during the optimization process. The constraint functions are designed to work with
optimization libraries like PuLP or SciPy.
"""
from typing import Dict, Any, Optional, Callable, Tuple
from src.models.aircraft import Aircraft
from src.models.route import Route


def generate_constraint_functions() -> Dict[str, Callable]:
    """
    Generate constraint functions compatible with optimization libraries.

    Returns:
        Dict[str, Callable]: Dictionary of constraint functions
    """
    # This would be implemented according to the specific optimization library being used
    # For example, for PuLP, this would return LpConstraint objects

    # Placeholder for future implementation
    return {}


class OptimizationConstraints:
    """
    Class that handles all constraints for the fuel and cargo optimization problem.
    
    This class can generate constraint functions compatible with optimization libraries
    and validates whether a proposed solution meets all operational requirements.
    """
    
    def __init__(
        self,
        aircraft: Aircraft,
        route: Route,
        pax_count: int,
        user_overrides: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the constraints manager with aircraft, route, and passenger data.
        
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
        
        # Initialize constraint violations tracking
        self.violations = {}
        
        # Calculate passenger weight
        self.pax_weight = self.pax_count * self.aircraft.std_pax_weight
    
    @property
    def mtow(self) -> float:
        """Get MTOW, potentially overridden by user input."""
        return self.user_overrides.get('regulated_mtow', self.aircraft.mtow)
    
    @property
    def mlw(self) -> float:
        """Get MLW, potentially overridden by user input."""
        return self.user_overrides.get('regulated_mlw', self.aircraft.mlw)
    
    @property
    def actual_zfw(self) -> Optional[float]:
        """Get user-specified ZFW if provided."""
        return self.user_overrides.get('actual_zfw', None)
    
    @property
    def block_fuel(self) -> Optional[float]:
        """Get user-specified block fuel if provided."""
        return self.user_overrides.get('block_fuel', None)
    
    @property
    def taxi_fuel(self) -> Optional[float]:
        """Get user-specified taxi fuel if provided."""
        return self.user_overrides.get('taxi_fuel', None)
    
    def max_cargo_weight(self) -> float:
        """
        Calculate maximum cargo weight based on MZFW constraint.
        
        Returns:
            float: Maximum cargo weight in kg
        """
        if self.actual_zfw is not None:
            # User has specified ZFW directly
            max_cargo = float(self.actual_zfw) - float(self.aircraft.dom) - float(self.pax_weight)
        else:
            # Calculate based on aircraft MZFW
            max_cargo = float(self.aircraft.mzfw) - float(self.aircraft.dom) - float(self.pax_weight)
        
        # Ensure max_cargo is not negative and is a float
        return max(0.0, max_cargo)
    
    def max_fuel_capacity(self) -> float:
        """
        Get maximum fuel capacity, taking into account user overrides.
        
        Returns:
            float: Maximum fuel capacity in kg
        """
        if self.block_fuel is not None:
            return self.block_fuel
        return self.aircraft.fuel_capacity
    
    def calc_trip_fuel(self, extra_weight: float = 0) -> float:
        """
        Calculate trip fuel based on route and potential extra weight.
        
        Args:
            extra_weight: Combined weight of extra cargo and tankering fuel in kg
            
        Returns:
            float: Trip fuel in kg
        """
        # Base trip fuel from the route
        base_trip_fuel = self.route.min_trip_fuel
        
        # Additional burn due to extra weight
        additional_burn = getattr(self.aircraft, 'additional_burn_factor', 0.0) * extra_weight * self.route.distance
        
        return base_trip_fuel + additional_burn
    
    def calc_total_min_fuel(self, trip_fuel: float) -> float:
        """
        Calculate total minimum fuel required (trip + contingency + reserve).
        
        Args:
            trip_fuel: Trip fuel in kg
            
        Returns:
            float: Total minimum fuel required in kg
        """
        contingency = trip_fuel * self.route.contingency_fuel_pct
        return trip_fuel + contingency + self.route.reserve_fuel
    
    def check_mtow_constraint(self, cargo: float, total_fuel: float) -> Tuple[bool, float]:
        """
        Check MTOW constraint.
        
        Args:
            cargo: Cargo weight in kg
            total_fuel: Total fuel onboard in kg
            
        Returns:
            Tuple[bool, float]: (constraint satisfied, violation amount)
        """
        tom = self.aircraft.calculate_tom(self.pax_count, cargo, total_fuel)
        violation = tom - self.mtow
        return violation <= 0, violation
    
    def check_mlw_constraint(self, cargo: float, total_fuel: float, trip_fuel: float) -> Tuple[bool, float]:
        """
        Check MLW constraint.
        
        Args:
            cargo: Cargo weight in kg
            total_fuel: Total fuel onboard in kg
            trip_fuel: Trip fuel in kg
            
        Returns:
            Tuple[bool, float]: (constraint satisfied, violation amount)
        """
        landing_mass = self.aircraft.calculate_tom(self.pax_count, cargo, total_fuel) - trip_fuel
        violation = landing_mass - self.mlw
        return violation <= 0, violation
    
    def check_mzfw_constraint(self, cargo: float) -> Tuple[bool, float]:
        """
        Check MZFW constraint.
        
        Args:
            cargo: Cargo weight in kg
            
        Returns:
            Tuple[bool, float]: (constraint satisfied, violation amount)
        """
        zfm = self.aircraft.calculate_zfm(self.pax_count, cargo)
        violation = zfm - self.aircraft.mzfw
        return violation <= 0, violation
    
    def check_fuel_capacity_constraint(self, total_fuel: float) -> Tuple[bool, float]:
        """
        Check fuel capacity constraint.
        
        Args:
            total_fuel: Total fuel onboard in kg
            
        Returns:
            Tuple[bool, float]: (constraint satisfied, violation amount)
        """
        max_capacity = self.max_fuel_capacity()
        violation = total_fuel - max_capacity
        return violation <= 0, violation
    
    def validate_solution(self, cargo: float, extra_fuel: float) -> Dict[str, Any]:
        """
        Validate if a proposed solution meets all constraints.
        
        Args:
            cargo: Cargo weight in kg
            extra_fuel: Extra fuel for tankering in kg
            
        Returns:
            Dict[str, Any]: Dictionary with validation results
        """
        # Calculate trip fuel with extra weight
        extra_weight = cargo + extra_fuel
        trip_fuel = self.calc_trip_fuel(extra_weight)
        
        # Calculate required minimum fuel
        min_required_fuel = self.calc_total_min_fuel(trip_fuel)
        
        # Total fuel onboard
        total_fuel = min_required_fuel + extra_fuel
        
        # Check all constraints
        mtow_ok, mtow_violation = self.check_mtow_constraint(cargo, total_fuel)
        mlw_ok, mlw_violation = self.check_mlw_constraint(cargo, total_fuel, trip_fuel)
        mzfw_ok, mzfw_violation = self.check_mzfw_constraint(cargo)
        fuel_cap_ok, fuel_cap_violation = self.check_fuel_capacity_constraint(total_fuel)
        
        # Store violations
        self.violations = {
            'mtow': mtow_violation if mtow_violation > 0 else 0,
            'mlw': mlw_violation if mlw_violation > 0 else 0,
            'mzfw': mzfw_violation if mzfw_violation > 0 else 0,
            'fuel_capacity': fuel_cap_violation if fuel_cap_violation > 0 else 0
        }
        
        # Overall validity
        valid = mtow_ok and mlw_ok and mzfw_ok and fuel_cap_ok
        
        return {
            'valid': valid,
            'violations': self.violations,
            'trip_fuel': trip_fuel,
            'min_required_fuel': min_required_fuel,
            'total_fuel': total_fuel,
            'tom': self.aircraft.calculate_tom(self.pax_count, cargo, total_fuel),
            'zfm': self.aircraft.calculate_zfm(self.pax_count, cargo),
            'lm': self.aircraft.calculate_tom(self.pax_count, cargo, total_fuel) - trip_fuel
        }
    
    def get_limiting_tom(self, required_fuel: float, trip_fuel: float) -> Tuple[float, str]:
        """
        Get the limiting take-off mass based on all constraints.
        
        Args:
            required_fuel: Total required fuel in kg
            trip_fuel: Trip fuel in kg
            
        Returns:
            Tuple[float, str]: Limiting take-off mass and the limiting factor
        """
        return self.aircraft.get_limiting_tom(required_fuel, trip_fuel)


def validate_weight_distribution(
    aircraft: Aircraft,
    route: Route,
    pax_count: int,
    cargo: float,
    extra_fuel: float,
    user_overrides: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Validate weight distribution for a flight.
    
    Args:
        aircraft: Aircraft instance
        route: Route instance
        pax_count: Number of passengers
        cargo: Cargo weight in kg
        extra_fuel: Extra fuel for tankering in kg
        user_overrides: Optional user overrides
        
    Returns:
        Dict[str, Any]: Validation results
    """
    constraints = OptimizationConstraints(aircraft, route, pax_count, user_overrides)
    return constraints.validate_solution(cargo, extra_fuel)