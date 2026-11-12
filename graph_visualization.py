"""PhytoGraph network visualizations.

Read-only Neo4j retrieval for compound-centred and full knowledge-graph views.
The original build_html_graph() and build_graph_html() APIs are preserved.
Tooltip content is plain text to avoid raw HTML appearing in vis-network.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Iterable

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
ALLOWED_NODE_TYPES = ("Plant", "Compound", "Target", "Pathogen")


def get_compound_graph(compound_id: str, max_plants: int = 20):
    """Read a compound-centred neighbourhood from Neo4j without mutation."""
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


def get_graph_relationship_types() -> list[str]:
    """Return relationship types present in the four-entity knowledge graph."""
    query = """
    MATCH (a)-[r]->(b)
    WHERE any(label IN labels(a) WHERE label IN $allowed_labels)
      AND any(label IN labels(b) WHERE label IN $allowed_labels)
    RETURN DISTINCT type(r) AS relationship_type
    ORDER BY relationship_type
    """
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            return [
                record["relationship_type"]
                for record in session.run(
                    query, allowed_labels=list(ALLOWED_NODE_TYPES)
                )
            ]


def get_graph_relationship_type_counts() -> dict[str, int]:
    """Return exact relationship counts for the four-entity graph."""
    query = """
    MATCH (a)-[r]->(b)
    WHERE any(label IN labels(a) WHERE label IN $allowed_labels)
      AND any(label IN labels(b) WHERE label IN $allowed_labels)
    RETURN type(r) AS relationship_type, count(r) AS relationship_count
    ORDER BY relationship_type
    """
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            return {
                str(record["relationship_type"]): int(record["relationship_count"])
                for record in session.run(
                    query, allowed_labels=list(ALLOWED_NODE_TYPES)
                )
            }


def get_compound_options() -> list[dict[str, str]]:
    """Return all registered compounds, not only the ranked subset."""
    query = """
    MATCH (c:Compound)
    WHERE c.Compound_ID IS NOT NULL
    RETURN c.Compound_ID AS compound_id,
           coalesce(c.Compound_Name, c.Name, c.name, c.Compound_ID) AS compound_name
    ORDER BY compound_name
    """
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            return [
                {
                    "compound_id": str(record["compound_id"]),
                    "compound_name": str(record["compound_name"] or record["compound_id"]),
                }
                for record in session.run(query)
            ]


def get_full_graph(
    node_types: Iterable[str] | None = None,
    relationship_types: Iterable[str] | None = None,
    max_relationships: int = 10000,
) -> dict:
    """Read selected graph nodes and relationships without changing Neo4j."""
    selected_nodes = [
        kind for kind in (node_types or ALLOWED_NODE_TYPES)
        if kind in ALLOWED_NODE_TYPES
    ]
    if not selected_nodes:
        selected_nodes = list(ALLOWED_NODE_TYPES)
    selected_relationships = list(relationship_types or [])

    node_query = """
    MATCH (n)
    WHERE any(label IN labels(n) WHERE label IN $allowed_labels)
    RETURN labels(n) AS labels,
           properties(n) AS node,
           elementId(n) AS element_id
    """
    edge_query = """
    MATCH (a)-[r]->(b)
    WHERE any(label IN labels(a) WHERE label IN $allowed_labels)
      AND any(label IN labels(b) WHERE label IN $allowed_labels)
      AND (size($relationship_types) = 0 OR type(r) IN $relationship_types)
    RETURN labels(a) AS source_labels,
           properties(a) AS source_node,
           elementId(a) AS source_element_id,
           type(r) AS relationship_type,
           properties(r) AS relationship,
           elementId(r) AS relationship_element_id,
           labels(b) AS target_labels,
           properties(b) AS target_node,
           elementId(b) AS target_element_id
    LIMIT $max_relationships
    """
    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            nodes = [
                dict(record)
                for record in session.run(
                    node_query, allowed_labels=selected_nodes
                )
            ]
            edges = [
                dict(record)
                for record in session.run(
                    edge_query,
                    allowed_labels=selected_nodes,
                    relationship_types=selected_relationships,
                    max_relationships=max(1, int(max_relationships)),
                )
            ]
    return {"nodes": nodes, "edges": edges}


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


def _clean_text(value, max_length: int = 260) -> str:
    """Make database values safe and readable in plain-text tooltips."""
    if value is None or str(value).strip() == "":
        return "Not recorded"
    text = " ".join(str(value).replace("\x00", "").split())
    if len(text) > max_length:
        text = text[: max_length - 1].rstrip() + "…"
    return text


def _tooltip(
    node_type: str,
    node_name: str,
    node_id: str,
    node: dict | None = None,
) -> str:
    """Readable plain-text node details; only show fields relevant to that entity."""
    node = node or {}
    field_map = {
        "Plant": [
            ("Common name", "Common_Name"),
            ("Source", "Source"),
        ],
        "Compound": [
            ("PubChem CID", "PubChem_CID"),
            ("Molecular formula", "Molecular_Formula"),
            ("Molecular weight", "Molecular_Weight"),
            ("Source", "Source"),
        ],
        "Target": [
            ("Gene", "Gene"),
            ("Organism", "Organism"),
            ("Target family", "Target_Family"),
            ("Target role", "Target_Role"),
            ("UniProt ID", "UniProt_ID"),
            ("PDB ID", "PDB_ID"),
            ("Source", "Source"),
        ],
        "Pathogen": [
            ("Resistance phenotype", "Resistance_Phenotype"),
            ("WHO category", "WHO_Category"),
            ("NCBI taxonomy ID", "NCBI_Taxonomy_ID"),
            ("Source", "Source"),
        ],
    }
    parts = [
        f"{node_type}: {_clean_text(node_name, 160)}",
        f"ID: {_clean_text(node_id, 80)}",
    ]
    for label, field in field_map.get(node_type, []):
        value = node.get(field)
        if value is not None and str(value).strip():
            parts.append(f"{label}: {_clean_text(value, 180)}")
    return "  |  ".join(parts)


def _friendly_relationship(edge_type: str, rel: dict | None = None) -> str:
    rel = rel or {}
    specific = (
        rel.get("Activity_Type")
        or rel.get("Relationship_Type")
        or rel.get("Interaction_Type")
    )
    if specific:
        return _clean_text(str(specific).replace("_", " ").title(), 90)

    names = {
        "CONTAINS_COMPOUND": "Plant → compound occurrence",
        "INTERACTS_WITH_TARGET": "Compound → molecular target evidence",
        "ACTS_AGAINST_PATHOGEN": "Compound → pathogen evidence",
        "ASSOCIATED_WITH_TARGET": "Pathogen → resistance-associated target",
    }
    return names.get(edge_type, edge_type.replace("_", " ").title())


def _edge_tooltip(edge_type: str, rel: dict) -> str:
    """Readable relationship details for the evidence fields used in the dataset."""
    source = (
        rel.get("Source_DOI_or_PMID")
        or rel.get("Evidence_Source_URL")
        or rel.get("Source_URL")
        or rel.get("Source")
        or rel.get("DOI")
        or rel.get("PMID")
    )
    fields = [
        ("Relationship", _friendly_relationship(edge_type, rel)),
        ("Relationship type", edge_type.replace("_", " ").title()),
        ("Link ID", rel.get("Link_ID")),
        ("Evidence level", rel.get("Evidence_Level")),
        ("Evidence type", rel.get("Evidence_Type")),
        ("Evidence category", rel.get("Biological_Evidence_Category")),
        ("Evidence audit status", rel.get("Evidence_Audit_Status")),
        ("Interaction type", rel.get("Interaction_Type")),
        ("Activity", rel.get("Activity_Type")),
        ("Mechanism", rel.get("Mechanism")),
        ("Experimental method", rel.get("Experimental_Method")),
        ("Plant part", rel.get("Plant_Part")),
        ("Tested strain", rel.get("Tested_Strain_Context") or rel.get("Strain_Context")),
        ("MIC", " ".join(str(v) for v in (rel.get("MIC"), rel.get("MIC_Unit")) if v)),
        ("Antibiotic / substrate", rel.get("Antibiotic_or_Substrate")),
        ("AMR relevance", rel.get("AMR_Relevance")),
        ("Finding", rel.get("Finding")),
        ("Evidence notes", rel.get("Evidence_Notes")),
        ("Source", source),
    ]
    parts = []
    for label, value in fields:
        if value is not None and str(value).strip():
            parts.append(f"{label}: {_clean_text(value, 240)}")
    return "  |  ".join(parts)


def _legend_html(counts: dict) -> str:
    dots = (
        ("Plant", "Plants"),
        ("Compound", "Compounds"),
        ("Target", "Targets"),
        ("Pathogen", "Pathogens"),
    )
    entries = "".join(
        '<span class="pg-legend-line">'
        f'<span class="pg-legend-circle" style="background:{COLORS[k]["background"]};border-color:{COLORS[k]["border"]}"></span>'
        f'{escape(label)} <small>{counts.get(k, 0)}</small></span>'
        for k, label in dots
    )
    return f'<aside class="pg-legend"><strong>NETWORK LEGEND</strong>{entries}</aside>'


def _wrap_html(html: str, counts: dict, *, full_graph: bool = False) -> str:
    css = """
    <style>
      html,body { margin:0!important; padding:0!important; background:#FAFCF9!important; color:#1F3F31; }
      body { position:relative; font-family:Arial,sans-serif; overflow:hidden; }
      #mynetwork { position:relative; z-index:1; border:1px solid #DEE9DC!important; border-radius:16px!important;
        background:radial-gradient(circle at 50% 50%,#FFF,#F9FCF8)!important;
        overflow:hidden!important; }
      .pg-legend { position:absolute; top:18px; left:20px; z-index:5; display:flex; gap:11px; flex-direction:column;
        min-width:125px; padding:15px; border:1px solid #E1EAE0; border-radius:13px;
        background:rgba(255,255,255,.96); box-shadow:0 6px 25px rgba(29,73,46,.06); pointer-events:none; }
      .pg-legend strong { color:#627D6D; letter-spacing:.12em; font-size:9px; margin-bottom:4px; }
      .pg-legend-line { display:flex; align-items:center; gap:8px; color:#476253; font-size:11px; font-weight:600; }
      .pg-legend-line small { margin-left:auto; color:#789181; font-size:10px; }
      .pg-legend-circle { display:inline-block; width:10px; height:10px; border-radius:50%; border:2px solid; }
      .pg-hint { position:absolute; z-index:5; bottom:42px; right:19px; border-radius:100px;
        background:rgba(255,255,255,.96); border:1px solid #E1EAE0; color:#536F5E;
        padding:8px 12px; font-size:10px; pointer-events:none; }
      .pg-note { position:absolute; z-index:5; bottom:10px; left:19px; max-width:70%;
        border-radius:9px; background:rgba(255,255,255,.94); border:1px solid #E1EAE0;
        color:#718677; padding:7px 10px; font-size:10px; pointer-events:none; }
      .vis-tooltip { border:1px solid #D5E4D7!important; border-radius:11px!important; background:#FFFFFF!important;
        color:#284D39!important; box-shadow:0 12px 30px rgba(28,64,40,.09)!important; padding:12px!important;
        max-width:440px; white-space:normal!important; overflow-wrap:anywhere; }
      .pg-search { position:absolute; z-index:50; top:18px; right:20px; width:min(470px, calc(100% - 180px));
        box-sizing:border-box; padding:12px; border:1px solid #DCE8DD; border-radius:13px;
        background:rgba(255,255,255,.97); box-shadow:0 6px 25px rgba(29,73,46,.08); }
      .pg-search-tools { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
      .pg-search-tools button { border:1px solid #D5E3D7; border-radius:8px; padding:7px 9px;
        background:#F4F8F3; color:#315B43; font-size:10px; font-weight:650; cursor:pointer; }
      .pg-search-tools button:hover { background:#E8F1E7; }
      .pg-search-tools button.pg-primary { background:#285C49; border-color:#285C49; color:#fff; }
      .pg-search-label { display:block; margin:0 0 7px; color:#627D6D; font-size:9px;
        font-weight:700; letter-spacing:.12em; }
      .pg-search-row { display:flex; gap:6px; }
      .pg-search input { min-width:0; flex:1; box-sizing:border-box; border:1px solid #D8E4D9;
        border-radius:8px; padding:8px 9px; color:#284D39; background:#fff; font-size:12px; outline:none; }
      .pg-search input:focus { border-color:#6F9B7D; box-shadow:0 0 0 2px rgba(111,155,125,.13); }
      .pg-search button { border:1px solid #D5E3D7; border-radius:8px; padding:7px 10px;
        background:#F4F8F3; color:#315B43; font-size:11px; font-weight:600; cursor:pointer; }
      .pg-search button:hover { background:#E8F1E7; }
      .pg-search-actions { display:flex; align-items:center; gap:6px; margin-top:6px; }
      .pg-search-status { flex:1; color:#718677; font-size:10px; line-height:1.35; }
      @media(max-width:600px) {
        .pg-legend { top:9px;left:9px;padding:10px;min-width:105px; }
        .pg-search { top:9px;right:9px;width:min(330px, calc(100% - 145px));padding:8px; }
        .pg-search button { padding:7px 8px; }
        .pg-hint { left:9px;right:auto;bottom:42px; }
        .pg-note { left:9px;bottom:8px;max-width:90%; }
      }
    </style>
    """
    hint = (
        "Hover over a connection for its evidence details"
        if full_graph
        else "Scroll to zoom · drag to explore · hover for evidence"
    )
    search_panel = '''
      <div class="pg-search">
        <label class="pg-search-label" for="pg-node-search">FIND & EXPLORE ANY NODE</label>
        <div class="pg-search-row">
          <input id="pg-node-search" type="search" placeholder="Plant, compound, pathogen, target or ID" autocomplete="off">
          <button id="pg-node-find" class="pg-primary" type="button">Find</button>
          <button id="pg-node-next" type="button">Next</button>
        </div>
        <div class="pg-search-tools">
          <button id="pg-node-focus" type="button">Focus selected</button>
          <button id="pg-node-neighbours" type="button">Highlight neighbours</button>
          <button id="pg-node-isolate" type="button">Isolate neighbourhood</button>
          <button id="pg-node-show-all" type="button">Show all</button>
          <button id="pg-node-fit" type="button">Fit graph</button>
        </div>
        <div class="pg-search-actions">
          <span id="pg-search-status" class="pg-search-status" aria-live="polite">Search the loaded graph, then explore its connections.</span>
          <button id="pg-node-clear" type="button">Clear search</button>
        </div>
      </div>
    '''
    search_script = r'''
    <script>
    (function () {
      // Use the explicitly exposed PyVis instance, not an assumed lexical global.
      const network = window.__pgNetwork || window.network;
      const byId = (id) => document.getElementById(id);
      const input = byId("pg-node-search");
      const findButton = byId("pg-node-find");
      const nextButton = byId("pg-node-next");
      const clearButton = byId("pg-node-clear");
      const focusButton = byId("pg-node-focus");
      const neighboursButton = byId("pg-node-neighbours");
      const isolateButton = byId("pg-node-isolate");
      const showAllButton = byId("pg-node-show-all");
      const fitButton = byId("pg-node-fit");
      const status = byId("pg-search-status");
      if (!input || !findButton || !nextButton || !clearButton || !status) return;

      let matches = [];
      let matchIndex = 0;
      let selectedId = null;
      const originalNodeStyles = new Map();
      const originalEdgeStyles = new Map();

      function getStores() {
        if (!network) return null;
        // PyVis exposes its DataSets as globals; prefer those public DataSets,
        // with the network body as a fallback for different vis-network versions.
        const nodeStore = window.nodes || (network.body && network.body.data && network.body.data.nodes);
        const edgeStore = window.edges || (network.body && network.body.data && network.body.data.edges);
        if (!nodeStore || !edgeStore || typeof nodeStore.get !== "function" ||
            typeof nodeStore.update !== "function" || typeof edgeStore.get !== "function" ||
            typeof edgeStore.update !== "function") return null;
        return { nodes: nodeStore, edges: edgeStore };
      }

      function getSelectedNode() {
        const stores = getStores();
        if (!stores) return null;
        if (selectedId !== null) {
          const selected = stores.nodes.get(selectedId);
          if (selected) return selected;
        }
        const ids = network.getSelectedNodes();
        if (ids && ids.length) {
          selectedId = ids[0];
          return stores.nodes.get(selectedId);
        }
        return null;
      }

      function focusNode(node) {
        if (!node || !network) return;
        selectedId = node.id;
        network.selectNodes([node.id], true);
        network.focus(node.id, {
          scale: 1.8,
          offset: { x: 0, y: 0 },
          animation: { duration: 650, easingFunction: "easeInOutQuad" }
        });
        status.textContent = "Focused: " + (node.label || node.id) + " · " + (node.group || "Entity");
      }

      function findMatches() {
        const query = input.value.trim().toLowerCase();
        const stores = getStores();
        if (!stores) {
          status.textContent = "Graph is still loading. Try again shortly.";
          return;
        }
        if (!query) {
          status.textContent = "Enter a node name or ID.";
          return;
        }
        matches = stores.nodes.get().filter(function (item) {
          const searchable = [item.label, item.title, item.id, item.group]
            .filter(Boolean).join(" ").toLowerCase();
          return searchable.includes(query);
        });
        matchIndex = 0;
        if (!matches.length) {
          selectedId = null;
          network.unselectAll();
          status.textContent = "No match in this loaded graph. Check the entity filters and reload.";
          return;
        }
        focusNode(matches[matchIndex]);
        if (matches.length > 1) {
          status.textContent += " · Match 1 of " + matches.length + " (use Next)";
        }
      }

      function getNeighbourIds(nodeId) {
        const stores = getStores();
        const neighbours = new Set([nodeId]);
        if (!stores) return neighbours;
        stores.edges.get().forEach(function (edge) {
          if (edge.from === nodeId) neighbours.add(edge.to);
          if (edge.to === nodeId) neighbours.add(edge.from);
        });
        return neighbours;
      }

      function rememberStyles(stores) {
        stores.nodes.get().forEach(function (node) {
          if (!originalNodeStyles.has(node.id)) {
            originalNodeStyles.set(node.id, {
              color: node.color, font: node.font, hidden: node.hidden
            });
          }
        });
        stores.edges.get().forEach(function (edge) {
          if (!originalEdgeStyles.has(edge.id)) {
            originalEdgeStyles.set(edge.id, {
              color: edge.color, hidden: edge.hidden, width: edge.width
            });
          }
        });
      }

      function restoreAll() {
        const stores = getStores();
        if (!stores) return;
        rememberStyles(stores);
        const nodeUpdates = stores.nodes.get().map(function (node) {
          const original = originalNodeStyles.get(node.id) || {};
          const update = { id: node.id, hidden: original.hidden === true };
          if (original.color !== undefined) update.color = original.color;
          if (original.font !== undefined) update.font = original.font;
          return update;
        });
        const edgeUpdates = stores.edges.get().map(function (edge) {
          const original = originalEdgeStyles.get(edge.id) || {};
          const update = { id: edge.id, hidden: original.hidden === true };
          if (original.color !== undefined) update.color = original.color;
          if (original.width !== undefined) update.width = original.width;
          return update;
        });
        // One batch update per DataSet instead of thousands of individual redraws.
        stores.nodes.update(nodeUpdates);
        stores.edges.update(edgeUpdates);
        network.redraw();
      }

      function explore(mode) {
        const stores = getStores();
        const selected = getSelectedNode();
        if (!stores || !selected) {
          status.textContent = "Find or click a node first.";
          return;
        }
        rememberStyles(stores);
        const neighbours = getNeighbourIds(selected.id);
        const isIsolate = mode === "isolate";

        const nodeUpdates = stores.nodes.get().map(function (node) {
          const keep = neighbours.has(node.id);
          const original = originalNodeStyles.get(node.id) || {};
          if (isIsolate) {
            return { id: node.id, hidden: !keep };
          }
          if (!keep) {
            return {
              id: node.id,
              color: { background: "#E8ECE9", border: "#D3DBD5", highlight: { background: "#E8ECE9", border: "#AEBBB2" } },
              font: { color: "#A5B0A8", size: 9 }
            };
          }
          const update = { id: node.id, hidden: false };
          if (original.color !== undefined) update.color = original.color;
          if (original.font !== undefined) update.font = original.font;
          return update;
        });

        const edgeUpdates = stores.edges.get().map(function (edge) {
          const direct = edge.from === selected.id || edge.to === selected.id;
          const original = originalEdgeStyles.get(edge.id) || {};
          if (isIsolate) return { id: edge.id, hidden: !direct };
          return {
            id: edge.id, hidden: false,
            color: direct ? (original.color || "#6F927B") : "#E5EAE6",
            width: direct ? 2.8 : 0.7
          };
        });

        // Batch updates: this is critical for large graphs.
        stores.nodes.update(nodeUpdates);
        stores.edges.update(edgeUpdates);
        network.redraw();

        focusNode(selected);
        status.textContent = (isIsolate ? "Isolated" : "Highlighted") + " neighbourhood of " +
          (selected.label || selected.id) + " · " + (neighbours.size - 1) +
          " direct neighbours. Use Show all to restore.";
        if (isIsolate) network.fit({ nodes: Array.from(neighbours), animation: { duration: 500 } });
      }

      findButton.addEventListener("click", findMatches);
      input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") findMatches();
      });
      nextButton.addEventListener("click", function () {
        if (!matches.length) return;
        matchIndex = (matchIndex + 1) % matches.length;
        focusNode(matches[matchIndex]);
        if (matches.length > 1) status.textContent += " · Match " + (matchIndex + 1) + " of " + matches.length;
      });
      clearButton.addEventListener("click", function () {
        input.value = "";
        matches = [];
        matchIndex = 0;
        selectedId = null;
        if (network) network.unselectAll();
        restoreAll();
        status.textContent = "Search cleared. The complete graph is visible.";
      });
      if (focusButton) focusButton.addEventListener("click", function () {
        const selected = getSelectedNode();
        if (!selected) { status.textContent = "Find or click a node first."; return; }
        restoreAll();
        focusNode(selected);
      });
      if (neighboursButton) neighboursButton.addEventListener("click", function () { explore("highlight"); });
      if (isolateButton) isolateButton.addEventListener("click", function () { explore("isolate"); });
      if (showAllButton) showAllButton.addEventListener("click", function () {
        restoreAll();
        const selected = getSelectedNode();
        if (selected) focusNode(selected);
        else network.fit({ animation: { duration: 500 } });
        status.textContent = "Complete graph restored.";
      });
      if (fitButton) fitButton.addEventListener("click", function () {
        restoreAll();
        network.fit({ animation: { duration: 500 } });
        status.textContent = "Fitting the complete graph to the canvas.";
      });

      if (network && typeof network.on === "function") {
        network.on("click", function (params) {
          if (params.nodes && params.nodes.length) {
            const stores = getStores();
            const clicked = stores && stores.nodes.get(params.nodes[0]);
            if (clicked) {
              selectedId = clicked.id;
              input.value = clicked.label || clicked.id;
              status.textContent = "Selected: " + (clicked.label || clicked.id) + " · Choose a neighbourhood action.";
            }
          }
        });
        network.once("stabilizationIterationsDone", function () {
          network.setOptions({ physics: { enabled: false } });
          network.fit({ animation: { duration: 400 } });
        });
      }
    })();
    </script>
    '''
    # Explicitly expose the PyVis Network instance for the injected controls.
    html, exposed_count = re.subn(
        r"(\bnetwork\s*=\s*new\s+vis\.Network\s*\([^;]*?\)\s*;)",
        r"\1\nwindow.network = network;\nwindow.__pgNetwork = network;",
        html,
        count=1,
        flags=re.DOTALL,
    )
    # Fail loudly rather than silently leaving non-functional controls.
    if exposed_count == 0:
        raise RuntimeError("Could not locate the PyVis network constructor; controls were not injected.")

    overlay = (
        _legend_html(counts)
        + search_panel
        + f'<div class="pg-hint">{hint}</div>'
        + '<div class="pg-note">Node positions and edge lengths are visual layout only; they do not represent biological distance or interaction strength.</div>'
    )
    html = re.sub(
        r"</head\s*>",
        lambda match: css + match.group(0),
        html,
        count=1,
        flags=re.IGNORECASE,
    )
    body_match = re.search(r"<body\b[^>]*>", html, flags=re.IGNORECASE)
    if body_match:
        html = html[:body_match.end()] + overlay + html[body_match.end():]
    else:
        html = html.replace("</html>", overlay + "</html>", 1)

    body_end = re.search(r"</body\s*>", html, flags=re.IGNORECASE)
    if body_end:
        html = html[:body_end.start()] + search_script + html[body_end.start():]
    else:
        html += search_script
    return html


def _configure_network(net: Network, *, full_graph: bool = False):
    if full_graph:
        options = r"""
        {
          "interaction": {
            "hover": true, "tooltipDelay": 180, "dragNodes": true,
            "hideEdgesOnDrag": false, "zoomView": true, "dragView": true,
            "navigationButtons": true, "keyboard": {"enabled": true}
          },
          "nodes": {"shape":"dot","font":{"color":"#2F5040","size":10,"face":"Arial"}},
          "edges": {
            "smooth":{"enabled":true,"type":"continuous","roundness":0.08},
            "selectionWidth":2, "color":{"inherit":false},
            "font":{"size":8,"face":"Arial","color":"#52695B","background":"rgba(255,255,255,0.75)"}
          },
          "physics": {
            "enabled":true,"solver":"barnesHut",
            "barnesHut":{"gravitationalConstant":-15000,"centralGravity":0.08,"springLength":145,"springConstant":0.018,"damping":0.22,"avoidOverlap":0.75},
            "stabilization":{"enabled":true,"iterations":220,"updateInterval":30}
          }
        }
        """
    else:
        options = r"""
        {
          "interaction": {
            "hover": true, "tooltipDelay": 180, "dragNodes": true,
            "hideEdgesOnDrag": false, "zoomView": true, "dragView": true,
            "navigationButtons": true, "keyboard": {"enabled": true}
          },
          "nodes": {"shape":"dot","font":{"color":"#2F5040","size":14,"face":"Arial"}},
          "edges": {
            "smooth":{"enabled":true,"type":"continuous","roundness":0.15},
            "selectionWidth":2,
            "font":{"size":10,"face":"Arial","color":"#52695B","background":"rgba(255,255,255,0.9)","strokeWidth":0}
          },
          "physics": {
            "enabled":true,"solver":"barnesHut",
            "barnesHut":{"gravitationalConstant":-4500,"centralGravity":0.14,"springLength":155,"springConstant":0.04,"damping":0.14,"avoidOverlap":0.45},
            "stabilization":{"enabled":true,"iterations":180,"updateInterval":25}
          }
        }
        """
    net.set_options(options)


def build_graph_html(compound_id: str, max_plants: int = 20) -> str | None:
    """Return a self-contained HTML graph for a selected compound."""
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
        label=name[:30] + ("..." if len(name) > 30 else ""),
        title=_tooltip("Compound", name, str(compound_id), center),
        shape="dot", size=36, color=_node_style("Compound", center=True),
        borderWidth=3,
        font={"color":"#234936","size":18,"face":"Arial","bold":True,"strokeWidth":3,"strokeColor":"#FAFCF9"},
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
                label = node_name[:27] + ("..." if len(node_name) > 27 else "")
                net.add_node(
                    graph_id, label=label, title=_tooltip(kind, node_name, str(node_id), node),
                    shape="dot", size=20 if kind != "Plant" else 18,
                    color=_node_style(kind), borderWidth=2,
                    font={"color":"#456052","size":14,"face":"Arial","strokeWidth":3,"strokeColor":"#FAFCF9"},
                )
            source, target = (graph_id, center_id) if incoming else (center_id, graph_id)
            key = (source, target, str(rel.get("Link_ID") or ""), edge_type)
            if key in edge_seen:
                continue
            edge_seen.add(key)
            net.add_edge(
                source, target,
                title=_edge_tooltip(edge_type, rel),
                label=_friendly_relationship(edge_type, rel),
                arrows="to",
                color={"color":"#779A83","highlight":"#285C49","hover":"#285C49"},
                width=2.2,
                font={"size":10,"align":"middle","background":"rgba(255,255,255,0.9)"},
            )

    _configure_network(net, full_graph=False)
    return _wrap_html(net.generate_html(), counts, full_graph=False)


def _kind_from_labels(labels, node: dict | None = None) -> str | None:
    """Resolve the semantic entity type from its identifying properties first.

    Some imported Neo4j nodes may carry an unexpected or legacy label. The
    entity-specific ID/name properties are a more reliable discriminator for
    rendering; labels remain the fallback for older or sparse records.
    """
    node = node or {}
    for kind in ALLOWED_NODE_TYPES:
        field = NODE_ID_FIELDS[kind]
        if node.get(field) is not None and str(node.get(field)).strip():
            return kind
    for kind in ALLOWED_NODE_TYPES:
        field = NODE_NAME_FIELDS[kind]
        if node.get(field) is not None and str(node.get(field)).strip():
            return kind
    for kind in ALLOWED_NODE_TYPES:
        if kind in (labels or []):
            return kind
    return None


def _node_graph_id(kind: str, node: dict, element_id: str | None = None) -> str:
    node_id = node.get(NODE_ID_FIELDS[kind])
    if node_id is None:
        node_id = element_id or node.get("id") or node.get("ID")
    return f"{kind}:{node_id}"


def _node_display_name(kind: str, node: dict) -> str:
    return str(
        node.get(NODE_NAME_FIELDS[kind])
        or node.get("Name")
        or node.get("name")
        or node.get(NODE_ID_FIELDS[kind])
        or kind
    )


def build_full_graph_html(
    node_types: Iterable[str] | None = None,
    relationship_types: Iterable[str] | None = None,
    max_relationships: int = 10000,
    show_edge_labels: bool = False,
) -> str | None:
    """Return the full four-entity knowledge graph as self-contained HTML.

    Optional filters can be supplied by the Streamlit interface. By default,
    all four entity types and all relationships are included.
    """
    selected_nodes = [
        kind for kind in (node_types or ALLOWED_NODE_TYPES)
        if kind in ALLOWED_NODE_TYPES
    ]
    if not selected_nodes:
        selected_nodes = list(ALLOWED_NODE_TYPES)

    graph = get_full_graph(
        node_types=selected_nodes,
        relationship_types=relationship_types,
        max_relationships=max_relationships,
    )
    if not graph["nodes"]:
        return None

    net = Network(
        height="760px", width="100%", bgcolor="#FAFCF9",
        font_color="#2F5040", directed=True, cdn_resources="in_line",
    )
    counts = {kind: 0 for kind in ALLOWED_NODE_TYPES}
    node_seen = set()

    for item in graph["nodes"]:
        kind = _kind_from_labels(item.get("labels"), item.get("node"))
        node = item.get("node") or {}
        if kind is None or not isinstance(node, dict):
            continue

        graph_id = _node_graph_id(kind, node, item.get("element_id"))
        if graph_id in node_seen:
            continue
        node_seen.add(graph_id)
        counts[kind] += 1

        name = _node_display_name(kind, node)
        label = name[:22] + ("..." if len(name) > 22 else "")
        node_id = node.get(NODE_ID_FIELDS[kind]) or item.get("element_id") or ""
        net.add_node(
            graph_id,
            label=label,
            title=_tooltip(kind, name, str(node_id), node),
            shape="dot",
            size={"Plant": 11, "Compound": 13, "Target": 12, "Pathogen": 12}[kind],
            color=_node_style(kind),
            borderWidth=1.5,
            font={"color":"#3E5A4B","size":10,"face":"Arial","strokeWidth":2,"strokeColor":"#FAFCF9"},
        )

    edge_seen = set()
    for item in graph["edges"]:
        source_kind = _kind_from_labels(item.get("source_labels"), item.get("source_node"))
        target_kind = _kind_from_labels(item.get("target_labels"), item.get("target_node"))
        source_node = item.get("source_node") or {}
        target_node = item.get("target_node") or {}
        if not source_kind or not target_kind:
            continue

        source_id = _node_graph_id(source_kind, source_node, item.get("source_element_id"))
        target_id = _node_graph_id(target_kind, target_node, item.get("target_element_id"))
        if source_id not in node_seen or target_id not in node_seen:
            continue

        rel_type = str(item.get("relationship_type") or "RELATED_TO")
        rel = item.get("relationship") or {}
        relationship_id = item.get("relationship_element_id")
        key = (
            str(relationship_id)
            if relationship_id is not None
            else (source_id, target_id, rel_type, str(rel.get("Link_ID") or ""))
        )
        if key in edge_seen:
            continue
        edge_seen.add(key)

        edge_args = {
            "title": _edge_tooltip(rel_type, rel),
            "arrows": "to",
            "color": {"color": "#6F927B", "highlight": "#285C49", "hover": "#285C49"},
            "width": 2.0,
        }
        if show_edge_labels:
            edge_args["label"] = _friendly_relationship(rel_type, rel)
            edge_args["font"] = {
                "size": 8, "align": "middle",
                "background": "rgba(255,255,255,0.82)",
            }
        net.add_edge(source_id, target_id, **edge_args)

    _configure_network(net, full_graph=True)
    return _wrap_html(net.generate_html(), counts, full_graph=True)


def build_html_graph(compound_id: str, output_file=None, max_plants: int = 20):
    """Backward-compatible file-based compound graph API."""
    html = build_graph_html(compound_id=compound_id, max_plants=max_plants)
    if html is None:
        return None
    path = Path(output_file or f"outputs/graph_{compound_id}.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def build_html_full_graph(output_file=None, **kwargs):
    """File-based full-graph API for scripts outside Streamlit."""
    html = build_full_graph_html(**kwargs)
    if html is None:
        return None
    path = Path(output_file or "outputs/full_knowledge_graph.html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


if __name__ == "__main__":
    path = build_html_graph("CMP011", output_file="outputs/graph_CMP011.html")
    print(f"Compound graph HTML: {path}" if path else "Compound not found in Neo4j")
