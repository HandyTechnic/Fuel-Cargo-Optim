"""
Data loader module for the fuel and cargo optimization system.

This module provides functions to load aircraft, route, and economic data from
various sources such as CSV files, databases, or web services.
"""
from typing import Dict, Any, List, Optional, Union
import os
import csv
import json
import yaml
import pandas as pd

from src.models.aircraft import Aircraft
from src.models.route import Route, load_route_from_config
from src.models.economics import FuelPrice, CargoRate


def load_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        List[Dict[str, Any]]: List of dictionaries with column names as keys
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    try:
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")


def load_aircraft_from_csv(file_path: str) -> Aircraft:
    """
    Load aircraft data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Aircraft: Aircraft instance
    
    Raises:
        ValueError: If required fields are missing
    """
    data = load_csv_data(file_path)
    
    if not data:
        raise ValueError("CSV file contains no data")
    
    # Assume the CSV has only one row of aircraft data
    aircraft_data = data[0]
    
    required_fields = [
        'aircraft_type', 'owe', 'mtow', 'mlw', 'mzfw', 'fuel_capacity',
        'fuel_density', 'passenger_capacity', 'std_pax_weight'
    ]
    
    # Check for missing fields
    missing_fields = [field for field in required_fields if field not in aircraft_data]
    if missing_fields:
        raise ValueError(f"Missing required aircraft fields: {missing_fields}")
    
    # Create aircraft instance
    return Aircraft(
        aircraft_type=aircraft_data['aircraft_type'],
        owe=float(aircraft_data['owe']),
        variable_load=float(aircraft_data.get('variable_load', 0)),
        mtow=float(aircraft_data['mtow']),
        mlw=float(aircraft_data['mlw']),
        mzfw=float(aircraft_data['mzfw']),
        fuel_capacity=float(aircraft_data['fuel_capacity']),
        fuel_density=float(aircraft_data['fuel_density']),
        passenger_capacity=int(aircraft_data['passenger_capacity']),
        std_pax_weight=float(aircraft_data['std_pax_weight']),
        additional_burn_factor=float(aircraft_data.get('additional_burn_factor', 0.0001))
    )


def load_routes_from_csv(file_path: str) -> Dict[str, Route]:
    """
    Load route data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Dict[str, Route]: Dictionary mapping route codes to Route instances
    
    Raises:
        ValueError: If required fields are missing
    """
    data = load_csv_data(file_path)
    
    if not data:
        raise ValueError("CSV file contains no data")
    
    required_fields = [
        'origin', 'destination', 'distance', 'flight_time',
        'flight_level', 'wind_component', 'min_trip_fuel'
    ]
    
    routes = {}
    
    for route_data in data:
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in route_data]
        if missing_fields:
            route_id = f"{route_data.get('origin', 'Unknown')}-{route_data.get('destination', 'Unknown')}"
            print(f"Warning: Skipping route {route_id} due to missing fields: {missing_fields}")
            continue
        
        # Create route instance
        route = Route(
            origin=route_data['origin'],
            destination=route_data['destination'],
            distance=float(route_data['distance']),
            flight_time=float(route_data['flight_time']),
            flight_level=int(route_data['flight_level']),
            wind_component=float(route_data['wind_component']),
            min_trip_fuel=float(route_data['min_trip_fuel']),
            contingency_fuel_pct=float(route_data.get('contingency_fuel_pct', 0.05)),
            reserve_fuel=float(route_data.get('reserve_fuel', 2500.0)),
            fuel_price_origin=float(route_data.get('fuel_price_origin', 0)) if 'fuel_price_origin' in route_data else None,
            fuel_price_dest=float(route_data.get('fuel_price_dest', 0)) if 'fuel_price_dest' in route_data else None,
            cargo_revenue_rate=float(route_data.get('cargo_revenue_rate', 0)) if 'cargo_revenue_rate' in route_data else None
        )
        
        # Add to routes dictionary
        route_id = f"{route.origin}-{route.destination}"
        routes[route_id] = route
    
    return routes


