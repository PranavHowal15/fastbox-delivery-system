"""
FastBox Logistics Simulator
============================
Simulates one day of delivery operations:
  - Reads warehouses, agents, and packages from data.json
  - Assigns each package to the nearest available agent
  - Simulates pick-up → delivery with distance tracking
  - Generates a JSON report + CSV top performer export
  - Visualizes routes on an ASCII grid
  - Supports random delivery delays and a new mid-day agent
"""

import json
import math
import random
import csv
import time
import os


# ──────────────────────────────────────────────
# 1. UTILITY: Euclidean Distance
# ──────────────────────────────────────────────
def euclidean_distance(point_a: list, point_b: list) -> float:
    """Return straight-line distance between two [x, y] coordinates."""
    return math.sqrt((point_a[0] - point_b[0]) ** 2 +
                     (point_a[1] - point_b[1]) ** 2)


# ──────────────────────────────────────────────
# 2. JSON PARSING
# ──────────────────────────────────────────────
def load_data(filepath: str) -> dict:
    """Read and parse the JSON input file. Returns the raw data dict."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    # Basic validation
    required_keys = {"warehouses", "agents", "packages"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"JSON is missing required keys: {missing}")

    print(f"[DATA] Loaded {len(data['warehouses'])} warehouses, "
          f"{len(data['agents'])} agents, "
          f"{len(data['packages'])} packages.\n")
    return data


# ──────────────────────────────────────────────
# 3. AGENT-PACKAGE ASSIGNMENT (nearest agent)
# ──────────────────────────────────────────────
def assign_packages(packages: list, agents: dict, warehouses: dict) -> dict:
    """
    For every package, find the agent whose current position is
    closest to the package's warehouse, then assign the package to
    that agent.

    Returns:
        assignments  – { agent_id: [list of packages] }
    """
    # Initialise empty bucket for every agent
    assignments = {agent_id: [] for agent_id in agents}

    for pkg in packages:
        warehouse_pos = warehouses[pkg["warehouse"]]

        # Find the nearest agent to this package's warehouse
        nearest_agent = min(
            agents.keys(),
            key=lambda aid: euclidean_distance(agents[aid], warehouse_pos)
        )

        assignments[nearest_agent].append(pkg)
        print(f"  [ASSIGN] Package {pkg['id']} (warehouse {pkg['warehouse']}) "
              f"→ Agent {nearest_agent}  "
              f"(dist={euclidean_distance(agents[nearest_agent], warehouse_pos):.2f})")

    print()
    return assignments


# ──────────────────────────────────────────────
# 4. SIMULATION: Pick-up + Delivery
# ──────────────────────────────────────────────
def simulate_deliveries(assignments: dict,
                        agents: dict,
                        warehouses: dict,
                        enable_delays: bool = True) -> dict:
    """
    For each agent, simulate the route:
      current_pos → warehouse → destination  (for every package)

    Computes:
      - total distance travelled
      - packages delivered
      - efficiency = total_distance / packages_delivered

    Returns:
        results  – { agent_id: { packages_delivered, total_distance,
                                  efficiency, route } }
    """
    results = {}

    for agent_id, pkgs in assignments.items():
        # Agent starts from their initial position
        current_pos = list(agents[agent_id])
        total_distance = 0.0
        route = [tuple(current_pos)]  # for ASCII visualisation

        print(f"[SIM] Agent {agent_id} starts at {current_pos}")

        for pkg in pkgs:
            warehouse_pos = warehouses[pkg["warehouse"]]
            destination   = pkg["destination"]

            # Leg 1: travel to warehouse to pick up package
            leg1 = euclidean_distance(current_pos, warehouse_pos)
            total_distance += leg1
            current_pos = list(warehouse_pos)
            route.append(tuple(current_pos))

            # Leg 2: travel from warehouse to destination
            leg2 = euclidean_distance(current_pos, destination)
            total_distance += leg2
            current_pos = list(destination)
            route.append(tuple(current_pos))

            # ── BONUS: Random delivery delay ──────────────────────────
            delay = 0
            if enable_delays and random.random() < 0.3:   # 30 % chance
                delay = random.randint(5, 30)             # minutes
                print(f"    ⚠  Delay: {pkg['id']} delayed {delay} min "
                      f"(traffic / weather)")
            # ──────────────────────────────────────────────────────────

            print(f"  → {pkg['id']}: warehouse→dest  "
                  f"({leg1:.2f} + {leg2:.2f} = {leg1+leg2:.2f} km) "
                  + (f"| delay {delay} min" if delay else ""))

        packages_delivered = len(pkgs)
        efficiency = (round(total_distance / packages_delivered, 2)
                      if packages_delivered else 0.0)

        results[agent_id] = {
            "packages_delivered": packages_delivered,
            "total_distance":     round(total_distance, 2),
            "efficiency":         efficiency,
            "route":              route          # used by ASCII visualiser
        }

        print(f"  ✔  {agent_id}: {packages_delivered} packages | "
              f"distance={total_distance:.2f} | efficiency={efficiency:.2f}\n")

    return results


# ──────────────────────────────────────────────
# 5. REPORT GENERATION
# ──────────────────────────────────────────────
def generate_report(results: dict) -> dict:
    """
    Build the final report dict.  Finds the best agent by lowest
    efficiency score (distance per package – smaller = better).
    """
    # Only consider agents that actually delivered something
    active = {aid: v for aid, v in results.items()
              if v["packages_delivered"] > 0}

    best_agent = min(active, key=lambda aid: active[aid]["efficiency"])

    report = {}
    for agent_id, data in results.items():
        report[agent_id] = {
            "packages_delivered": data["packages_delivered"],
            "total_distance":     data["total_distance"],
            "efficiency":         data["efficiency"]
        }
    report["best_agent"] = best_agent
    return report


def save_report(report: dict, filepath: str) -> None:
    """Write the report dict to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(report, f, indent=4)
    print(f"[REPORT] Saved → {filepath}")


