"""
Aircraft model that defines specifications and basic weight calculations for aircraft types.
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Aircraft:
    """
    Aircraft model containing all relevant specifications and weight calculations.

    Attributes:
        aircraft_type (str): Type designation of the aircraft (e.g., "A330-203")
        owe (float): Basic Empty Mass in kg
        variable_load (float): Variable operational items (crew, catering, etc.) in kg
        mtow (float): Maximum Take-Off Weight in kg
        mlw (float): Maximum Landing Weight in kg
        mzfw (float): Maximum Zero Fuel Weight in kg
        fuel_capacity (float): Maximum fuel capacity in kg
        fuel_density (float): Conversion factor from kg to liters
        passenger_capacity (int): Standard passenger capacity
        std_pax_weight (float): Standard weight per passenger including baggage
    """

    aircraft_type: str
    owe: float
    variable_load: float
    mtow: float
    mlw: float
    mzfw: float
    fuel_capacity: float
    fuel_density: float
    passenger_capacity: int
    std_pax_weight: float
    additional_burn_factor: float = 0.0001  # Default value, can be adjusted

    @property
    def dom(self) -> float:
        """
        Calculate the Dry Operating Mass (DOM).

        Returns:
            float: Dry Operating Mass (OWE + Variable Load) in kg
        """
        return self.owe + self.variable_load

    def get_limiting_tom(self, required_fuel: float, trip_fuel: float) -> Tuple[float, str]:
        """
        Calculate the limiting take-off mass based on aircraft limitations.

        Args:
            required_fuel (float): Total required fuel in kg (includes trip, contingency, reserves)
            trip_fuel (float): Trip fuel for the route in kg

        Returns:
            Tuple[float, str]: The limiting take-off mass in kg and the limiting factor
        """
        mtow_limit = self.mtow
        mzfw_limit = self.mzfw + required_fuel
        mlw_limit = self.mlw + trip_fuel

        limits = [mtow_limit, mzfw_limit, mlw_limit]
        limit_names = ['MTOW', 'MZFW+Fuel', 'MLW+TripFuel']

        limiting_tom = min(limits)
        limiting_factor = limit_names[limits.index(limiting_tom)]

        return limiting_tom, limiting_factor

    def calculate_zfm(self, pax_count: int, cargo_weight: float) -> float:
        """
        Calculate Zero Fuel Mass.

        Args:
            pax_count (int): Number of passengers
            cargo_weight (float): Weight of cargo in kg

        Returns:
            float: Zero Fuel Mass in kg
        """
        return self.dom + (pax_count * self.std_pax_weight) + cargo_weight

    def calculate_tom(self, pax_count: int, cargo_weight: float, total_fuel: float) -> float:
        """
        Calculate Take-Off Mass.

        Args:
            pax_count (int): Number of passengers
            cargo_weight (float): Weight of cargo in kg
            total_fuel (float): Total fuel onboard in kg

        Returns:
            float: Take-Off Mass in kg
        """
        zfm = self.calculate_zfm(pax_count, cargo_weight)
        return zfm + total_fuel

    @staticmethod
    def calculate_landing_mass(tom: float, trip_fuel: float) -> float:
        """
        Calculate Landing Mass.

        Args:
            tom (float): Take-Off Mass in kg
            trip_fuel (float): Trip fuel in kg

        Returns:
            float: Landing Mass in kg
        """
        return tom - trip_fuel

    @classmethod
    def create_a330_203(cls) -> 'Aircraft':
        """
        Factory method to create an A330-203 aircraft with default specifications.

        Returns:
            Aircraft: Configured A330-203 aircraft instance
        """
        return cls(
            aircraft_type="A330-203",
            owe=120310,  # Basic Empty Mass in kg
            variable_load=0,  # Set to 0, can be updated based on specific flight
            mtow=233000,  # Maximum Take-Off Weight in kg
            mlw=182000,  # Maximum Landing Weight in kg
            mzfw=170000,  # Maximum Zero Fuel Weight in kg
            fuel_capacity=109186,  # Maximum fuel capacity in kg
            fuel_density=0.785,  # kg/liter
            passenger_capacity=264,  # Full passenger capacity
            std_pax_weight=102,  # Standard weight per passenger including baggage
            additional_burn_factor=0.0001  # Additional fuel burn factor
        )

    def calculate_additional_burn(self, extra_weight: float, distance: float) -> float:
        """
        Calculate additional fuel burn due to extra weight.

        Args:
            extra_weight (float): Extra weight carried (cargo + extra fuel) in kg
            distance (float): Flight distance in nautical miles

        Returns:
            float: Additional fuel burn in kg
        """
        return self.additional_burn_factor * extra_weight * distance