def load_fuel_prices_from_csv(file_path: str) -> Dict[str, FuelPrice]:
    """
    Load fuel price data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Dict[str, FuelPrice]: Dictionary mapping airport codes to FuelPrice instances
    """
    data = load_csv_data(file_path)
    
    if not data:
        raise ValueError("CSV file contains no data")
    
    required_fields = ['airport_code', 'price_per_liter', 'update_date']
    
    prices = {}
    
    for price_data in data:
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in price_data]
        if missing_fields:
            print(f"Warning: Skipping fuel price for {price_data.get('airport_code', 'Unknown')} due to missing fields: {missing_fields}")
            continue
        
        # Create fuel price instance
        fuel_price = FuelPrice(
            airport_code=price_data['airport_code'],
            price_per_liter=float(price_data['price_per_liter']),
            update_date=price_data['update_date']
        )
        
        # Add to prices dictionary
        prices[fuel_price.airport_code] = fuel_price
    
    return prices


def load_cargo_rates_from_csv(file_path: str) -> Dict[str, CargoRate]:
    """
    Load cargo rate data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Dict[str, CargoRate]: Dictionary mapping route codes to CargoRate instances
    """
    data = load_csv_data(file_path)
    
    if not data:
        raise ValueError("CSV file contains no data")
    
    required_fields = ['origin', 'destination', 'rate_per_kg', 'update_date']
    
    rates = {}
    
    for rate_data in data:
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in rate_data]
        if missing_fields:
            route_id = f"{rate_data.get('origin', 'Unknown')}-{rate_data.get('destination', 'Unknown')}"
            print(f"Warning: Skipping cargo rate for route {route_id} due to missing fields: {missing_fields}")
            continue
        
        # Create cargo rate instance
        cargo_rate = CargoRate(
            origin=rate_data['origin'],
            destination=rate_data['destination'],
            rate_per_kg=float(rate_data['rate_per_kg']),
            update_date=rate_data['update_date']
        )
        
        # Add to rates dictionary
        route_id = f"{cargo_rate.origin}-{cargo_rate.destination}"
        rates[route_id] = cargo_rate
    
    return rates


def parse_tfu_study(file_path: str) -> Dict[str, Any]:
    """
    Parse the TFU study CSV file to extract fuel burn information.
    
    Args:
        file_path: Path to the CSV file
    
    Returns:
        Dict[str, Any]: Dictionary with parsed data
    
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"TFU study file not found: {file_path}")
    
    try:
        # Read CSV using pandas for better handling
        df = pd.read_csv(file_path)
        
        # Clean up column names by stripping whitespace
        df.columns = [col.strip() for col in df.columns]
        
        # Extract relevant columns and convert to numeric
        data = {
            'extra_fuel': df['EXTRA'].astype(float).tolist(),
            'trip_fuel': df['Trip Fuel'].astype(float).tolist(),
            'extra_burn': df['Extra Burn Due. Tankering'].astype(float).tolist(),
            'contingency': df['Cont.'].astype(float).tolist(),
            'alternate': df['ALTN'].astype(float).tolist(),
            'final_reserve': df['FINRES'].astype(float).tolist(),
            'block_fuel': df['BLOCK'].astype(float).tolist()
        }
        
        # Calculate additional burn factor from the data
        extra_fuel = data['extra_fuel']
        extra_burn = data['extra_burn']
        
        # Filter out zero values to avoid division by zero
        valid_pairs = [(ef, eb) for ef, eb in zip(extra_fuel, extra_burn) if ef > 0]
        
        if valid_pairs:
            # Calculate burn factors for each data point
            burn_factors = [eb / ef for ef, eb in valid_pairs]
            
            # Take the average burn factor
            avg_burn_factor = sum(burn_factors) / len(burn_factors)
            
            # Assuming route distance of 2662 nm from data_collection_template.md
            route_distance = 2662
            
            # Calculate burn factor per kg per nm
            burn_factor_per_nm = avg_burn_factor / route_distance
            
            data['avg_burn_factor'] = avg_burn_factor
            data['burn_factor_per_nm'] = burn_factor_per_nm
        
        # Extract fuel prices if available
        try:
            # Look for fuel price data in the bottom part of the CSV
            fuel_price_rows = df.iloc[-10:].dropna(how='all')
            mle_price_idx = fuel_price_rows[fuel_price_rows.iloc[:, 0] == 'Fuel Price MLE'].index
            
            if not mle_price_idx.empty:
                row_idx = mle_price_idx[0]
                data['fuel_price_mle'] = df.iloc[row_idx, 1]
                data['fuel_price_tfu'] = df.iloc[row_idx, 2]
                data['price_diff_percent'] = df.iloc[row_idx, 3]
        except Exception as e:
            print(f"Warning: Could not extract fuel price data: {str(e)}")
        
        return data
    
    except Exception as e:
        raise ValueError(f"Failed to parse TFU study file: {str(e)}")


def calculate_burn_factor_from_tfu_study(file_path: str) -> float:
    """
    Calculate the additional burn factor from the TFU study data.
    
    Args:
        file_path: Path to the TFU study CSV file
    
    Returns:
        float: Additional burn factor (kg/kg/nm)
    
    Raises:
        ValueError: If the calculation fails
    """
    try:
        tfu_data = parse_tfu_study(file_path)
        return tfu_data.get('burn_factor_per_nm', 0.0001)  # Default if calculation fails
    except Exception as e:
        print(f"Warning: Failed to calculate burn factor from TFU study: {str(e)}")
        return 0.0001  # Default value


def load_json_data(file_path: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Dict[str, Any]: Loaded data
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON file: {str(e)}")


def load_yaml_data(file_path: str) -> Dict[str, Any]:
    """
    Load data from a YAML file.
    
    Args:
        file_path: Path to the YAML file
    
    Returns:
        Dict[str, Any]: Loaded data
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file cannot be parsed
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse YAML file: {str(e)}")


