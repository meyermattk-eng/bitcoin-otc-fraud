"""
Produces two output artifacts in output/:
  fraud_cliques.csv   -- one row per clique, all scores, member list
  fraud_report.html   -- interactive force-directed graph (pyvis) of the
                         top N cliques + a sortable summary table
"""

import csv
from pathlib import Path
from typing import List

import networkx as nx
from pyvis.network import Network

from clique_analysis import CliqueResult
from config import OUTPUT_DIR, TOP_N_VISUAL

CSV_PATH = Path(OUTPUT_DIR) / "fraud_cliques.csv"
HTML_PATH = Path(OUTPUT_DIR) / "fraud_report.html"

CSV_FIELDS = [
    "rank",
    "size",
    "suspicion_score",
    "isolation_score",
    "burst_score",
    "homogeneity_score",
    "mean_rating",
    "timestamp_std_days",
    "internal_edges",
    "external_edges",
    "members",
]

_PALETTE = [
    "#e63946", "#e76f51", "#f4a261", "#e9c46a",
    "#a8dadc", "#457b9d", "#1d3557", "#6a4c93",
    "#2d6a4f", "#52b788",
]


def write_csv(results: List[CliqueResult]) -> None:
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for rank, r in enumerate(results, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "size": r.size,
                    "suspicion_score": r.suspicion_score,
                    "isolation_score": r.isolation_score,
                    "burst_score": r.burst_score,
                    "homogeneity_score": r.homogeneity_score,
                    "mean_rating": r.mean_rating,
                    "timestamp_std_days": r.timestamp_std_days,
                    "internal_edges": r.internal_edges,
                    "external_edges": r.external_edges,
                    "members": "|".join(str(m) for m in r.members),
                }
            )
    print(f"[report]   CSV  -> {CSV_PATH}  ({len(results):,} cliques)")


def write_html(results: List[CliqueResult], trust_graph: nx.Graph) -> None:
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    top = results[:TOP_N_VISUAL]

    net = Network(
        height="620px",
        width="100%",
        bgcolor="#1a1a2e",
        font_color="#e0e0e0",
        notebook=False,
        directed=False,
    )
    net.set_options("""
    {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 200 }
      },
      "edges": {
        "smooth": { "type": "continuous" },
        "color": { "opacity": 0.6 }
      },
      "interaction": { "hover": true, "tooltipDelay": 100 }
    }
    """)

    node_clique_map: dict[int, int] = {}
    for rank, r in enumerate(top):
        for member in r.members:
            if member not in node_clique_map:
                node_clique_map[member] = rank

    for node_id, clique_rank in node_clique_map.items():
        colour = _PALETTE[clique_rank % len(_PALETTE)]
        r = top[clique_rank]
        tooltip = (
            f"Node {node_id}<br>"
            f"Top clique rank: #{clique_rank + 1}<br>"
            f"Suspicion: {r.suspicion_score:.4f}<br>"
            f"Clique size: {r.size}"
        )
        net.add_node(
            node_id,
            label=str(node_id),
            color=colour,
            title=tooltip,
            size=12 + r.size * 2,
        )

    seen_edges: set[tuple] = set()
    for rank, r in enumerate(top):
        colour = _PALETTE[rank % len(_PALETTE)]
        members = r.members
        for i, u in enumerate(members):
            for v in members[i + 1:]:
                key = (min(u, v), max(u, v))
                if key not in seen_edges:
                    seen_edges.add(key)
                    w = trust_graph[u][v]["weight"] if trust_graph.has_edge(u, v) else 0
                    net.add_edge(
                        u, v,
                        color=colour,
                        title=f"Mean rating: {w:.1f}",
                        width=1 + (w - 8) * 0.5,
                    )

    net.save_graph(str(HTML_PATH))
    _inject_table(results)
    print(f"[report]   HTML -> {HTML_PATH}  (top {len(top)} cliques visualised)")


def _inject_table(results: List[CliqueResult]) -> None:
    """Append a sortable summary table to the pyvis-generated HTML file."""
    rows = []
    for rank, r in enumerate(results, start=1):
        member_str = ", ".join(str(m) for m in r.members)
        rows.append(
            f"<tr>"
            f"<td>{rank}</td>"
            f"<td>{r.size}</td>"
            f"<td>{r.suspicion_score:.4f}</td>"
            f"<td>{r.isolation_score:.4f}</td>"
            f"<td>{r.burst_score:.4f}</td>"
            f"<td>{r.homogeneity_score:.4f}</td>"
            f"<td>{r.mean_rating:.2f}</td>"
            f"<td>{r.timestamp_std_days:.1f}</td>"
            f"<td>{r.external_edges}</td>"
            f"<td style='font-size:0.75em'>{member_str}</td>"
            f"</tr>"
        )

    table_html = f"""
<style>
  body {{ background: #1a1a2e; color: #e0e0e0; font-family: sans-serif; margin: 0; }}
  h1, h2 {{ text-align: center; color: #e63946; }}
  p.subtitle {{ text-align: center; color: #a0a0c0; font-size: 0.9em; margin-top: -0.5em; }}
  #table-container {{ max-width: 1200px; margin: 0 auto; padding: 1em; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85em; }}
  th, td {{ border: 1px solid #333; padding: 6px 10px; text-align: right; }}
  th {{ background: #16213e; color: #e63946; cursor: pointer; user-select: none; }}
  th:last-child, td:last-child {{ text-align: left; }}
  tr:nth-child(even) {{ background: #16213e; }}
  tr:hover {{ background: #0f3460; }}
  .sort-asc::after  {{ content: " \\25b2"; }}
  .sort-desc::after {{ content: " \\25bc"; }}
</style>
<h1>Bitcoin OTC -- Suspicious Clique Report</h1>
<p class="subtitle">
  Mutual-trust cliques (rating &gt;= {results[0].mean_rating if results else 5}, size &gt;= 5) ranked by composite suspicion score.
  Top {TOP_N_VISUAL} are shown in the network above.
</p>
<div id="table-container">
<table id="clique-table">
  <thead>
    <tr>
      <th>Rank</th><th>Size</th><th>Suspicion</th>
      <th>Isolation</th><th>Burst</th><th>Homogeneity</th>
      <th>Mean Rating</th><th>TS Std (days)</th>
      <th>Ext. Edges</th><th>Members</th>
    </tr>
  </thead>
  <tbody>
    {"".join(rows)}
  </tbody>
</table>
</div>
<script>
(function() {{
  const table = document.getElementById('clique-table');
  const headers = table.querySelectorAll('th');
  let sortCol = -1, sortAsc = true;

  headers.forEach((th, idx) => {{
    th.addEventListener('click', () => {{
      sortAsc = (sortCol === idx) ? !sortAsc : true;
      sortCol = idx;
      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');

      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {{
        const av = a.cells[idx].textContent.trim();
        const bv = b.cells[idx].textContent.trim();
        const an = parseFloat(av), bn = parseFloat(bv);
        const cmp = isNaN(an) ? av.localeCompare(bv) : an - bn;
        return sortAsc ? cmp : -cmp;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
}})();
</script>
"""

    html = Path(HTML_PATH).read_text(encoding="utf-8")
    html = html.replace("</body>", table_html + "\n</body>")
    Path(HTML_PATH).write_text(html, encoding="utf-8")
