"""
Fuel and Cargo Optimization System

This is the main entry point for the fuel and cargo optimization application.
It integrates all components and provides a command-line interface for now,
with GUI capabilities planned for future implementation.
"""
import argparse
from typing import Dict, Any, Optional

from src.models.aircraft import Aircraft
from src.models.route import Route, load_route_from_config
from src.optimization.optimizer import optimize_for_route, Optimizer
from src.optimization.constraints import validate_weight_distribution
from src.optimization.fuel_calc import (
    calculate_fuel_weight_impact,
    calculate_tankering_factor,
    examine_fuel_weight_tradeoff
)
from src.utils.logger import OptimLogger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fuel and Cargo Optimization System')
    
    # Required arguments
    parser.add_argument('--route', type=str, choices=['MLE-TFU', 'MLE-PEK', 'MLE-PVG'],
                       help='Route to optimize')
    parser.add_argument('--pax', type=int, default=237,
                       help='Number of passengers')
    
    # Optional user overrides
    parser.add_argument('--regulated-mtow', type=float,
                       help='Regulated maximum take-off weight (kg)')
    parser.add_argument('--regulated-mlw', type=float,
                       help='Regulated maximum landing weight (kg)')
    parser.add_argument('--actual-zfw', type=float,
                       help='Actual zero fuel weight (kg)')
    parser.add_argument('--block-fuel', type=float,
                       help='Block fuel (kg)')
    parser.add_argument('--taxi-fuel', type=float,
                       help='Taxi fuel (kg)')
    
    # Optimization method
    parser.add_argument('--method', type=str, default='linear',
                       choices=['linear', 'grid_search'],
                       help='Optimization method')
    
    # Output options
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--output', type=str,
                       help='Output file for results')

    return parser.parse_args()


def get_route_from_code(route_code: str) -> Route:
    """
    Get route instance from route code.
    
    Args:
        route_code: Route code (e.g., 'MLE-TFU')
        
    Returns:
        Route: Route instance
        
    Raises:
        ValueError: If route code is invalid
    """
    if route_code == 'MLE-TFU':
        return Route.create_mle_tfu()
    elif route_code == 'MLE-PEK':
        return Route.create_mle_pek()
    elif route_code == 'MLE-PVG':
        return Route.create_mle_pvg()
    else:
        raise ValueError(f"Invalid route code: {route_code}")


def process_user_overrides(args) -> Dict[str, float]:
    """
    Process user overrides from command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dict[str, float]: User overrides dictionary
    """
    overrides = {}
    
    if args.regulated_mtow:
        overrides['regulated_mtow'] = args.regulated_mtow
    
    if args.regulated_mlw:
        overrides['regulated_mlw'] = args.regulated_mlw
    
    if args.actual_zfw:
        overrides['actual_zfw'] = args.actual_zfw
    
    if args.block_fuel:
        overrides['block_fuel'] = args.block_fuel
    
    if args.taxi_fuel:
        overrides['taxi_fuel'] = args.taxi_fuel
    
    return overrides


