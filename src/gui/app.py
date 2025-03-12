"""
GUI Application for Fuel and Cargo Optimization System.

This module provides a graphical user interface for the fuel and cargo optimization
system, allowing users to select routes, input parameters, and view optimization results.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.aircraft import Aircraft
from models.route import Route
from optimization.optimizer import Optimizer, OptimizationResult
from optimization.fuel_calc import (
    calculate_tankering_factor,
    examine_fuel_weight_tradeoff
)
from utils.logger import OptimLogger


class FuelCargoOptimizerApp:
    """
    Main application class for the Fuel and Cargo Optimizer GUI.
    """
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Fuel and Cargo Optimizer")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Set up logger
        self.logger = OptimLogger(enable_console=True, enable_file=True)
        
        # Initialize aircraft (default to A330-203)
        self.aircraft = Aircraft.create_a330_203()
        
        # Initialize route dictionary
        self.routes = {
            'MLE-TFU': Route.create_mle_tfu(),
            'MLE-PEK': Route.create_mle_pek(),
            'MLE-PVG': Route.create_mle_pvg()
        }
        
        # Selected route
        self.selected_route = None
        
        # User input variables
        self.pax_count_var = tk.IntVar(value=237)
        
        # Weight override values
        self.regulated_mtow_var = tk.DoubleVar(value=self.aircraft.mtow)
        self.regulated_mlw_var = tk.DoubleVar(value=self.aircraft.mlw)
        self.actual_zfw_var = tk.DoubleVar(value=0)
        self.block_fuel_var = tk.DoubleVar(value=0)
        self.taxi_fuel_var = tk.DoubleVar(value=600)
        
        # Override checkboxes
        self.use_regulated_mtow_var = tk.BooleanVar(value=False)
        self.use_regulated_mlw_var = tk.BooleanVar(value=False)
        self.use_actual_zfw_var = tk.BooleanVar(value=False)
        self.use_block_fuel_var = tk.BooleanVar(value=False)
        self.use_taxi_fuel_var = tk.BooleanVar(value=False)
        
        # Cargo revenue rate (separate from weight overrides)
        self.cargo_revenue_var = tk.DoubleVar(value=0)  # Default to 0, will be updated when route selected
        
        # Optimization method
        self.optim_method_var = tk.StringVar(value="linear")
        
        # Results
        self.optimization_result = None
        
        # Create the main UI
        self.create_ui()
    
    def create_ui(self):
        """Create the user interface."""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for inputs
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create route selection
        route_frame = ttk.Frame(input_frame)
        route_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(route_frame, text="Route:").pack(side=tk.LEFT)
        self.route_combo = ttk.Combobox(route_frame, values=list(self.routes.keys()), width=10)
        self.route_combo.pack(side=tk.LEFT, padx=5)
        self.route_combo.bind("<<ComboboxSelected>>", self.on_route_selected)
        
        ttk.Label(route_frame, text="Passengers:").pack(side=tk.LEFT, padx=(20, 0))
        pax_entry = ttk.Entry(route_frame, textvariable=self.pax_count_var, width=8)
        pax_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(route_frame, text="Optimization Method:").pack(side=tk.LEFT, padx=(20, 0))
        method_combo = ttk.Combobox(route_frame, textvariable=self.optim_method_var,
                                  values=["linear", "grid_search"], width=12)
        method_combo.pack(side=tk.LEFT, padx=5)
        
        # Add cargo revenue rate field (separate from weight overrides)
        cargo_frame = ttk.Frame(input_frame)
        cargo_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(cargo_frame, text="Cargo Revenue Rate ($/kg):").pack(side=tk.LEFT)
        ttk.Entry(cargo_frame, textvariable=self.cargo_revenue_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Create weight overrides frame
        weights_frame = ttk.LabelFrame(input_frame, text="Weight Overrides (Optional)", padding="10")
        weights_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # First row of weight overrides
        row1 = ttk.Frame(weights_frame)
        row1.pack(fill=tk.X, pady=5)
        
        # MTOW with checkbox
        ttk.Checkbutton(row1, variable=self.use_regulated_mtow_var).pack(side=tk.LEFT)
        ttk.Label(row1, text="Regulated MTOW (kg):").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.regulated_mtow_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # MLW with checkbox
        ttk.Checkbutton(row1, variable=self.use_regulated_mlw_var).pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(row1, text="Regulated MLW (kg):").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.regulated_mlw_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # ZFW with checkbox
        ttk.Checkbutton(row1, variable=self.use_actual_zfw_var).pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(row1, text="Actual ZFW (kg):").pack(side=tk.LEFT)
        self.zfw_entry = ttk.Entry(row1, textvariable=self.actual_zfw_var, width=10)
        self.zfw_entry.pack(side=tk.LEFT, padx=5)
        
        # Second row of weight overrides
        row2 = ttk.Frame(weights_frame)
        row2.pack(fill=tk.X, pady=5)
        
        # Block Fuel with checkbox
        ttk.Checkbutton(row2, variable=self.use_block_fuel_var).pack(side=tk.LEFT)
        ttk.Label(row2, text="Block Fuel (kg):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.block_fuel_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Taxi Fuel with checkbox
        ttk.Checkbutton(row2, variable=self.use_taxi_fuel_var).pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(row2, text="Taxi Fuel (kg):").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.taxi_fuel_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Optimize", command=self.run_optimization).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Defaults", command=self.reset_defaults).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Results", command=self.export_results).pack(side=tk.LEFT, padx=5)
        
        # Create notebook for results
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create results tabs
        self.summary_frame = ttk.Frame(self.results_notebook, padding="10")
        self.results_notebook.add(self.summary_frame, text="Summary")
        
        self.details_frame = ttk.Frame(self.results_notebook, padding="10")
        self.results_notebook.add(self.details_frame, text="Details")
        
        self.charts_frame = ttk.Frame(self.results_notebook, padding="10")
        self.results_notebook.add(self.charts_frame, text="Charts")
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Select default route
        self.route_combo.set("MLE-TFU")
        self.on_route_selected(None)
    
    def on_route_selected(self, event):
        """
        Handle route selection event.
        
        Args:
            event: ComboboxSelected event
        """
        route_code = self.route_combo.get()
        if route_code in self.routes:
            self.selected_route = self.routes[route_code]
            
            # Update status
            self.status_var.set(f"Selected route: {route_code}, Distance: {self.selected_route.distance} nm")
            
            # Update cargo revenue default value if available
            if self.selected_route.cargo_revenue_rate is not None:
                self.cargo_revenue_var.set(self.selected_route.cargo_revenue_rate)
                
            # Update fuel price labels if available
            if hasattr(self, 'fuel_price_origin_var') and hasattr(self, 'fuel_price_dest_var'):
                self.fuel_price_origin_var.set(f"{self.selected_route.fuel_price_origin:.4f} USD/liter")
                self.fuel_price_dest_var.set(f"{self.selected_route.fuel_price_dest:.4f} USD/liter")
            
            # Update ZFW display
            self.update_zfw_display()
    
    def get_user_overrides(self) -> Dict[str, float]:
        """
        Get user overrides from input fields.
        
        Returns:
            Dict[str, float]: Dictionary of user overrides
        """
        overrides = {}
        
        # Only add values if the corresponding checkbox is checked
        if self.use_regulated_mtow_var.get():
            overrides['regulated_mtow'] = self.regulated_mtow_var.get()
        
        if self.use_regulated_mlw_var.get():
            overrides['regulated_mlw'] = self.regulated_mlw_var.get()
        
        if self.use_actual_zfw_var.get():
            overrides['actual_zfw'] = self.actual_zfw_var.get()
        
        if self.use_block_fuel_var.get():
            overrides['block_fuel'] = self.block_fuel_var.get()
        
        if self.use_taxi_fuel_var.get():
            overrides['taxi_fuel'] = self.taxi_fuel_var.get()
        
        # Add cargo revenue rate if it differs from the route's default
        cargo_revenue = self.cargo_revenue_var.get()
        if self.selected_route and cargo_revenue != self.selected_route.cargo_revenue_rate:
            overrides['cargo_revenue_rate'] = cargo_revenue
        
        return overrides
    
    def run_optimization(self):
        """Run the optimization based on user inputs."""
        if not self.selected_route:
            messagebox.showerror("Error", "Please select a route first")
            return
        
        # Get input parameters
        pax_count = self.pax_count_var.get()
        method = self.optim_method_var.get()
        user_overrides = self.get_user_overrides()
        
        # Explicitly add cargo revenue rate to overrides
        user_overrides['cargo_revenue_rate'] = self.cargo_revenue_var.get()
        
        # Update status
        self.status_var.set("Running optimization...")
        self.root.update_idletasks()
        # Update status
        self.status_var.set("Running optimization...")
        self.root.update_idletasks()
        
        try:
            # Create optimizer
            optimizer = Optimizer(
                aircraft=self.aircraft,
                route=self.selected_route,
                pax_count=pax_count,
                user_overrides=user_overrides
            )
            
            # Run optimization
            self.optimization_result = optimizer.optimize(method)
            
            # Log results
            self.logger.log_input_parameters(
                aircraft_type=self.aircraft.aircraft_type,
                route=f"{self.selected_route.origin}-{self.selected_route.destination}",
                pax_count=pax_count,
                fuel_price_origin=self.selected_route.fuel_price_origin or 0,
                fuel_price_dest=self.selected_route.fuel_price_dest or 0,
                cargo_rate=self.selected_route.cargo_revenue_rate or 0,
                user_overrides=user_overrides
            )
            
            self.logger.log_optimization_result(
                optimal_cargo=self.optimization_result.optimal_cargo,
                optimal_tankering=self.optimization_result.optimal_tankering,
                total_profit=self.optimization_result.total_profit,
                cargo_revenue=self.optimization_result.cargo_revenue,
                fuel_savings=self.optimization_result.fuel_savings,
                additional_burn=self.optimization_result.additional_burn,
                tom=self.optimization_result.tom,
                zfm=self.optimization_result.zfm,
                lm=self.optimization_result.lm,
                limiting_factor=self.optimization_result.limiting_factor
            )
            
            # Update UI with results
            self.update_results_display()
            
            # Update status
            self.status_var.set("Optimization completed successfully")
            
        except Exception as e:
            messagebox.showerror("Optimization Error", str(e))
            self.logger.log_error("Optimization failed", e)
            self.status_var.set(f"Error: {str(e)}")
    
    def update_results_display(self):
        """Update the results display with optimization results."""
        if not self.optimization_result:
            return
        
        # Clear existing results
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        
        # Format results for summary tab
        result = self.optimization_result
        
        # Create summary frame contents
        summary_title = ttk.Label(
            self.summary_frame,
            text=f"Optimization Results for {self.selected_route.origin}-{self.selected_route.destination}",
            font=("Helvetica", 14, "bold")
        )
        summary_title.pack(pady=(0, 10))
        
        # Main results frame
        main_results = ttk.Frame(self.summary_frame)
        main_results.pack(fill=tk.BOTH, expand=True)
        
        # Left column - Optimal solution
        left_col = ttk.LabelFrame(main_results, text="Optimal Solution", padding="10")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(left_col, text=f"Optimal Cargo: {result.optimal_cargo:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(left_col, text=f"Optimal Tankering: {result.optimal_tankering:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(left_col, text=f"Total Fuel: {result.total_fuel:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(left_col, text=f"Trip Fuel: {result.trip_fuel:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(left_col, text=f"Additional Burn: {result.additional_burn:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        
        # Center column - Economics
        center_col = ttk.LabelFrame(main_results, text="Economics", padding="10")
        center_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Label(center_col, text=f"Total Profit: ${result.total_profit:.2f}",
                 font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=2)
        ttk.Label(center_col, text=f"Cargo Revenue: ${result.cargo_revenue:.2f}",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(center_col, text=f"Fuel Savings: ${result.fuel_savings:.2f}",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)

        # Fuel prices
        price_frame = ttk.Frame(center_col)
        price_frame.pack(anchor=tk.W, pady=2, fill=tk.X)
        ttk.Label(price_frame, text="Fuel Price Origin:").pack(side=tk.LEFT)
        ttk.Label(price_frame, text=f"${self.selected_route.fuel_price_origin:.4f}/liter").pack(side=tk.LEFT, padx=5)

        price_frame2 = ttk.Frame(center_col)
        price_frame2.pack(anchor=tk.W, pady=2, fill=tk.X)
        ttk.Label(price_frame2, text="Fuel Price Destination:").pack(side=tk.LEFT)
        ttk.Label(price_frame2, text=f"${self.selected_route.fuel_price_dest:.4f}/liter").pack(side=tk.LEFT, padx=5)

        # Cargo rate
        cargo_rate_frame = ttk.Frame(center_col)
        cargo_rate_frame.pack(anchor=tk.W, pady=2, fill=tk.X)
        ttk.Label(cargo_rate_frame, text="Cargo Revenue Rate:").pack(side=tk.LEFT)
        ttk.Label(cargo_rate_frame, text=f"${self.cargo_revenue_var.get():.2f}/kg").pack(side=tk.LEFT, padx=5)

        # Calculate and display tankering factor
        tankering_factor = calculate_tankering_factor(
            self.selected_route.fuel_price_origin or 0,
            self.selected_route.fuel_price_dest or 0,
            self.selected_route.distance,
            self.aircraft.additional_burn_factor
        )
        ttk.Label(center_col, text=f"Tankering Factor: {tankering_factor:.4f}",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        
        # Right column - Weights
        right_col = ttk.LabelFrame(main_results, text="Weights", padding="10")
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(right_col, text=f"Take-Off Mass: {result.tom:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(right_col, text=f"Zero Fuel Mass: {result.zfm:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(right_col, text=f"Landing Mass: {result.lm:.2f} kg",
                 font=("Helvetica", 12)).pack(anchor=tk.W, pady=2)
        ttk.Label(right_col, text=f"Limiting Factor: {result.limiting_factor}",
                 font=("Helvetica", 12, "bold")).pack(anchor=tk.W, pady=2)
        
        # Add constraint violations if any
        if result.constraints_violated:
            violations_frame = ttk.LabelFrame(self.summary_frame, text="Constraint Violations", padding="10")
            violations_frame.pack(fill=tk.X, pady=10)
            
            for constraint, violation in result.violations.items():
                if violation > 0:
                    ttk.Label(
                        violations_frame,
                        text=f"{constraint}: {violation:.2f} kg over limit",
                        foreground="red"
                    ).pack(anchor=tk.W)
        
        # Create details frame contents
        details_title = ttk.Label(
            self.details_frame,
            text="Detailed Results",
            font=("Helvetica", 14, "bold")
        )
        details_title.pack(pady=(0, 10))
        
        # Create a treeview for detailed data
        columns = ("Parameter", "Value", "Unit")
        details_tree = ttk.Treeview(self.details_frame, columns=columns, show="headings")
        details_tree.pack(fill=tk.BOTH, expand=True)
        
        # Set column headings
        for col in columns:
            details_tree.heading(col, text=col)
            details_tree.column(col, width=100)
        
        # Add data - Aircraft and Route
        details_tree.insert("", "end", values=("Aircraft Type", self.aircraft.aircraft_type, ""))
        details_tree.insert("", "end", values=("Route", f"{self.selected_route.origin}-{self.selected_route.destination}", ""))
        details_tree.insert("", "end", values=("Distance", f"{self.selected_route.distance}", "nm"))
        details_tree.insert("", "end", values=("Passenger Count", f"{self.pax_count_var.get()}", "pax"))
        details_tree.insert("", "end", values=("Passenger Weight", f"{self.pax_count_var.get() * self.aircraft.std_pax_weight:.2f}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add Fuel Breakdown Section
        details_tree.insert("", "end", values=("=== FUEL BREAKDOWN ===", "", ""))
        
        # Calculate base fuel components (without extra weight)
        base_trip_fuel = self.selected_route.min_trip_fuel
        base_contingency = base_trip_fuel * self.selected_route.contingency_fuel_pct
        alternate_fuel = getattr(self.selected_route, 'alternate_fuel', 0.0)
        reserve_fuel = self.selected_route.reserve_fuel
        base_req_fuel = base_trip_fuel + base_contingency + alternate_fuel + reserve_fuel
        
        # Calculate actual fuel components with extra weight
        actual_trip_fuel = result.trip_fuel
        actual_contingency = actual_trip_fuel * self.selected_route.contingency_fuel_pct
        # For alternate fuel, we typically use the same value, but it might increase with weight
        # Let's estimate a small increase proportional to the trip fuel increase
        actual_alternate = alternate_fuel
        if alternate_fuel > 0 and base_trip_fuel > 0:
            # Adjust alternate fuel proportionally to trip fuel increase
            actual_alternate = alternate_fuel * (actual_trip_fuel / base_trip_fuel)
        actual_req_fuel = actual_trip_fuel + actual_contingency + actual_alternate + reserve_fuel
        
        # Calculate differences
        trip_fuel_increase = actual_trip_fuel - base_trip_fuel
        contingency_increase = actual_contingency - base_contingency
        alternate_increase = actual_alternate - alternate_fuel
        total_req_increase = actual_req_fuel - base_req_fuel
        
        # Add base fuel values
        details_tree.insert("", "end", values=("Base Trip Fuel", f"{base_trip_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Base Contingency Fuel", f"{base_contingency:.2f}", "kg"))
        if alternate_fuel > 0:
            details_tree.insert("", "end", values=("Alternate Fuel", f"{alternate_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Final Reserve", f"{reserve_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Base Required Fuel", f"{base_req_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add actual fuel values with extra weight
        details_tree.insert("", "end", values=("Actual Trip Fuel", f"{actual_trip_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Actual Contingency Fuel", f"{actual_contingency:.2f}", "kg"))
        if alternate_fuel > 0:
            details_tree.insert("", "end", values=("Alternate Fuel", f"{alternate_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Final Reserve", f"{reserve_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("Actual Required Fuel", f"{actual_req_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add differences due to extra weight
        details_tree.insert("", "end", values=("Trip Fuel Increase", f"{trip_fuel_increase:.2f}", "kg"))
        details_tree.insert("", "end", values=("Contingency Increase", f"{contingency_increase:.2f}", "kg"))
        if alternate_fuel > 0:
            details_tree.insert("", "end", values=("Alternate Increase", f"{alternate_increase:.2f}", "kg"))
        details_tree.insert("", "end", values=("Total Required Increase", f"{total_req_increase:.2f}", "kg"))
        details_tree.insert("", "end", values=("Additional Burn", f"{result.additional_burn:.2f}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add total fuel values - using REQTOF and ACTTOF terminology from the TFU study
        details_tree.insert("", "end", values=("REQTOF (Required Fuel)", f"{actual_req_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("EXTRA (Tankering)", f"{result.optimal_tankering:.2f}", "kg"))
        details_tree.insert("", "end", values=("ACTTOF (Total Fuel)", f"{result.total_fuel:.2f}", "kg"))
        if self.use_taxi_fuel_var.get():
            taxi_fuel = self.taxi_fuel_var.get()
            details_tree.insert("", "end", values=("TAXI", f"{taxi_fuel:.2f}", "kg"))
            details_tree.insert("", "end", values=("BLOCK", f"{result.total_fuel + taxi_fuel:.2f}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add cargo and economics section
        details_tree.insert("", "end", values=("=== CARGO & ECONOMICS ===", "", ""))
        details_tree.insert("", "end", values=("Optimal Cargo", f"{result.optimal_cargo:.2f}", "kg"))
        details_tree.insert("", "end", values=("Cargo Revenue Rate", f"{self.cargo_revenue_var.get():.2f}", "USD/kg"))
        details_tree.insert("", "end", values=("Cargo Revenue", f"{result.cargo_revenue:.2f}", "USD"))
        details_tree.insert("", "end", values=("Fuel Savings", f"{result.fuel_savings:.2f}", "USD"))
        details_tree.insert("", "end", values=("Total Profit", f"{result.total_profit:.2f}", "USD"))
        details_tree.insert("", "end", values=("", "", ""))
        
        # Add weights section
        details_tree.insert("", "end", values=("=== WEIGHTS ===", "", ""))
        details_tree.insert("", "end", values=("Take-Off Mass", f"{result.tom:.2f}", "kg"))
        details_tree.insert("", "end", values=("Zero Fuel Mass", f"{result.zfm:.2f}", "kg"))
        details_tree.insert("", "end", values=("Landing Mass", f"{result.lm:.2f}", "kg"))
        details_tree.insert("", "end", values=("MTOW", f"{self.aircraft.mtow}", "kg"))
        details_tree.insert("", "end", values=("MZFW", f"{self.aircraft.mzfw}", "kg"))
        details_tree.insert("", "end", values=("MLW", f"{self.aircraft.mlw}", "kg"))
        details_tree.insert("", "end", values=("DOM", f"{self.aircraft.dom}", "kg"))
        details_tree.insert("", "end", values=("", "", ""))
        
        details_tree.insert("", "end", values=("Limiting Factor", result.limiting_factor, ""))
        details_tree.insert("", "end", values=("Status", result.status, ""))
        
        # Create charts frame contents
        charts_title = ttk.Label(
            self.charts_frame,
            text="Analysis Charts",
            font=("Helvetica", 14, "bold")
        )
        charts_title.pack(pady=(0, 10))
        
        # Create charts frame with two charts side by side
        charts_container = ttk.Frame(self.charts_frame)
        charts_container.pack(fill=tk.BOTH, expand=True)
        
        # Left chart - Profit breakdown
        left_chart_frame = ttk.LabelFrame(charts_container, text="Profit Breakdown")
        left_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        fig1 = plt.Figure(figsize=(5, 4), dpi=100)
        ax1 = fig1.add_subplot(111)
        
        # Profit breakdown data
        labels = ['Cargo Revenue', 'Fuel Savings']
        values = [result.cargo_revenue, result.fuel_savings]
        colors = ['#4CAF50', '#2196F3']
        
        ax1.bar(labels, values, color=colors)
        ax1.set_ylabel('USD')
        ax1.set_title('Profit Components')
        
        for i, v in enumerate(values):
            ax1.text(i, v/2, f"${v:.2f}", ha='center', va='center', color='white', fontweight='bold')
        
        canvas1 = FigureCanvasTkAgg(fig1, left_chart_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right chart - Weight distribution
        right_chart_frame = ttk.LabelFrame(charts_container, text="Weight Distribution")
        right_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        fig2 = plt.Figure(figsize=(5, 4), dpi=100)
        ax2 = fig2.add_subplot(111)
        
        # Weight distribution data
        pax_weight = self.pax_count_var.get() * self.aircraft.std_pax_weight
        labels = ['DOM', 'Passengers', 'Cargo', 'Fuel']
        values = [self.aircraft.dom, pax_weight, result.optimal_cargo, result.total_fuel]
        colors = ['#9C27B0', '#FF9800', '#4CAF50', '#2196F3']
        
        # Create pie chart
        wedges, texts, autotexts = ax2.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Make text more readable
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')
        
        ax2.set_title('Aircraft Weight Components')
        ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        canvas2 = FigureCanvasTkAgg(fig2, right_chart_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add a third chart at the bottom - Tradeoff analysis
        bottom_chart_frame = ttk.LabelFrame(self.charts_frame, text="Cargo vs. Fuel Tradeoff Analysis")
        bottom_chart_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Create optimizer for tradeoff analysis
        optimizer = Optimizer(
            aircraft=self.aircraft,
            route=self.selected_route,
            pax_count=self.pax_count_var.get(),
            user_overrides=self.get_user_overrides()
        )
        
        # Get tradeoff analysis
        tradeoff_points = optimizer.analyze_tradeoff(steps=10)
        
        # Create figure for tradeoff analysis
        fig3 = plt.Figure(figsize=(10, 4), dpi=100)
        ax3 = fig3.add_subplot(111)
        
        # Extract data from tradeoff points, handling invalid points
        valid_points = [p for p in tradeoff_points if 'valid' in p and p['valid']]
        
        if valid_points:
            cargo_vals = [p['cargo'] for p in valid_points]
            fuel_vals = [p['extra_fuel'] for p in valid_points]
            profit_vals = [p['total_profit'] for p in valid_points]
            
            # Set up twin axes
            ax3_twin = ax3.twinx()
            
            # Plot weight values
            line1 = ax3.plot(cargo_vals, label='Cargo (kg)', color='#4CAF50', marker='o')
            line2 = ax3.plot(fuel_vals, label='Extra Fuel (kg)', color='#2196F3', marker='s')
            
            # Plot profit values on twin axis
            line3 = ax3_twin.plot(profit_vals, label='Total Profit ($)', color='#FF5722', marker='^', linestyle='--')
            
            # Set labels
            ax3.set_xlabel('Tradeoff Point')
            ax3.set_ylabel('Weight (kg)')
            ax3_twin.set_ylabel('Profit ($)')
            
            # Create combined legend
            lines = line1 + line2 + line3
            labels = [line.get_label() for line in lines]
            ax3.legend(lines, labels, loc='upper center')
            
            # Highlight the optimal point
            optimal_idx = None
            for i, p in enumerate(valid_points):
                if abs(p['cargo'] - result.optimal_cargo) < 1 and abs(p['extra_fuel'] - result.optimal_tankering) < 1:
                    optimal_idx = i
                    break
            
            if optimal_idx is not None:
                ax3.plot([optimal_idx], [cargo_vals[optimal_idx]], 'o', color='red', markersize=10)
                ax3.plot([optimal_idx], [fuel_vals[optimal_idx]], 's', color='red', markersize=10)
                ax3_twin.plot([optimal_idx], [profit_vals[optimal_idx]], '^', color='red', markersize=10)
            
            # Set title
            ax3.set_title('Cargo vs. Fuel Tradeoff Analysis')
            
            # Adjust layout
            fig3.tight_layout()
        else:
            ax3.text(0.5, 0.5, 'No valid tradeoff points found',
                    horizontalalignment='center', verticalalignment='center',
                    transform=ax3.transAxes)
        
        canvas3 = FigureCanvasTkAgg(fig3, bottom_chart_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def update_zfw_display(self, event=None):
        """
        Update the zero fuel weight display based on passenger count.
        
        Args:
            event: Event that triggered the update (optional)
        """
        try:
            pax_count = self.pax_count_var.get()
            
            # Calculate passenger weight
            pax_weight = pax_count * self.aircraft.std_pax_weight
            
            # Calculate ZFW
            calculated_zfw = self.aircraft.dom + pax_weight
            
            # Only update if not manually set
            if not self.use_actual_zfw_var.get():
                self.actual_zfw_var.set(calculated_zfw)
                
            self.status_var.set(f"Updated ZFW based on {pax_count} passengers: {calculated_zfw:.2f} kg")
        except Exception as e:
            # Ignore errors during typing
            pass

    def reset_defaults(self):
        """Reset all input fields to default values."""
        self.pax_count_var.set(237)
        self.regulated_mtow_var.set(self.aircraft.mtow)
        self.regulated_mlw_var.set(self.aircraft.mlw)
        
        # Reset checkboxes
        self.use_regulated_mtow_var.set(False)
        self.use_regulated_mlw_var.set(False)
        self.use_actual_zfw_var.set(False)
        self.use_block_fuel_var.set(False)
        self.use_taxi_fuel_var.set(False)
        
        # Reset block fuel and taxi fuel
        self.block_fuel_var.set(0)
        self.taxi_fuel_var.set(600)
        
        # Reset optimization method
        self.optim_method_var.set("linear")
        
        # If route is selected, reset cargo revenue rate to route default
        if self.selected_route and self.selected_route.cargo_revenue_rate is not None:
            self.cargo_revenue_var.set(self.selected_route.cargo_revenue_rate)
        else:
            self.cargo_revenue_var.set(0)
        
        # Update ZFW display
        self.update_zfw_display()
        
        # Update status
        self.status_var.set("Input values reset to defaults")
    
    def export_results(self):
        """Export the optimization results to a file."""
        if not self.optimization_result:
            messagebox.showerror("Error", "No optimization results to export")
            return
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w') as f:
                result = self.optimization_result
                route = self.selected_route
                
                # Write header
                f.write(f"Fuel and Cargo Optimization Results\n")
                f.write(f"==============================\n\n")
                
                # Write input parameters
                f.write(f"Input Parameters:\n")
                f.write(f"  Aircraft: {self.aircraft.aircraft_type}\n")
                f.write(f"  Route: {route.origin}-{route.destination} ({route.distance} nm)\n")
                f.write(f"  Passengers: {self.pax_count_var.get()}\n")
                f.write(f"  Optimization Method: {self.optim_method_var.get()}\n\n")
                
                # Write economic data
                f.write(f"Economic Data:\n")
                f.write(f"  Fuel Price at {route.origin}: ${route.fuel_price_origin:.4f}/liter\n")
                f.write(f"  Fuel Price at {route.destination}: ${route.fuel_price_dest:.4f}/liter\n")
                f.write(f"  Cargo Revenue Rate: ${route.cargo_revenue_rate:.2f}/kg\n\n")
                
                # Write results
                f.write(f"Optimization Results:\n")
                f.write(f"  Status: {result.status}\n")
                f.write(f"  Optimal Cargo: {result.optimal_cargo:.2f} kg\n")
                f.write(f"  Optimal Tankering: {result.optimal_tankering:.2f} kg\n")
                f.write(f"  Total Fuel: {result.total_fuel:.2f} kg\n")
                f.write(f"  Trip Fuel: {result.trip_fuel:.2f} kg\n")
                f.write(f"  Additional Burn: {result.additional_burn:.2f} kg\n\n")
                
                f.write(f"Economics:\n")
                f.write(f"  Total Profit: ${result.total_profit:.2f}\n")
                f.write(f"  Cargo Revenue: ${result.cargo_revenue:.2f}\n")
                f.write(f"  Fuel Savings: ${result.fuel_savings:.2f}\n\n")
                
                f.write(f"Weights:\n")
                f.write(f"  Take-Off Mass: {result.tom:.2f} kg\n")
                f.write(f"  Zero Fuel Mass: {result.zfm:.2f} kg\n")
                f.write(f"  Landing Mass: {result.lm:.2f} kg\n")
                f.write(f"  Limiting Factor: {result.limiting_factor}\n\n")
                
                # Write constraint violations if any
                if result.constraints_violated:
                    f.write(f"Constraint Violations:\n")
                    for constraint, violation in result.violations.items():
                        if violation > 0:
                            f.write(f"  {constraint}: {violation:.2f} kg over limit\n")
                    f.write("\n")
                
                # Write a timestamp
                import datetime
                now = datetime.datetime.now()
                f.write(f"Report generated on {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Update status
            self.status_var.set(f"Results exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
            self.status_var.set(f"Error exporting results: {str(e)}")


def main():
    """Main function to start the GUI application."""
    root = tk.Tk()
    app = FuelCargoOptimizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()