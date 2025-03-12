"""
Route model that defines specifications, distances, and fuel requirements for aircraft routes.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Route:
    """
    Route model containing all relevant route information for fuel and cargo optimization.

    Attributes:
        origin (str): Origin airport IATA code
        destination (str): Destination airport IATA code
        distance (float): Great circle distance in nautical miles
        flight_time (float): Typical flight time in hours
        flight_level (int): Standard flight level
        wind_component (float): Average wind component in knots (negative for headwind)
        min_trip_fuel (float): Minimum trip fuel in kg
        contingency_fuel_pct (float): Contingency fuel percentage (typically 5%)
        reserve_fuel (float): Final reserve fuel in kg
        fuel_price_origin (float): Fuel price at origin airport in USD/liter
        fuel_price_dest (float): Fuel price at destination airport in USD/liter
        cargo_revenue_rate (float): Cargo revenue rate in USD/kg
    """

    origin: str
    destination: str
    distance: float
    flight_time: float
    flight_level: int
    wind_component: float
    min_trip_fuel: float
    contingency_fuel_pct: float = 0.05
    reserve_fuel: float = 2500.0
    fuel_price_origin: Optional[float] = None
    fuel_price_dest: Optional[float] = None
    cargo_revenue_rate: Optional[float] = None

    @property
    def contingency_fuel(self) -> float:
        """
        Calculate the contingency fuel based on the minimum trip fuel and contingency percentage.

        Returns:
            float: Contingency fuel in kg
        """
        return self.min_trip_fuel * self.contingency_fuel_pct

    @property
    def total_min_fuel(self) -> float:
        """
        Calculate the total minimum fuel required for the route.

        Returns:
            float: Total minimum fuel in kg (trip + contingency + reserve)
        """
        return self.min_trip_fuel + self.contingency_fuel + self.reserve_fuel

    @property
    def tankering_factor(self) -> Optional[float]:
        """
        Calculate the tankering factor based on fuel prices.
        A tankering factor > 1 suggests tankering is economically beneficial.

        Returns:
            Optional[float]: Tankering factor or None if prices are not set
        """
        if self.fuel_price_origin is None or self.fuel_price_dest is None:
            return None
        return self.fuel_price_dest / self.fuel_price_origin

    def estimate_add_fuel_burn(self, extra_weight: float, aircraft_burn_factor: float) -> float:
        """
        Estimate additional fuel burn due to carrying extra weight on this route.

        Args:
            extra_weight (float): Extra weight in kg (cargo + tankering fuel)
            aircraft_burn_factor (float): Aircraft's additional burn factor (kg/kg/nm)

        Returns:
            float: Additional fuel burn in kg
        """
        return aircraft_burn_factor * extra_weight * self.distance

    @classmethod
    def create_mle_tfu(cls) -> 'Route':
        """
        Factory method to create the MLE-TFU route with default specifications.

        Returns:
            Route: Configured MLE-TFU route instance
        """
        return cls(
            origin="TFU",
            destination="MLE",
            distance=2662,            # nm
            flight_time=6.08,         # hours
            flight_level=380,         # FL
            wind_component=-22,       # knots, negative for headwind
            min_trip_fuel=32841,      # kg
            contingency_fuel_pct=0.05,
            reserve_fuel=2500,        # kg
            fuel_price_origin=0.6875, # USD/liter
            fuel_price_dest=0.9974,   # USD/liter
            cargo_revenue_rate=2.6    # USD/kg
        )

    @classmethod
    def create_mle_pek(cls) -> 'Route':
        """
        Factory method to create the MLE-PEK route.
        Note: Placeholder values, should be updated with actual data.

        Returns:
            Route: Configured MLE-PEK route instance
        """
        return cls(
            origin="PEK",
            destination="MLE",
            distance=3800,            # nm (placeholder)
            flight_time=8.5,          # hours (placeholder)
            flight_level=380,         # FL (placeholder)
            wind_component=-25,       # knots, negative for headwind (placeholder)
            min_trip_fuel=45000,      # kg (placeholder)
            contingency_fuel_pct=0.05,
            reserve_fuel=2500,        # kg
            fuel_price_origin=0.6853, # USD/liter
            fuel_price_dest=0.9974,   # USD/liter
            cargo_revenue_rate=2.6    # USD/kg
        )

    @classmethod
    def create_mle_pvg(cls) -> 'Route':
        """
        Factory method to create the MLE-PVG route.
        Note: Placeholder values, should be updated with actual data.

        Returns:
            Route: Configured MLE-PVG route instance
        """
        return cls(
            origin="PVG",
            destination="MLE",
            distance=4000,            # nm (placeholder)
            flight_time=9.0,          # hours (placeholder)
            flight_level=380,         # FL (placeholder)
            wind_component=-25,       # knots, negative for headwind (placeholder)
            min_trip_fuel=47000,      # kg (placeholder)
            contingency_fuel_pct=0.05,
            reserve_fuel=2500,        # kg
            fuel_price_origin=0.5914, # USD/liter
            fuel_price_dest=0.9974,   # USD/liter
            cargo_revenue_rate=2.6    # USD/kg
        )


def load_route_from_config(config: Dict[str, Any]) -> Route:
    """
    Create a Route instance from a configuration dictionary.

    Args:
        config (Dict[str, Any]): Dictionary containing route specifications

    Returns:
        Route: Configured route instance

    Raises:
        ValueError: If required keys are missing from the config
    """
    required_keys = [
        'origin', 'destination', 'distance', 'flight_time',
        'flight_level', 'wind_component', 'min_trip_fuel'
    ]

    # Check if all required keys are present
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required route configuration keys: {missing_keys}")

    # Create route with required fields
    route = Route(
        origin=config['origin'],
        destination=config['destination'],
        distance=float(config['distance']),
        flight_time=float(config['flight_time']),
        flight_level=int(config['flight_level']),
        wind_component=float(config['wind_component']),
        min_trip_fuel=float(config['min_trip_fuel'])
    )

    # Add optional fields if present
    if 'contingency_fuel_pct' in config:
        route.contingency_fuel_pct = float(config['contingency_fuel_pct'])
    if 'reserve_fuel' in config:
        route.reserve_fuel = float(config['reserve_fuel'])
    if 'fuel_price_origin' in config:
        route.fuel_price_origin = float(config['fuel_price_origin'])
    if 'fuel_price_dest' in config:
        route.fuel_price_dest = float(config['fuel_price_dest'])
    if 'cargo_revenue_rate' in config:
        route.cargo_revenue_rate = float(config['cargo_revenue_rate'])

    return route