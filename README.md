# FastBox Delivery System

## How to Run
```bash
python delivery_system.py
```

## Assumptions Made
1. **Nearest Agent Assignment** — Each package is assigned to the agent 
   closest to the package's warehouse (not destination), using Euclidean distance.
2. **Tie-breaking** — If two agents are equidistant, Python's `min()` picks 
   the first one alphabetically (A1 before A2).
3. **Routing Order** — Agent delivers packages in the order they were assigned.
4. **Mid-day Agent (A4)** — Joins at [25, 60] after initial assignment; 
   receives no packages since all were already assigned.
5. **Efficiency** — Defined as total_distance / packages_delivered 
   (lower = better). Agents with 0 packages are excluded from best_agent selection.
6. **Distance Unit** — Treated as km on a 2D coordinate plane.
