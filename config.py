"""
Tunables for the Bitcoin OTC fraud clique analysis.
Edit these to explore different detection sensitivities.
"""

# Minimum edge weight (trust rating 1–10) to include in the positive-trust graph.
# An undirected edge (u,v) is kept if EITHER u->v or v->u meets this threshold.
# Rating >= 5 gives enough density for size-5+ cliques while excluding lukewarm
# ratings.  Raise to 7 or 8 to focus on the most aggressively high endorsements
# (note: the graph becomes very sparse above 7 -- fewer but higher-confidence hits).
MIN_RATING = 5

# Only report cliques at least this large. Pairs and triples are too common to be
# meaningful; size 5+ suggests a coordinated mutual-vouching ring.
MIN_CLIQUE_SIZE = 5

# Top N cliques (by suspicion score) to render in the HTML network visualization.
TOP_N_VISUAL = 20

# Weights for the composite suspicion score (must sum to 1.0).
WEIGHT_ISOLATION = 0.40
WEIGHT_BURST = 0.35
WEIGHT_HOMOGENEITY = 0.25

# Dataset
DATASET_URL = "https://snap.stanford.edu/data/soc-sign-bitcoinotc.csv.gz"
DATA_DIR = "data"
OUTPUT_DIR = "output"