def display_results(result: Dict[str, Any], aircraft: Aircraft, route: Route, logger: OptimLogger):
    """
    Display optimization results.
    
    Args:
        result: Optimization result dictionary
        aircraft: Aircraft instance
        route: Route instance
        logger: Logger instance
    """
    # Log the detailed results
    logger.log_optimization_result(
        optimal_cargo=result.optimal_cargo,
        optimal_tankering=result.optimal_tankering,
        total_profit=result.total_profit,
        cargo_revenue=result.cargo_revenue,
        fuel_savings=result.fuel_savings,
        additional_burn=result.additional_burn,
        tom=result.tom,
        zfm=result.zfm,
        lm=result.lm,
        limiting_factor=result.limiting_factor
    )
    
    # Log any constraint violations
    logger.log_constraint_violations(result.violations)
    
    # Print formatted results to console
    print("\n===== OPTIMIZATION RESULTS =====")
    print(f"Route: {route.origin}-{route.destination} ({route.distance} nm)")
    print(f"Aircraft: A330-203")
    print(f"Status: {result.status}")
    
    if result.status.startswith("ERROR"):
        print(f"Error: {result.status}")
        return
    
    print("\n--- Optimal Solution ---")
    print(f"Optimal Cargo: {result.optimal_cargo:.2f} kg")
    print(f"Optimal Tankering: {result.optimal_tankering:.2f} kg")
    
    print("\n--- Economics ---")
    print(f"Total Profit: ${result.total_profit:.2f}")
    print(f"  - Cargo Revenue: ${result.cargo_revenue:.2f}")
    print(f"  - Fuel Savings: ${result.fuel_savings:.2f}")
    
    print("\n--- Weights ---")
    print(f"Take-off Mass: {result.tom:.2f} kg")
    print(f"Zero Fuel Mass: {result.zfm:.2f} kg")
    print(f"Landing Mass: {result.lm:.2f} kg")
    print(f"Trip Fuel: {result.trip_fuel:.2f} kg")
    print(f"Total Fuel: {result.total_fuel:.2f} kg")
    print(f"Additional Burn: {result.additional_burn:.2f} kg")
    
    print("\n--- Constraints ---")
    if result.constraints_violated:
        print("WARNING: Some constraints are violated!")
        for constraint, violation in result.violations.items():
            if violation > 0:
                print(f"  - {constraint}: {violation:.2f} kg over limit")
    else:
        print("All constraints satisfied.")
    
    print(f"Limiting Factor: {result.limiting_factor}")
    
    # Calculate tankering factor
    if route.fuel_price_origin is not None and route.fuel_price_dest is not None:
        tankering_factor = calculate_tankering_factor(
            route.fuel_price_origin,
            route.fuel_price_dest,
            route.distance,
            aircraft.additional_burn_factor
        )
        print(f"\nTankering Factor: {tankering_factor:.4f}")
        print(f"  (Factor > 1.0 suggests tankering may be beneficial)")


def main():
    """Main function to run the optimization."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = OptimLogger(enable_console=True, enable_file=True)
    logger.log_info("Starting Fuel and Cargo Optimization")
    
    # Get aircraft instance (currently only A330-203 is supported)
    aircraft = Aircraft.create_a330_203()
    
    # Get route instance
    if args.route:
        try:
            route = get_route_from_code(args.route)
        except ValueError as e:
            logger.log_error(str(e))
            return
    else:
        logger.log_info("No route specified, using MLE-TFU as default")
        route = Route.create_mle_tfu()
    
    # Process user overrides
    user_overrides = process_user_overrides(args)
    
    # Log input parameters
    logger.log_input_parameters(
        aircraft_type=aircraft.aircraft_type,
        route=f"{route.origin}-{route.destination}",
        pax_count=args.pax,
        fuel_price_origin=route.fuel_price_origin or 0,
        fuel_price_dest=route.fuel_price_dest or 0,
        cargo_rate=route.cargo_revenue_rate or 0,
        user_overrides=user_overrides
    )
    
    # Run optimization
    try:
        result = optimize_for_route(
            aircraft=aircraft,
            route=route,
            pax_count=args.pax,
            user_overrides=user_overrides,
            method=args.method
        )
        
        # Display results
        display_results(result, aircraft, route, logger)
        
        # If requested, analyze tradeoff
        if args.verbose:
            logger.log_info("Analyzing cargo-fuel tradeoff...")
            
            # Create optimizer instance for analysis
            optimizer = Optimizer(aircraft, route, args.pax, user_overrides)
            
            # Analyze tradeoff
            tradeoff_analysis = optimizer.analyze_tradeoff(steps=10)
            
            # Log tradeoff analysis
            logger.log_tradeoff_analysis(tradeoff_analysis)
            
            # Calculate max payload
            max_cargo = optimizer.constraints.max_cargo_weight()
            logger.log_info(f"Maximum cargo weight: {max_cargo:.2f} kg")
            
            # Fuel price info
            if route.fuel_price_origin is not None and route.fuel_price_dest is not None:
                logger.log_info(f"Fuel price at {route.origin}: ${route.fuel_price_origin:.4f}/liter")
                logger.log_info(f"Fuel price at {route.destination}: ${route.fuel_price_dest:.4f}/liter")
                logger.log_info(f"Price difference: ${route.fuel_price_dest - route.fuel_price_origin:.4f}/liter")
            
            # Tankering factor
            tankering_factor = calculate_tankering_factor(
                route.fuel_price_origin or 0,
                route.fuel_price_dest or 0,
                route.distance,
                aircraft.additional_burn_factor
            )
            logger.log_info(f"Tankering factor: {tankering_factor:.4f}")
        
    except Exception as e:
        logger.log_error("Optimization failed", e)
        return
    
    logger.log_info("Optimization completed successfully")


if __name__ == "__main__":
    main()