"""Light botanical knowledge-graph visualization for PhytoGraph Research Atlas.

Read-only Neo4j retrieval. Compatible with the original build_html_graph()
API, and adds an in-memory build_graph_html() API for cloud-safe Streamlit.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from dotenv import load_dotenv
from pyvis.network import Network

from database import _secret, get_driver

load_dotenv()
DATABASE = _secret("NEO4J_DATABASE", "neo4j")

COLORS = {
    "Plant": {"background": "#74B18A", "border": "#4C946C", "highlight": "#4C946C"},
    "Compound": {"background": "#E0BA80", "border": "#B58A4F", "highlight": "#B58A4F"},
    "Target": {"background": "#9BB8D5", "border": "#6C91B9", "highlight": "#6C91B9"},
    "Pathogen": {"background": "#DDA7AA", "border": "#C77E84", "highlight": "#C77E84"},
}

NODE_ID_FIELDS = {
    "Plant": "Plant_ID",
    "Compound": "Compound_ID",
    "Target": "Target_ID",
    "Pathogen": "Pathogen_ID",
}
NODE_NAME_FIELDS = {
    "Plant": "Scientific_Name",
    "Compound": "Compound_Name",
    "Target": "Target_Name",
    "Pathogen": "Organism",
}


def get_compound_graph(compound_id: str, max_plants: int = 20):
    """Read a compound-centered neighborhood from Neo4j without mutation."""
    query = """
    MATCH (c:Compound {Compound_ID: $compound_id})
    CALL (c) {
        OPTIONAL MATCH (p:Plant)-[pc:CONTAINS_COMPOUND]->(c)
        WITH p, pc WHERE p IS NOT NULL
        ORDER BY p.Scientific_Name
        LIMIT $max_plants
        RETURN collect({node: properties(p), rel: properties(pc)}) AS plants
    }
    CALL (c) {
        OPTIONAL MATCH (c)-[ct:INTERACTS_WITH_TARGET]->(t:Target)
        WITH t, ct WHERE t IS NOT NULL
        RETURN collect({node: properties(t), rel: properties(ct)}) AS targets
    }
    CALL (c) {
        OPTIONAL MATCH (c)-[cp:ACTS_AGAINST_PATHOGEN]->(g:Pathogen)
        WITH g, cp WHERE g IS NOT NULL
        RETURN collect({node: properties(g), rel: properties(cp)}) AS pathogens
    }
    RETURN properties(c) AS compound, plants, targets, pathogens
    """
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            record = session.run(
                query, compound_id=compound_id, max_plants=int(max_plants)
            ).single()
            return dict(record) if record is not None else None


def _node_style(kind: str, *, center: bool = False) -> dict:
    palette = COLORS[kind]
    return {
        "background": palette["background"],
        "border": palette["border"],
        "highlight": {
            "background": "#F5F8EE" if center else palette["background"],
            "border": palette["highlight"],
        },
        "hover": {
            "background": palette["background"],
            "border": palette["highlight"],
        },
    }


def _tooltip(node_type: str, node_name: str, node_id: str) -> str:
    return (
        '<div style="font-family:Arial,sans-serif;font-size:12px;line-height:1.7">'
        f'<b>{escape(node_type)}</b><br>{escape(node_name)}<br>'
        f'ID: {escape(str(node_id))}</div>'
    )


def _edge_tooltip(edge_type: str, rel: dict) -> str:
    fields = (
        ("Relationship", edge_type),
        ("Link ID", rel.get("Link_ID")),
        ("Evidence", rel.get("Evidence_Type")),
        ("Activity", rel.get("Activity_Type")),
        ("Category", rel.get("Biological_Evidence_Category")),
        ("Finding", rel.get("Finding")),
        ("Source", rel.get("Source_URL")),
    )
    html = ''.join(
        f'<div><strong>{escape(label)}:</strong> {escape(str(value) if value is not None else "Not recorded")}</div>'
        for label, value in fields
    )
    return '<div style="max-width:380px;font-family:Arial,sans-serif;font-size:12px;line-height:1.65">' + html + '</div>'


def _legend_html(counts: dict) -> str:
    dots = (
        ("Plant", "Plants"),
        ("Compound", "Compounds"),
        ("Target", "Targets"),
        ("Pathogen", "Pathogens"),
    )
    entries = ''.join(
        '<span class="pg-legend-line">'
        f'<span class="pg-legend-circle" style="background:{COLORS[k]["background"]};border-color:{COLORS[k]["border"]}"></span>'
        f'{escape(label)} <small>{counts.get(k, 0)}</small></span>'
        for k, label in dots
    )
    return f'<aside class="pg-legend"><strong>NETWORK LEGEND</strong>{entries}</aside>'


def _wrap_html(html: str, counts: dict) -> str:
    css = """
    <style>
      html,body { margin:0!important; padding:0!important; background:#FAFCF9!important; color:#1F3F31; }
      body { position:relative; font-family:Arial,sans-serif; }
      #mynetwork { border:1px solid #DEE9DC!important; border-radius:16px!important;
        background: radial-gradient(circle at 50% 50%,#FFF,#F9FCF8)!important;
        overflow:hidden!important; }
      .pg-legend { position:absolute; top:18px; left:20px; z-index:5; display:flex; gap:11px; flex-direction:column;
        min-width:125px; padding:15px 15px; border:1px solid #E1EAE0; border-radius:13px;
        background:rgba(255,255,255,.95); box-shadow:0 6px 25px rgba(29,73,46,.06); pointer-events:none; }
      .pg-legend strong { color:#627D6D; letter-spacing:.12em; font-size:9px; margin-bottom:4px; }
      .pg-legend-line { display:flex; align-items:center; gap:8px; color:#476253; font-size:11px; font-weight:600; }
      .pg-legend-line small { margin-left:auto; color:#9BB0A2; font-size:10px; }
      .pg-legend-circle { display:inline-block; width:10px; height:10px; border-radius:50%; border:2px solid; }
      .pg-hint { position:absolute; z-index:5; bottom:16px; right:19px; border-radius:100px;
        background:rgba(255,255,255,.94); border:1px solid #E1EAE0; color:#718677;
        padding:8px 12px; font-size:10px; pointer-events:none; }
      .vis-tooltip { border:1px solid #D5E4D7!important; border-radius:11px!important; background:#FFFFFF!important;
        color:#284D39!important; box-shadow:0 12px 30px rgba(28,64,40,.09)!important; padding:12px!important;
        max-width:400px; white-space:normal!important; overflow-wrap:anywhere; }
      @media(max-width:600px){ .pg-legend { top:9px;left:9px; padding:10px; min-width:105px; }
        .pg-hint { left:9px;right:auto;bottom:9px; } }
    </style>
    """
    overlay = _legend_html(counts) + '<div class="pg-hint">Scroll to zoom · drag to explore · hover for evidence</div>'
    return html.replace('</head>', css + '</head>', 1).replace('<body>', '<body>' + overlay, 1)


def build_graph_html(compound_id: str, max_plants: int = 20) -> str | None:
    """Return a self-contained HTML graph for st.components.v1.html."""
    result = get_compound_graph(compound_id, max_plants=max_plants)
    if result is None:
        return None

    net = Network(
        height="615px", width="100%", bgcolor="#FAFCF9",
        font_color="#2F5040", directed=True, cdn_resources="in_line",
    )

    center = result.get("compound") or {}
    center_id = f'Compound:{center.get("Compound_ID", compound_id)}'
    name = str(center.get("Compound_Name") or compound_id)
    net.add_node(
        center_id,
        label=name[:26] + ("..." if len(name) > 26 else ""),
        title=_tooltip("Compound", name, str(compound_id)),
        shape="dot", size=34, color=_node_style("Compound", center=True),
        borderWidth=3,
        font={"color":"#234936","size":17,"face":"Arial","bold":True,"strokeWidth":3,"strokeColor":"#FAFCF9"},
    )

    sections = (
        ("plants", "Plant", "CONTAINS_COMPOUND", True),
        ("targets", "Target", "INTERACTS_WITH_TARGET", False),
        ("pathogens", "Pathogen", "ACTS_AGAINST_PATHOGEN", False),
    )
    counts = {"Compound": 1, "Plant": 0, "Target": 0, "Pathogen": 0}
    node_seen = {center_id}
    edge_seen = set()

    for section, kind, edge_type, incoming in sections:
        for item in result.get(section) or []:
            if not isinstance(item, dict):
                continue
            node = item.get("node") or {}
            rel = item.get("rel") or {}
            if not isinstance(node, dict) or not isinstance(rel, dict):
                continue
            node_id = node.get(NODE_ID_FIELDS[kind])
            if node_id is None:
                continue
            graph_id = f"{kind}:{node_id}"
            node_name = str(node.get(NODE_NAME_FIELDS[kind]) or node_id)
            if graph_id not in node_seen:
                node_seen.add(graph_id)
                counts[kind] += 1
                label = node_name[:23] + ("..." if len(node_name) > 23 else "")
                net.add_node(
                    graph_id, label=label, title=_tooltip(kind, node_name, str(node_id)),
                    shape="dot", size=19 if kind != "Plant" else 17,
                    color=_node_style(kind), borderWidth=2,
                    font={"color":"#456052","size":12,"face":"Arial","strokeWidth":3,"strokeColor":"#FAFCF9"},
                )
            source, target = (graph_id, center_id) if incoming else (center_id, graph_id)
            key = (source, target, str(rel.get("Link_ID") or ""), edge_type)
            if key in edge_seen:
                continue
            edge_seen.add(key)
            net.add_edge(
                source, target, title=_edge_tooltip(edge_type, rel), arrows="to",
                color={"color":"#B9CFC0","highlight":"#56836E","hover":"#56836E"},
                width=1.35,
            )

    net.set_options(r'''
    {
      "interaction": {
        "hover": true, "tooltipDelay": 160, "dragNodes": true,
        "hideEdgesOnDrag": false, "zoomView": true, "dragView": true,
        "navigationButtons": true, "keyboard": {"enabled": true}
      },
      "nodes": {"shape":"dot","font":{"color":"#2F5040","size":12,"face":"Arial"}},
      "edges": {
        "smooth":{"enabled":true,"type":"continuous","roundness":0.15},
        "selectionWidth":2
      },
      "physics": {
        "enabled":true,"solver":"barnesHut",
        "barnesHut":{"gravitationalConstant":-4500,"centralGravity":0.14,"springLength":155,"springConstant":0.04,"damping":0.14,"avoidOverlap":0.45},
        "stabilization":{"enabled":true,"iterations":180,"updateInterval":25}
      }
    }
    ''')
    return _wrap_html(net.generate_html(), counts)


def build_html_graph(compound_id: str, output_file=None, max_plants: int = 20):
    """Backward-compatible file-based graph API (previous Streamlit version)."""
    html = build_graph_html(compound_id=compound_id, max_plants=max_plants)
    if html is None:
        return None
    path = Path(output_file or f"outputs/graph_{compound_id}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    path = build_html_graph("CMP011", output_file="outputs/graph_CMP011.html")
    print(f"Graph HTML: {path}" if path else "Compound not found in Neo4j")
