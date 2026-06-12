"""
Parses the raw Bitcoin OTC CSV and builds two NetworkX graphs:
  - signed_graph   : full directed graph with all ratings and timestamps
  - trust_graph    : undirected graph of high-trust edges
                     An undirected edge (u, v) exists if either u->v or v->u
                     (or both) has rating >= MIN_RATING.  Requiring strict
                     reciprocity would reduce the graph to ~200 edges at
                     threshold 8 -- too sparse for meaningful clique detection.
                     The "any direction" model still captures coordinated
                     endorsement rings: if every pair in a group has rated
                     each other highly in at least one direction, the group
                     forms a dense mutual-vouching cluster.

Edge attributes on trust_graph:
  weight     : max of the directional ratings for the pair
  timestamps : all timestamps for edges between u and v
"""

import csv
from pathlib import Path

import networkx as nx

from config import MIN_RATING


def load(csv_path: Path) -> tuple[nx.DiGraph, nx.Graph]:
    """Return (signed_graph, trust_graph)."""
    signed = nx.DiGraph()

    with open(csv_path, newline="") as f:
        for row in csv.reader(f):
            if row[0].startswith("#"):
                continue
            src, tgt, rating, ts = int(row[0]), int(row[1]), int(row[2]), int(float(row[3]))
            signed.add_edge(src, tgt, rating=rating, timestamp=ts)

    trust = _build_trust_graph(signed)
    print(
        f"[graph]    Signed graph  : {signed.number_of_nodes():,} nodes, "
        f"{signed.number_of_edges():,} edges"
    )
    print(
        f"[graph]    Trust graph   : {trust.number_of_nodes():,} nodes, "
        f"{trust.number_of_edges():,} edges  (any-direction rating >= {MIN_RATING})"
    )
    return signed, trust


def _build_trust_graph(signed: nx.DiGraph) -> nx.Graph:
    """
    Undirected projection: add an edge (u,v) if either u->v or v->u
    has rating >= MIN_RATING.  Edge weight = max rating seen; timestamps
    collect all rating events between the pair.
    """
    trust = nx.Graph()

    for u, v, data in signed.edges(data=True):
        if data["rating"] < MIN_RATING:
            continue
        if trust.has_edge(u, v):
            existing = trust[u][v]
            existing["weight"] = max(existing["weight"], data["rating"])
            existing["timestamps"].append(data["timestamp"])
        else:
            trust.add_edge(u, v, weight=float(data["rating"]), timestamps=[data["timestamp"]])

    return trust
