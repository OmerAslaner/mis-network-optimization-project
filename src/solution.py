"""
=============================================================================
MIS Network Optimization Project
Marmara University Göztepe Campus — Fiber-Optic Backbone Network Design
Using the Maximum Flow Problem (Ford-Fulkerson / Edmonds-Karp Algorithm)

Author  : [Your Name]
Course  : Management Information Systems
Date    : 2025

Problem Statement:
    The Marmara University IT directorate must determine how much data (in
    Mbps) can be simultaneously pushed from the **Central Data Center** to
    the **Student Labs** (modelled here as a single super-sink) without
    violating the physical capacity limits of the proposed fiber-optic links.
    This is a classic Maximum Flow problem, and its solution directly informs
    budget decisions (which links to upgrade) and risk assessments (bottleneck
    identification).
=============================================================================
"""

import os
import csv
import networkx as nx
import matplotlib
matplotlib.use("Agg")                  # non-interactive backend — safe on servers
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ---------------------------------------------------------------------------
# 0.  Path helpers
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE   = os.path.join(BASE_DIR, "data", "network_data.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

VIZ_FILE    = os.path.join(RESULTS_DIR, "network_visualization.png")
OUTPUT_FILE = os.path.join(RESULTS_DIR, "solution_output.txt")


# ---------------------------------------------------------------------------
# 1.  Load the campus network from CSV
# ---------------------------------------------------------------------------
def load_network(csv_path: str) -> nx.DiGraph:
    """
    Build a directed graph from the CSV dataset.

    Nodes represent physical locations on the Marmara Göztepe campus:
        - data_center    : Central server room / IT infrastructure hub
        - rectorate      : Administrative core building
        - engineering    : Faculty of Engineering building
        - science_letters: Faculty of Science & Letters building
        - library        : Central library (major user traffic generator)
        - student_affairs: Student affairs & registrar offices
        - student_labs_A : Computer labs block A (primary end-user sink)
        - student_labs_B : Computer labs block B (primary end-user sink)
        - health_center  : Campus health center

    Edges represent proposed single-mode fiber-optic cable runs.

    Edge attribute 'capacity' (Mbps):
        The maximum data throughput the physical cable can sustain. This is
        the bottleneck resource that the Maximum Flow algorithm will respect.
        Values are derived from standard SFP transceiver ratings (1 GbE,
        10 GbE, 2.5 GbE) downscaled for realistic campus-scale planning.

    Additional edge attributes stored for reference (not used by the solver):
        - distance_m     : Physical cable run length in metres
        - cable_cost_tl  : Estimated installation cost in Turkish Lira
    """
    G = nx.DiGraph()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = row["source"].strip()
            v = row["target"].strip()
            cap   = int(row["capacity_mbps"])
            dist  = int(row["distance_m"])
            cost  = int(row["cable_cost_tl"])
            nt_u  = row["node_type_source"].strip()
            nt_v  = row["node_type_target"].strip()

            # Add nodes with metadata (used only for visualisation)
            G.add_node(u, node_type=nt_u)
            G.add_node(v, node_type=nt_v)

            # Add directed edge; 'capacity' is mandatory for nx.max_flow_value
            G.add_edge(u, v, capacity=cap, distance_m=dist, cable_cost_tl=cost)

            # Fiber is bidirectional — add the reverse arc with same capacity
            # (upload traffic from labs back to the data center)
            if not G.has_edge(v, u):
                G.add_edge(v, u, capacity=cap, distance_m=dist, cable_cost_tl=cost)

    print(f"[INFO] Graph loaded: {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} directed edges")
    return G


# ---------------------------------------------------------------------------
# 2.  Define source and super-sink
# ---------------------------------------------------------------------------
def add_super_sink(G: nx.DiGraph, sink_nodes: list, super_sink: str = "super_sink") -> nx.DiGraph:
    """
    The Maximum Flow algorithm requires a single source and a single sink.

    Real-world mapping:
        source     = data_center  (where all traffic originates)
        super_sink = virtual node that aggregates student_labs_A and
                     student_labs_B, because in practice both lab blocks
                     consume data simultaneously.

    We connect each real sink node to the super_sink with infinite capacity
    so that the aggregated pipe into the labs — not an artificial merge link —
    remains the binding constraint.
    """
    G.add_node(super_sink, node_type="virtual")
    for node in sink_nodes:
        G.add_edge(node, super_sink, capacity=float("inf"))
    return G


# ---------------------------------------------------------------------------
# 3.  Solve the Maximum Flow problem
# ---------------------------------------------------------------------------
def solve_max_flow(G: nx.DiGraph, source: str, sink: str):
    """
    Use NetworkX's implementation of the Edmonds-Karp algorithm
    (a BFS-based Ford-Fulkerson variant) to find:

        1. max_flow_value  : Total throughput (Mbps) from data_center to labs
        2. flow_dict       : Per-edge flow assignment (how many Mbps on each link)

    Time complexity: O(V * E^2) — tractable for campus-scale graphs.

    The algorithm guarantees:
        * Flow conservation at every intermediate node
        * No edge carries more flow than its capacity
        * The total flow from source to sink is maximised
    """
    flow_value, flow_dict = nx.maximum_flow(G, source, sink, flow_func=nx.algorithms.flow.edmonds_karp)
    return flow_value, flow_dict


# ---------------------------------------------------------------------------
# 4.  Identify bottleneck edges (minimum cut)
# ---------------------------------------------------------------------------
def find_min_cut(G: nx.DiGraph, source: str, sink: str):
    """
    By the Max-Flow Min-Cut Theorem, the set of edges whose removal would
    disconnect source from sink with minimum total capacity loss is called
    the **minimum cut**.  These edges are the network bottlenecks — upgrading
    them is the single highest-ROI infrastructure investment.

    Returns:
        cut_value   : Same as max_flow_value (the theorem guarantees this)
        reachable   : Nodes on the source side of the cut
        non_reachable: Nodes on the sink side of the cut
    """
    cut_value, (reachable, non_reachable) = nx.minimum_cut(G, source, sink)
    return cut_value, reachable, non_reachable


# ---------------------------------------------------------------------------
# 5.  Visualise the network
# ---------------------------------------------------------------------------
def visualise(G: nx.DiGraph, flow_dict: dict, reachable: set,
              source: str, sink: str, output_path: str):
    """
    Draw the campus network graph and save it as a PNG.

    Visual encoding:
        Node colour   → role (core, admin, faculty, lab, service, virtual)
        Edge colour   → blue  = carries flow | grey  = idle link
        Edge width    → proportional to flow volume
        Edge label    → 'flow / capacity' (Mbps)
        Dashed border → nodes on the SOURCE side of the minimum cut
    """

    # ---- Layout ----
    # Hand-tuned positions that roughly mirror the Göztepe campus geography
    pos = {
        "data_center"    : (0.5,  0.9),
        "rectorate"      : (0.15, 0.65),
        "engineering"    : (0.82, 0.65),
        "science_letters": (0.55, 0.65),
        "library"        : (0.28, 0.42),
        "student_affairs": (0.10, 0.20),
        "student_labs_A" : (0.65, 0.20),
        "student_labs_B" : (0.90, 0.20),
        "health_center"  : (0.40, 0.20),
        "super_sink"     : (0.75, 0.02),
    }

    # ---- Node colours by type ----
    color_map = {
        "core"   : "#E74C3C",   # red    — data center
        "admin"  : "#3498DB",   # blue   — administrative buildings
        "faculty": "#2ECC71",   # green  — faculty buildings
        "lab"    : "#9B59B6",   # purple — student labs
        "service": "#F39C12",   # orange — service buildings
        "virtual": "#BDC3C7",   # grey   — super-sink
    }
    node_colors = [color_map.get(G.nodes[n].get("node_type", "service"), "#BDC3C7") for n in G.nodes]

    # ---- Edge styling ----
    # For bidirectional edges, only one label per physical link is drawn
    # (the direction carrying flow, or forward if both zero).
    edge_colors, edge_widths = [], []
    edge_labels   = {}   # (u,v) -> label string
    label_pos_map = {}   # (u,v) -> label_pos scalar
    seen_pairs    = set()

    for u, v in G.edges():
        flow = flow_dict.get(u, {}).get(v, 0)
        cap  = G[u][v]["capacity"]
        rev_flow = flow_dict.get(v, {}).get(u, 0)

        if flow > 0:
            edge_colors.append("#2980B9")
            edge_widths.append(1.5 + 4 * flow / max(cap, 1))
        else:
            edge_colors.append("#555555")
            edge_widths.append(0.9)

        if cap >= float("inf"):
            continue

        pair = tuple(sorted([u, v]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        # Label the direction that carries more flow
        if rev_flow > flow and G.has_edge(v, u):
            lu, lv  = v, u
            lflow   = int(rev_flow)
            lcap    = G[v][u]["capacity"]
        else:
            lu, lv  = u, v
            lflow   = int(flow)
            lcap    = cap

        edge_labels[(lu, lv)]   = f"{lflow}/{lcap}"
        label_pos_map[(lu, lv)] = 0.35   # shift toward source to avoid midpoint clutter

    # ---- Draw ----
    fig, ax = plt.subplots(figsize=(16, 11))
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")
    ax.set_title(
        "Marmara University Göztepe Campus\n"
        "Fiber-Optic Network — Maximum Flow Analysis",
        fontsize=15, fontweight="bold", pad=18, color="#FFFFFF"
    )

    nx.draw_networkx_nodes(G, pos, ax=ax,
                           node_color=node_colors, node_size=1600, alpha=0.95)
    nx.draw_networkx_labels(G, pos, ax=ax,
                            font_size=7.5, font_weight="bold", font_color="white")
    nx.draw_networkx_edges(G, pos, ax=ax,
                           edge_color=edge_colors, width=edge_widths,
                           arrows=True, arrowsize=18,
                           connectionstyle="arc3,rad=0.08",
                           min_source_margin=22, min_target_margin=22)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                 font_size=6.5, font_color="#FFFFFF",
                                 label_pos=0.35,
                                 bbox=dict(boxstyle="round,pad=0.15",
                                           fc="#1a1a1a", ec="none", alpha=0.85))

    # ---- Highlight minimum-cut boundary (dashed box around source side) ----
    cut_nodes = [n for n in reachable if n in pos]
    xs = [pos[n][0] for n in cut_nodes]
    ys = [pos[n][1] for n in cut_nodes]
    if xs and ys:
        ax.add_patch(mpatches.FancyBboxPatch(
            (min(xs) - 0.07, min(ys) - 0.06),
            max(xs) - min(xs) + 0.14,
            max(ys) - min(ys) + 0.12,
            boxstyle="round,pad=0.01",
            linewidth=2.2, linestyle="--",
            edgecolor="#FF4444", facecolor="none",
            label="Source side of min-cut"
        ))

    # ---- Legend ----
    legend_handles = [
        mpatches.Patch(color="#E74C3C", label="Core (Data Center)"),
        mpatches.Patch(color="#3498DB", label="Administrative"),
        mpatches.Patch(color="#2ECC71", label="Faculty"),
        mpatches.Patch(color="#9B59B6", label="Student Labs"),
        mpatches.Patch(color="#F39C12", label="Service"),
        mpatches.Patch(color="#BDC3C7", label="Virtual / Super-Sink"),
        mpatches.Patch(color="#2980B9", label="Active flow link"),
        mpatches.Patch(color="#444444", label="Idle link"),
        mpatches.Patch(facecolor="none", edgecolor="#FF4444",
                       linestyle="--", linewidth=2, label="Min-cut boundary"),
    ]
    legend = ax.legend(handles=legend_handles, loc="lower left",
                       fontsize=8.5, framealpha=0.85, title="Legend",
                       title_fontsize=9, facecolor="#1a1a1a", edgecolor="#444444",
                       labelcolor="white")
    legend.get_title().set_color("white")

    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="#000000")
    plt.close()
    print(f"[INFO] Visualisation saved → {output_path}")


# ---------------------------------------------------------------------------
# 6.  Write human-readable results
# ---------------------------------------------------------------------------
def write_results(flow_value: float, flow_dict: dict,
                  G: nx.DiGraph, reachable: set, non_reachable: set,
                  source: str, sink: str, output_path: str):
    """
    Persist the solver output to a plain-text file.
    The file is formatted for easy inclusion in an academic report.
    """
    lines = []
    sep   = "=" * 70

    lines += [
        sep,
        "MARMARA UNIVERSITY — GÖZTEPE CAMPUS FIBER-OPTIC NETWORK",
        "Maximum Flow Analysis — Solution Output",
        sep, "",
        f"  Source node  : {source}",
        f"  Sink node    : {sink} (aggregates student_labs_A + student_labs_B)",
        f"  Algorithm    : Edmonds-Karp (BFS-based Ford-Fulkerson)",
        "",
        f"  *** MAXIMUM ACHIEVABLE THROUGHPUT : {int(flow_value):,} Mbps ***",
        "",
        sep,
        "FLOW ALLOCATION PER DIRECTED EDGE  (flow / capacity in Mbps)",
        sep,
    ]

    # Sort for readability; exclude super_sink virtual arcs
    for u in sorted(flow_dict.keys()):
        for v, flow in sorted(flow_dict[u].items()):
            if v == "super_sink" or u == "super_sink":
                continue
            cap = G[u][v].get("capacity", float("inf"))
            if cap == float("inf"):
                continue
            util = (flow / cap * 100) if cap > 0 else 0
            status = "SATURATED" if flow >= cap else "available"
            lines.append(
                f"  {u:<22} → {v:<22}  {int(flow):>6} / {int(cap):<6} Mbps"
                f"  ({util:5.1f}%)  [{status}]"
            )

    lines += [
        "",
        sep,
        "MINIMUM CUT — BOTTLENECK IDENTIFICATION",
        sep,
        f"  Min-cut value : {int(flow_value):,} Mbps  (= max flow, by theorem)",
        "",
        "  Source-side nodes  (upgrade these links to increase throughput):",
    ]
    for n in sorted(reachable):
        if n != "super_sink":
            lines.append(f"    • {n}")

    lines += [
        "",
        "  Sink-side nodes:",
    ]
    for n in sorted(non_reachable):
        if n != "super_sink":
            lines.append(f"    • {n}")

    # Identify the actual bottleneck edges (crossing the cut)
    lines += ["", "  Bottleneck edges (crossing the min-cut):"]
    bottlenecks = []
    for u in reachable:
        for v in G.successors(u):
            if v in non_reachable and G[u][v].get("capacity", float("inf")) < float("inf"):
                bottlenecks.append((u, v, G[u][v]["capacity"]))
    for u, v, cap in sorted(bottlenecks, key=lambda x: x[2]):
        lines.append(f"    ✦ {u}  →  {v}   (capacity: {cap:,} Mbps)")

    lines += [
        "",
        sep,
        "MANAGERIAL RECOMMENDATION",
        sep,
        "  Upgrading the bottleneck link(s) identified above will directly",
        "  increase the maximum deliverable throughput to student labs.",
        "  Priority 1: Saturated edges crossing the min-cut.",
        "  Priority 2: Links with utilisation > 80% (pre-bottleneck risk).",
        sep,
    ]

    report = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[INFO] Results saved → {output_path}")
    print("\n" + report)


# ---------------------------------------------------------------------------
# 7.  Main entry point
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("  MIS Network Optimization — Marmara University")
    print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Step 1 · Load the campus topology from CSV
    # ------------------------------------------------------------------
    G = load_network(DATA_FILE)

    # ------------------------------------------------------------------
    # Step 2 · Define source and aggregated sink
    #   SOURCE : data_center (all campus internet traffic originates here)
    #   SINKS  : student_labs_A and student_labs_B (primary end-users)
    #   We merge both lab nodes into a virtual super_sink so NetworkX can
    #   apply single-source / single-sink max-flow.
    # ------------------------------------------------------------------
    SOURCE     = "data_center"
    SINK_NODES = ["student_labs_A", "student_labs_B"]
    SUPER_SINK = "super_sink"

    G = add_super_sink(G, SINK_NODES, SUPER_SINK)

    # ------------------------------------------------------------------
    # Step 3 · Run the Maximum Flow solver
    # ------------------------------------------------------------------
    flow_value, flow_dict = solve_max_flow(G, SOURCE, SUPER_SINK)
    print(f"\n[RESULT] Maximum flow from '{SOURCE}' to '{SUPER_SINK}': "
          f"{int(flow_value):,} Mbps\n")

    # ------------------------------------------------------------------
    # Step 4 · Find minimum cut (bottleneck identification)
    # ------------------------------------------------------------------
    cut_value, reachable, non_reachable = find_min_cut(G, SOURCE, SUPER_SINK)

    # ------------------------------------------------------------------
    # Step 5 · Visualise and save results
    # ------------------------------------------------------------------
    visualise(G, flow_dict, reachable, SOURCE, SUPER_SINK, VIZ_FILE)
    write_results(flow_value, flow_dict, G, reachable, non_reachable,
                  SOURCE, SUPER_SINK, OUTPUT_FILE)


if __name__ == "__main__":
    main()