# ──────────────────────────────────────────────
# BONUS A: Export top performer to CSV
# ──────────────────────────────────────────────
def export_top_performer_csv(report: dict, filepath: str) -> None:
    """Write the best agent's stats to a CSV file."""
    best = report["best_agent"]
    stats = report[best]

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent", "packages_delivered",
                         "total_distance", "efficiency"])
        writer.writerow([best,
                         stats["packages_delivered"],
                         stats["total_distance"],
                         stats["efficiency"]])

    print(f"[CSV]    Top performer ({best}) exported → {filepath}")


# ──────────────────────────────────────────────
# BONUS B: ASCII Route Visualiser
# ──────────────────────────────────────────────
def ascii_visualise(results: dict,
                    warehouses: dict,
                    grid_size: int = 24) -> None:
    """
    Render all agent routes on a simple ASCII grid.
    Grid is scaled so that coordinate 110 maps to grid_size cells.
    """
    scale = grid_size / 115.0   # world coords go up to ~110

    def to_grid(x, y):
        gx = min(int(x * scale), grid_size - 1)
        gy = min(int(y * scale), grid_size - 1)
        return gx, gy

    # Blank grid (origin bottom-left)
    grid = [["·"] * grid_size for _ in range(grid_size)]

    # Mark warehouses
    for wid, (wx, wy) in warehouses.items():
        gx, gy = to_grid(wx, wy)
        grid[grid_size - 1 - gy][gx] = "W"

    # Agent symbols and route markers
    AGENT_SYMBOLS = {"A1": "1", "A2": "2", "A3": "3", "A4": "4"}
    for agent_id, data in results.items():
        sym = AGENT_SYMBOLS.get(agent_id, "A")
        route = data["route"]
        for (rx, ry) in route:
            gx, gy = to_grid(rx, ry)
            if grid[grid_size - 1 - gy][gx] not in ("W",):
                grid[grid_size - 1 - gy][gx] = sym

    print("\n" + "=" * (grid_size + 4))
    print("  ASCII ROUTE MAP  (W=warehouse, 1/2/3=agent routes)")
    print("=" * (grid_size + 4))
    for row in grid:
        print("  " + " ".join(row))
    print("=" * (grid_size + 4) + "\n")


# ──────────────────────────────────────────────
# BONUS C: New Agent Joins Mid-Day
# ──────────────────────────────────────────────
def add_midday_agent(data: dict, new_agent_id: str,
                     position: list) -> None:
    """
    Inject a new agent into the data dict mid-simulation.
    In a real system this would trigger re-assignment of
    undelivered packages; here we show the concept.
    """
    data["agents"][new_agent_id] = position
    print(f"[MID-DAY] New agent {new_agent_id} joined at {position}!\n")


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────
def main():
    random.seed(42)   # reproducible randomness

    BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
    DATA_FILE  = os.path.join(BASE_DIR, "data.json")
    REPORT_FILE = os.path.join(BASE_DIR, "report.json")
    CSV_FILE    = os.path.join(BASE_DIR, "top_performer.csv")

    print("=" * 55)
    print("   FastBox Logistics Simulator — Day Simulation")
    print("=" * 55 + "\n")

    # ── Step 1: Load data ────────────────────────────────────
    data = load_data(DATA_FILE)

    # ── BONUS C: New agent joins mid-day ─────────────────────
    add_midday_agent(data, "A4", [25, 60])

    warehouses = data["warehouses"]
    agents     = data["agents"]
    packages   = data["packages"]

    # ── Step 2: Assign packages → nearest agent ───────────────
    print("[PHASE 1] Package Assignment\n" + "-" * 40)
    assignments = assign_packages(packages, agents, warehouses)

    # ── Step 3: Simulate deliveries ───────────────────────────
    print("[PHASE 2] Delivery Simulation\n" + "-" * 40)
    results = simulate_deliveries(assignments, agents, warehouses,
                                  enable_delays=True)

    # ── Step 4: Generate & save report ────────────────────────
    print("[PHASE 3] Report\n" + "-" * 40)
    report = generate_report(results)
    save_report(report, REPORT_FILE)

    # ── BONUS A: CSV export ───────────────────────────────────
    export_top_performer_csv(report, CSV_FILE)

    # ── BONUS B: ASCII visualisation ─────────────────────────
    ascii_visualise(results, warehouses)

    # ── Final summary ─────────────────────────────────────────
    print("\n" + "=" * 55)
    print("   FINAL REPORT SUMMARY")
    print("=" * 55)
    for agent_id, stats in report.items():
        if agent_id == "best_agent":
            continue
        star = " ⭐ BEST" if agent_id == report["best_agent"] else ""
        print(f"  {agent_id}: {stats['packages_delivered']} pkg(s) | "
              f"dist={stats['total_distance']:.2f} | "
              f"eff={stats['efficiency']:.2f}{star}")
    print(f"\n  🏆 Most Efficient Agent: {report['best_agent']}")
    print("=" * 55)


if __name__ == "__main__":
    main()
