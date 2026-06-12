"""
Finds all maximal cliques in the trust graph and scores each one
on three fraud-indicative heuristics, producing a composite suspicion score.

Heuristics
----------
isolation_score
    Fraction of possible external edges that are actually absent.
    A clique whose members only trust each other (and barely interact with
    the rest of the graph) scores near 1.0.

    isolation = 1 - (external_edges / max_possible_external_edges)
    where max_possible_external_edges = k * (N - k),
    k = clique size, N = total nodes in trust graph.

burst_score
    How temporally concentrated the mutual ratings are.
    We compute the standard deviation of all timestamps within the clique
    (in days), then map it to [0, 1] via an exponential decay.
    A burst of ratings in a short window scores near 1.0.

    burst = exp(-std_days / BURST_HALFLIFE_DAYS)

homogeneity_score
    Mean edge weight within the clique, normalised to [0, 1].
    All-10 cliques score 1.0; a clique with mean weight 8 scores ~0.78.
    (Weights reflect the 1-10 scale.)

suspicion_score
    Weighted sum of the three components (weights in config.py).
"""

import statistics
from dataclasses import dataclass
from math import exp
from typing import List

import networkx as nx

from config import (
    MIN_CLIQUE_SIZE,
    WEIGHT_BURST,
    WEIGHT_HOMOGENEITY,
    WEIGHT_ISOLATION,
)

# A burst window of 30 days: ratings spread over 30 days score ~0.37,
# over 7 days ~0.79, same day ~1.0.
BURST_HALFLIFE_DAYS = 30.0
SECONDS_PER_DAY = 86_400


@dataclass
class CliqueResult:
    members: List[int]
    size: int
    mean_rating: float
    isolation_score: float
    burst_score: float
    homogeneity_score: float
    suspicion_score: float
    timestamp_std_days: float
    internal_edges: int
    external_edges: int


def analyse(trust_graph: nx.Graph) -> List[CliqueResult]:
    """Return CliqueResult list sorted descending by suspicion_score."""
    print("[cliques]  Finding maximal cliques ...")
    cliques = [
        c for c in nx.find_cliques(trust_graph) if len(c) >= MIN_CLIQUE_SIZE
    ]
    print(f"[cliques]  Found {len(cliques):,} maximal cliques of size >= {MIN_CLIQUE_SIZE}")

    total_nodes = trust_graph.number_of_nodes()
    results = [_score_clique(trust_graph, members, total_nodes) for members in cliques]
    results.sort(key=lambda r: r.suspicion_score, reverse=True)
    return results


def _score_clique(
    g: nx.Graph, members: List[int], total_nodes: int
) -> CliqueResult:
    k = len(members)
    member_set = set(members)

    ratings = []
    timestamps_flat = []
    for i, u in enumerate(members):
        for v in members[i + 1:]:
            data = g[u][v]
            ratings.append(data["weight"])
            timestamps_flat.extend(data["timestamps"])

    internal_edges = len(ratings)
    mean_rating = statistics.mean(ratings) if ratings else 0.0

    external_edges = sum(
        1
        for u in members
        for v in g.neighbors(u)
        if v not in member_set
    )
    max_external = k * (total_nodes - k)
    isolation = 1.0 - (external_edges / max_external) if max_external > 0 else 1.0

    if len(timestamps_flat) > 1:
        std_seconds = statistics.stdev(timestamps_flat)
        std_days = std_seconds / SECONDS_PER_DAY
    else:
        std_days = 0.0
    burst = exp(-std_days / BURST_HALFLIFE_DAYS)

    homogeneity = (mean_rating - 1) / 9.0

    suspicion = (
        WEIGHT_ISOLATION * isolation
        + WEIGHT_BURST * burst
        + WEIGHT_HOMOGENEITY * homogeneity
    )

    return CliqueResult(
        members=sorted(members),
        size=k,
        mean_rating=round(mean_rating, 3),
        isolation_score=round(isolation, 4),
        burst_score=round(burst, 4),
        homogeneity_score=round(homogeneity, 4),
        suspicion_score=round(suspicion, 4),
        timestamp_std_days=round(std_days, 2),
        internal_edges=internal_edges,
        external_edges=external_edges,
    )
