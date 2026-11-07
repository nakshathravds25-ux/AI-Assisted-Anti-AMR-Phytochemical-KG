# PhytoGraph Research Atlas

### An AI-Assisted Knowledge Graph Framework for Identifying Anti-AMR Phytochemicals from Traditional Medicine

## Project Overview

PhytoGraph Research Atlas is a research-oriented platform designed to explore medicinal plants, phytochemicals, antibiotic-resistant pathogens, and molecular targets using a knowledge graph.

The project combines evidence-based compound prioritization, Neo4j graph exploration, and an AI-assisted research interface to help identify promising phytochemicals for further anti-antimicrobial resistance (AMR) research.

## Knowledge Graph Dataset

| Entity | Count |
|---|---:|
| Medicinal plants | 100 |
| Phytochemical compounds | 425 |
| Pathogen/resistance records | 24 |
| Molecular targets | 49 |
| Total nodes | 598 |
| Total relationships | 4,299 |
| Evidence-ranked compounds | 137 |

## Key Features

- **Compound Explorer:** Explore phytochemicals and their evidence-priority rankings.
- **Knowledge Graph Explorer:** Visualize relationships between plants, compounds, pathogens, and molecular targets.
- **AI Research Assistant:** Answer research questions using graph-retrieved evidence and Groq-powered explanations.
- **Evidence Safeguards:** Identify questions for which the available evidence is insufficient.
- **Interactive Dashboard:** Explore the dataset through a Streamlit-based research interface.

## Technology Stack

- Python
- Streamlit
- Neo4j AuraDB
- Groq API
- PyVis
- Graph-based retrieval-augmented generation (GraphRAG)

## Running Locally

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Configure Neo4j and Groq credentials privately using environment variables, then run:

```bash
python -m streamlit run app.py
```

Required configuration includes `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `GROQ_API_KEY`, and `GROQ_MODEL`.

## Research Limitations

PhytoGraph is a computational research-support tool, not a clinically validated drug discovery system.

Compound priority scores are heuristic evidence-ranking indicators, not measures of treatment effectiveness. A graph relationship does not necessarily demonstrate experimentally confirmed binding, and additional laboratory validation is required before drawing therapeutic conclusions.

## Project Status

Dataset integration, knowledge graph exploration, compound ranking, and AI-assisted evidence retrieval have been implemented. Cloud deployment and final application testing are in progress.