def load_aircraft_from_config(config: Dict[str, Any]) -> Aircraft:
    """
    Create an Aircraft instance from a configuration dictionary.
    
    Args:
        config: Dictionary containing aircraft specifications
    
    Returns:
        Aircraft: Configured aircraft instance
    
    Raises:
        ValueError: If required keys are missing from the config
    """
    required_keys = [
        'aircraft_type', 'owe', 'mtow', 'mlw', 'mzfw', 'fuel_capacity',
        'fuel_density', 'passenger_capacity', 'std_pax_weight'
    ]
    
    # Check if all required keys are present
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required aircraft configuration keys: {missing_keys}")
    
    # Create aircraft with required fields
    return Aircraft(
        aircraft_type=config['aircraft_type'],
        owe=float(config['owe']),
        variable_load=float(config.get('variable_load', 0)),
        mtow=float(config['mtow']),
        mlw=float(config['mlw']),
        mzfw=float(config['mzfw']),
        fuel_capacity=float(config['fuel_capacity']),
        fuel_density=float(config['fuel_density']),
        passenger_capacity=int(config['passenger_capacity']),
        std_pax_weight=float(config['std_pax_weight']),
        additional_burn_factor=float(config.get('additional_burn_factor', 0.0001))
    )


def update_route_prices(routes: Dict[str, Route], fuel_prices: Dict[str, FuelPrice]) -> None:
    """
    Update routes with current fuel prices.
    
    Args:
        routes: Dictionary of Route instances
        fuel_prices: Dictionary of FuelPrice instances
    """
    for route_id, route in routes.items():
        # Update origin fuel price if available
        if route.origin in fuel_prices:
            route.fuel_price_origin = fuel_prices[route.origin].price_per_liter
        
        # Update destination fuel price if available
        if route.destination in fuel_prices:
            route.fuel_price_dest = fuel_prices[route.destination].price_per_liter


def update_route_cargo_rates(routes: Dict[str, Route], cargo_rates: Dict[str, CargoRate]) -> None:
    """
    Update routes with current cargo rates.
    
    Args:
        routes: Dictionary of Route instances
        cargo_rates: Dictionary of CargoRate instances
    """
    for route_id, route in routes.items():
        if route_id in cargo_rates:
            route.cargo_revenue_rate = cargo_rates[route_id].rate_per_kg


def save_optimization_results(results: Dict[str, Any], file_path: str) -> None:
    """
    Save optimization results to a file.
    
    Args:
        results: Optimization results
        file_path: Path to save the results
    """
    # Determine file format from extension
    _, ext = os.path.splitext(file_path)
    
    try:
        with open(file_path, 'w') as f:
            if ext.lower() == '.json':
                json.dump(results, f, indent=2)
            elif ext.lower() == '.csv':
                writer = csv.DictWriter(f, fieldnames=results.keys())
                writer.writeheader()
                writer.writerow(results)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        print(f"Warning: Failed to save optimization results: {str(e)}")