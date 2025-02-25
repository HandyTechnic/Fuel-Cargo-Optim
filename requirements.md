# Cargo Load and Fuel Tankering Optimization Requirements

## Project Overview
This document outlines the requirements for a system that optimizes the balance between cargo load and fuel tankering for an A330-203 aircraft operating on MLE-TFU, MLE-PEK, and MLE-PVG routes.

## Core Requirements
1. The system must optimize between cargo revenue and fuel cost savings
2. The system must guarantee capacity for 264 passengers
3. The system must respect all aircraft limitations including MTOW, MLW, and fuel capacity
4. The system must provide clear recommendations on optimal cargo load and fuel tankering

## Data Requirements

### Aircraft Data (A330-203)
1. Basic specifications:
   - Maximum Take-Off Weight (MTOW)
   - Maximum Landing Weight (MLW)
   - Maximum Zero Fuel Weight (MZFW)
   - Operating Empty Weight (OWE)
   - Maximum structural payload
   - Maximum fuel capacity

2. Performance data:
   - Fuel consumption rates at various weights and distances
   - Relationship between extra weight and additional fuel burn
   - Standard passenger weights and configuration

### Route Data
1. For each route (MLE-TFU, MLE-PEK, MLE-PVG):
   - Distance in nautical miles
   - Typical flight time
   - Standard flight level
   - Average wind component

### Economic Data
1. Fuel information:
   - Current fuel prices at each airport (MLE, TFU, PEK, PVG)
   - Fuel density conversion factor (kg/liter)
   - Into-plane fees if applicable

2. Cargo information:
   - Revenue per kg for cargo on each route
   - Cargo demand patterns
   - Priority cargo considerations

### Operational Constraints
1. Standard fuel reserves policy
2. Minimum contingency fuel requirements
3. Company-specific operating procedures
4. Any route-specific restrictions