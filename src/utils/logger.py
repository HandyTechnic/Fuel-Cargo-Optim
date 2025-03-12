"""
Logger module for the fuel and cargo optimization system.

This module provides logging functionality to track the optimization process,
record results, and help with debugging.
"""
import logging
import os
import time
from typing import Dict, Any, Optional


class OptimLogger:
    """
    Logger for the fuel and cargo optimization system.
    
    This class provides methods for logging various events during the optimization
    process, including input parameters, optimization results, and errors.
    """
    
    def __init__(
        self,
        log_dir: str = 'logs',
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        Initialize the logger.
        
        Args:
            log_dir: Directory to store log files
            console_level: Logging level for console output
            file_level: Logging level for file output
            enable_console: Whether to log to console
            enable_file: Whether to log to file
        """
        self.logger = logging.getLogger('fuel_cargo_optim')
        self.logger.setLevel(logging.DEBUG)  # Capture all levels
        self.logger.propagate = False  # Prevent duplicate logging
        
        # Clear existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatters
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if enable_file:
            # Create log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Create timestamped log file
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            log_file = os.path.join(log_dir, f'optimization_{timestamp}.log')
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(file_level)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def log_input_parameters(
        self,
        aircraft_type: str,
        route: str,
        pax_count: int,
        fuel_price_origin: float,
        fuel_price_dest: float,
        cargo_rate: float,
        user_overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Log input parameters for an optimization run.
        
        Args:
            aircraft_type: Type of aircraft
            route: Route designation (origin-destination)
            pax_count: Number of passengers
            fuel_price_origin: Fuel price at origin
            fuel_price_dest: Fuel price at destination
            cargo_rate: Cargo revenue rate
            user_overrides: User-specified overrides
        """
        self.logger.info(f"Starting optimization for {route} with {aircraft_type}")
        self.logger.info(f"Passengers: {pax_count}")
        self.logger.info(f"Fuel price at origin: ${fuel_price_origin:.4f}/liter")
        self.logger.info(f"Fuel price at destination: ${fuel_price_dest:.4f}/liter")
        self.logger.info(f"Cargo revenue rate: ${cargo_rate:.2f}/kg")
        
        if user_overrides:
            self.logger.info("User overrides:")
            for key, value in user_overrides.items():
                self.logger.info(f"  {key}: {value}")
    
    def log_optimization_result(
        self,
        optimal_cargo: float,
        optimal_tankering: float,
        total_profit: float,
        cargo_revenue: float,
        fuel_savings: float,
        additional_burn: float,
        tom: float,
        zfm: float,
        lm: float,
        limiting_factor: str
    ):
        """
        Log optimization results.
        
        Args:
            optimal_cargo: Optimal cargo weight
            optimal_tankering: Optimal tankering fuel
            total_profit: Total profit
            cargo_revenue: Revenue from cargo
            fuel_savings: Savings from tankering
            additional_burn: Additional fuel burn
            tom: Take-off mass
            zfm: Zero fuel mass
            lm: Landing mass
            limiting_factor: Factor limiting the solution
        """
        self.logger.info("Optimization results:")
        self.logger.info(f"Optimal cargo: {optimal_cargo:.2f} kg")
        self.logger.info(f"Optimal tankering: {optimal_tankering:.2f} kg")
        self.logger.info(f"Total profit: ${total_profit:.2f}")
        self.logger.info(f"  - Cargo revenue: ${cargo_revenue:.2f}")
        self.logger.info(f"  - Fuel savings: ${fuel_savings:.2f}")
        self.logger.info(f"Additional burn: {additional_burn:.2f} kg")
        self.logger.info(f"Take-off mass: {tom:.2f} kg")
        self.logger.info(f"Zero fuel mass: {zfm:.2f} kg")
        self.logger.info(f"Landing mass: {lm:.2f} kg")
        self.logger.info(f"Limiting factor: {limiting_factor}")
    
    def log_constraint_violations(self, violations: Dict[str, float]):
        """
        Log constraint violations.
        
        Args:
            violations: Dictionary of constraint violations
        """
        if any(v > 0 for v in violations.values()):
            self.logger.warning("Constraint violations detected:")
            for constraint, violation in violations.items():
                if violation > 0:
                    self.logger.warning(f"  {constraint}: {violation:.2f} kg")
        else:
            self.logger.info("No constraint violations")
    
    def log_error(self, message: str, exception: Optional[Exception] = None):
        """
        Log an error.
        
        Args:
            message: Error message
            exception: Exception object, if available
        """
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
        else:
            self.logger.error(message)
    
    def log_warning(self, message: str):
        """
        Log a warning.
        
        Args:
            message: Warning message
        """
        self.logger.warning(message)
    
    def log_info(self, message: str):
        """
        Log an info message.
        
        Args:
            message: Info message
        """
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """
        Log a debug message.
        
        Args:
            message: Debug message
        """
        self.logger.debug(message)
    
    def log_sensitivity_analysis(
        self,
        parameter: str,
        values: Dict[float, Dict[str, float]]
    ):
        """
        Log sensitivity analysis results.
        
        Args:
            parameter: Parameter name
            values: Dictionary mapping parameter values to result metrics
        """
        self.logger.info(f"Sensitivity analysis for {parameter}:")
        headers = list(next(iter(values.values())).keys())
        header_line = f"{'Value':<10}" + "".join([f"{h:<15}" for h in headers])
        self.logger.info(header_line)
        
        for param_value, results in values.items():
            result_line = f"{param_value:<10.4f}"
            for metric, value in results.items():
                result_line += f"{value:<15.2f}"
            self.logger.info(result_line)
    
    def log_tradeoff_analysis(self, tradeoffs: list):
        """
        Log tradeoff analysis results.
        
        Args:
            tradeoffs: List of tradeoff points
        """
        self.logger.info("Cargo vs. Fuel Tradeoff Analysis:")
        headers = list(tradeoffs[0].keys())
        header_line = "".join([f"{h:<15}" for h in headers])
        self.logger.info(header_line)
        
        for point in tradeoffs:
            result_line = ""
            for metric, value in point.items():
                if isinstance(value, float):
                    result_line += f"{value:<15.2f}"
                else:
                    result_line += f"{value:<15}"
            self.logger.info(result_line)


# Create a default logger instance for easy import
default_logger = OptimLogger()

def get_logger():
    """
    Get the default logger instance.
    
    Returns:
        OptimLogger: Default logger instance
    """
    return default_logger