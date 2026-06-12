"""
Bitcoin OTC Fraud Clique Detector
----------------------------------
Identifies suspicious mutual-trust cliques in the Bitcoin OTC network
and outputs a ranked CSV and an interactive HTML report.

Usage:
    python main.py
"""

import time

import download
import graph_builder
import clique_analysis
import report
from config import MIN_CLIQUE_SIZE, MIN_RATING


def main() -> None:
    t0 = time.perf_counter()
    print("=" * 60)
    print("  Bitcoin OTC Fraud Clique Detector")
    print(f"  min_rating={MIN_RATING}  min_clique_size={MIN_CLIQUE_SIZE}")
    print("=" * 60)

    csv_path = download.fetch()
    signed_graph, trust_graph = graph_builder.load(csv_path)
    results = clique_analysis.analyse(trust_graph)

    if not results:
        print(
            f"\n  No cliques of size >= {MIN_CLIQUE_SIZE} found at rating >= {MIN_RATING}.\n"
            "  Try lowering MIN_RATING or MIN_CLIQUE_SIZE in config.py.\n"
        )
        return

    report.write_csv(results)
    report.write_html(results, trust_graph)

    elapsed = time.perf_counter() - t0
    print(f"\n[done]     {len(results):,} suspicious cliques ranked in {elapsed:.1f}s")
    print(f"           Top suspicion score: {results[0].suspicion_score:.4f}")
    print(f"           Top clique members : {results[0].members}")


if __name__ == "__main__":
    main()
