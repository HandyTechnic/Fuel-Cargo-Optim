"""
Economics model that defines financial calculations for fuel tankering and cargo optimization.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class FuelPrice:
    """
    Fuel price data for an airport.

    Attributes:
        airport_code (str): IATA airport code
        price_per_liter (float): Fuel price in USD per liter
        update_date (str): Date of the price update (ISO format: YYYY-MM-DD)
    """
    airport_code: str
    price_per_liter: float
    update_date: str


@dataclass
class CargoRate:
    """
    Cargo revenue rate for a route.

    Attributes:
        origin (str): Origin airport IATA code
        destination (str): Destination airport IATA code
        rate_per_kg (float): Revenue rate in USD per kg
        update_date (str): Date of the rate update (ISO format: YYYY-MM-DD)
    """
    origin: str
    destination: str
    rate_per_kg: float
    update_date: str


class Economics:
    """
    Economics model for calculating costs and revenues for fuel tankering and cargo optimization.
    """

    @staticmethod
    def calculate_tankering_savings(
        uplifted_fuel: float,
        price_origin: float,
        price_destination: float,
        fuel_density: float,
        additional_burn: float = 0.0
    ) -> float:
        """
        Calculate the savings from tankering fuel.

        Args:
            uplifted_fuel (float): Amount of extra fuel uplifted in kg
            price_origin (float): Fuel price at origin in USD per liter
            price_destination (float): Fuel price at destination in USD per liter
            fuel_density (float): Fuel density in kg per liter
            additional_burn (float): Additional fuel burn due to tankering in kg

        Returns:
            float: Savings in USD (negative value means loss)
        """
        # Convert kg to liters
        uplifted_fuel_liters = uplifted_fuel / fuel_density
        
        # Calculate the cost of uplifting extra fuel at origin
        cost_at_origin = uplifted_fuel_liters * price_origin
        
        # Calculate the value of fuel that won't be purchased at destination
        # (accounting for additional burn)
        effective_tankered_fuel = uplifted_fuel - additional_burn
        effective_tankered_fuel_liters = effective_tankered_fuel / fuel_density
        value_at_destination = effective_tankered_fuel_liters * price_destination
        
        # Net savings
        return value_at_destination - cost_at_origin

    @staticmethod
    def calculate_cargo_revenue(cargo_weight: float, rate_per_kg: float) -> float:
        """
        Calculate revenue from carrying cargo.

        Args:
            cargo_weight (float): Weight of cargo in kg
            rate_per_kg (float): Revenue rate in USD per kg

        Returns:
            float: Revenue in USD
        """
        return cargo_weight * rate_per_kg

    @staticmethod
    def calculate_total_profit(
        cargo_weight: float,
        cargo_rate: float,
        uplifted_fuel: float,
        price_origin: float,
        price_destination: float,
        fuel_density: float,
        additional_burn: float
    ) -> Dict[str, float]:
        """
        Calculate the total profit from cargo and fuel tankering.

        Args:
            cargo_weight (float): Weight of cargo in kg
            cargo_rate (float): Cargo revenue rate in USD per kg
            uplifted_fuel (float): Amount of extra fuel uplifted in kg
            price_origin (float): Fuel price at origin in USD per liter
            price_destination (float): Fuel price at destination in USD per liter
            fuel_density (float): Fuel density in kg per liter
            additional_burn (float): Additional fuel burn due to extra weight in kg

        Returns:
            Dict[str, float]: Breakdown of profit components and total profit
        """
        cargo_revenue = Economics.calculate_cargo_revenue(cargo_weight, cargo_rate)
        
        tankering_savings = Economics.calculate_tankering_savings(
            uplifted_fuel, price_origin, price_destination, fuel_density, additional_burn
        )
        
        # Cost of additional burn due to extra weight
        additional_burn_cost = (additional_burn / fuel_density) * price_origin
        
        total_profit = cargo_revenue + tankering_savings - additional_burn_cost
        
        return {
            "cargo_revenue": cargo_revenue,
            "tankering_savings": tankering_savings,
            "additional_burn_cost": additional_burn_cost,
            "total_profit": total_profit
        }

    @staticmethod
    def calculate_tankering_factor(price_origin: float, price_destination: float) -> float:
        """
        Calculate the tankering factor.
        A factor > 1 suggests tankering is economically beneficial.

        Args:
            price_origin (float): Fuel price at origin in USD per liter
            price_destination (float): Fuel price at destination in USD per liter

        Returns:
            float: Tankering factor
        """
        return price_destination / price_origin