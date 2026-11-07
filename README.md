# PhytoGraph Research Atlas

### An AI-Assisted Knowledge Graph Framework for Identifying Anti-AMR Phytochemicals from Traditional Medicine

**A research-oriented platform integrating medicinal plant data, phytochemical evidence, knowledge graphs, and AI-assisted scientific question answering to support antimicrobial resistance (AMR) research.**

**Live Application:** https://phytograph-research-atlas.streamlit.app/

**Project Status:** Deployed — Functional Testing Completed

---

## 1. Project Overview

Antimicrobial resistance (AMR) is a major global health challenge that reduces the effectiveness of existing antimicrobial treatments.

Medicinal plants contain diverse phytochemical compounds that may exhibit antimicrobial activity or interact with biological mechanisms associated with antimicrobial resistance.

However, information about medicinal plants, phytochemicals, bacterial pathogens, and molecular targets is distributed across multiple scientific databases and research publications.

**PhytoGraph Research Atlas** addresses this information-integration challenge by building an AI-assisted knowledge graph framework to organize, explore, and prioritize potentially relevant phytochemicals.

The system integrates:

- Medicinal plants and their associated phytochemicals
- Antibiotic-resistant pathogen and resistance-phenotype records
- Molecular targets involved in antimicrobial activity or resistance
- Evidence-supported relationships between biological entities
- A heuristic evidence-based compound prioritization framework
- Graph Retrieval-Augmented Generation (GraphRAG)
- An interactive research interface for knowledge graph exploration

The objective is to support evidence exploration and research prioritization, not to establish the clinical effectiveness of compounds.

---

## 2. Project Objectives

The primary objectives of the project are:

1. **Integrate traditional medicine and molecular research data** into a structured, connected knowledge graph.
2. **Identify relationships** among medicinal plants, phytochemicals, resistant pathogens, and molecular targets.
3. **Expand and organize the knowledge graph** using literature-derived and curated biological associations.
4. **Prioritize phytochemicals** using a transparent, evidence-oriented ranking framework.
5. **Implement GraphRAG** to retrieve relevant biological evidence for scientific questions.
6. **Provide AI-assisted explanations** grounded in retrieved graph records.
7. **Introduce scientific safeguards** to identify claims not adequately supported by the available evidence.
8. **Develop an interactive web application** to make the knowledge graph accessible for research and academic demonstration.

---

## 3. Knowledge Graph Dataset

The current knowledge graph contains **598 nodes and 4,299 relationships**.

### Entity Statistics

| Entity Type | Count |
|---|---:|
| Medicinal Plants | 100 |
| Phytochemical Compounds | 425 |
| Pathogen / Resistance Records | 24 |
| Molecular Targets | 49 |
| **Total Nodes** | **598** |

### Relationship Statistics

| Relationship Type | Count |
|---|---:|
| Plant → Compound | 3,898 |
| Compound → Target | 174 |
| Compound → Pathogen | 178 |
| Pathogen → Target | 49 |
| **Total Relationships** | **4,299** |

### Compound Prioritization

| Metric | Value |
|---|---:|
| Total Compounds in Knowledge Graph | 425 |
| Compounds Included in V3 Evidence Ranking | 137 |
| Compounds Without V3 Ranking | 288 |

The 137 ranked compounds have sufficient mapped information to be included in the current evidence-prioritization dataset.

Compounds not included in the ranking are **not necessarily inactive or ineffective**. Their exclusion does not establish a lack of biological activity.

### Data Representation

The knowledge graph contains four principal node types:

- **Plant:** Medicinal plant species
- **Compound:** Phytochemical entities
- **Pathogen:** Bacterial pathogen and resistance-related records
- **Target:** Molecular or protein targets

The relationships describe recorded plant occurrences, target associations, pathogen-related evidence, and pathogen–target connections.

Relationship types represent curated or mapped associations. Their experimental support, provenance, and validation status may differ.

---

## 4. System Architecture

PhytoGraph combines a knowledge graph database, scientific evidence retrieval, rule-based safeguards, and optional large language model explanations.

### System Workflow

```text
Scientific and Traditional Medicine Data
                  |
                  v
      Data Integration and Curation
                  |
                  v
       Neo4j Knowledge Graph
                  |
          +-------+-------+
          |               |
          v               v
  Compound Ranking   Graph Exploration
          |               |
          +-------+-------+
                  |
                  v
          GraphRAG Retrieval
                  |
                  v
       Relevant Evidence Records
                  |
                  v
      Evidence Sufficiency Checks
                  |
          +-------+-------+
          |               |
          v               v
   Direct Evidence     Groq-Assisted
      Response          Explanation
          |               |
          +-------+-------+
                  |
                  v
         Streamlit Interface
```

The retrieval system queries Neo4j before producing a scientific response.

For supported compound-list questions, the application can return deterministic answers directly from graph records without requiring the language model to generate the list.

For analytical questions, the application can use Groq to produce evidence-grounded explanations.

---

## 5. Key Features

### 5.1 Interactive Research Dashboard

The Streamlit application provides an accessible interface for exploring the integrated research dataset.

It includes:

- Knowledge graph statistics
- Dataset overview
- Research workflow descriptions
- Navigation between research modules
- Scientific interpretation notes

The frontend uses a custom light botanical-scientific design.

### 5.2 Compound Explorer

The Compound Explorer allows users to investigate phytochemicals included in the evidence-prioritization dataset.

Features include:

- Compound search and exploration
- Evidence-based ranking display
- Antimicrobial evidence indicators
- Molecular target evidence indicators
- Supporting publication information
- Pathogen and target connection counts
- Evidence caution indicators

The interface emphasizes research priority rather than predicted treatment effectiveness.

### 5.3 Knowledge Graph Explorer

The interactive graph visualization shows connections between selected compounds and associated biological entities.

Graph elements include:

- Central phytochemical compound
- Associated medicinal plants
- Molecular targets
- Pathogen and resistance records
- Evidence-linked relationships

Visualization features include:

- Interactive node dragging
- Graph zooming and navigation
- Hover-based information
- Distinct visual categories for node types
- Focused compound-centered network exploration

The visualization uses **PyVis** and Neo4j graph queries.

### 5.4 AI Evidence Research Assistant

The research assistant supports questions involving phytochemicals, molecular targets, and pathogen-related associations.

Example questions:

- Which phytochemicals interact with OXA-48?
- What target-related evidence is available for Kaempferol?
- What antimicrobial evidence is recorded for Eugenol?
- Does the available evidence establish direct binding between Eugenol and NorA?
- Does the evidence establish that Kaempferol cures resistant infections in humans?

The system retrieves mapped evidence from Neo4j and evaluates whether it is relevant to the question.

Depending on the question and evidence, it may provide:

- A direct graph-derived answer
- An AI-assisted explanation with evidence references
- An insufficient-evidence response
- A recommendation for further evidence review

### 5.5 Scientific Evidence Safeguards

The system includes a rule-based answerability detector designed to reduce unsupported scientific claims.

It distinguishes among:

- **SUPPORTED:** Relevant graph evidence was retrieved; this does not independently verify the claim.
- **INSUFFICIENT:** The retrieved records do not establish the requested claim.
- **REVIEW_REQUIRED:** Potentially relevant evidence exists but requires additional examination of the original scientific sources.

Specific safeguards address:

- Human clinical efficacy claims
- Direct physical target-binding claims
- Differences between MIC, IC50, and FICI measurements
- Publication identifiers and study independence
- Experimental evidence versus inferred biological associations

These safeguards are heuristic screening mechanisms, **not automated scientific fact-checking or independent validation of publications**.

---

## 6. Evidence-Based Compound Prioritization

PhytoGraph uses a **V3 heuristic evidence-prioritization framework**.

The ranking system considers evidence-related indicators such as:

- Recorded antimicrobial activity
- Molecular target associations
- Pathogen-related evidence coverage
- Supporting publication information
- Evidence specificity
- Caution and uncertainty indicators

The application currently includes an evidence-ranking dataset of **137 compounds**.

### Understanding the Evidence Priority Score

The Evidence Priority Score is a computational ranking indicator intended to help identify compounds that may warrant further scientific investigation.

**A higher score indicates greater priority under the current ranking methodology.**

It does not mean that a compound:

- Has a corresponding percentage of antimicrobial efficacy
- Is clinically effective
- Has been proven safe in humans
- Directly binds every associated target
- Is superior to an approved antibiotic

The ranking framework is intended for research prioritization and evidence exploration.

Exact scoring implementation and weighting should be interpreted using the corresponding V3 methodology and source data.

---

## 7. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development and research workflows |
| Streamlit | Interactive web application |
| Neo4j AuraDB | Cloud-hosted knowledge graph database |
| Cypher | Graph querying and relationship retrieval |
| Pandas | Dataset loading and manipulation |
| PyVis | Interactive knowledge graph visualization |
| Groq API | Hosted language model inference |
| GPT-OSS 20B | Configured hosted explanation model |
| GraphRAG | Knowledge graph evidence retrieval and answer generation |
| GitHub | Source code version control |
| Streamlit Community Cloud | Web application deployment |

The application also includes an optional local language model interface through `ollama_engine.py`.

The currently deployed system uses Groq for hosted model explanations rather than depending on college DGX GPU infrastructure.

---

## 8. Repository Structure

```text
AI-Assisted-Anti-AMR-Phytochemical-KG/
│
├── app.py
├── database.py
├── graphrag.py
├── groq_engine.py
├── ollama_engine.py
├── graph_visualization.py
├── ranking.py
│
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── V3_EVIDENCE_PRIORITIZATION_137.csv
│
├── evaluation/
│   ├── __init__.py
│   └── answerability_detector.py
│
└── .streamlit/
    └── config.toml
```

### Main File Descriptions

| File | Description |
|---|---|
| `app.py` | Main Streamlit frontend and application navigation |
| `database.py` | Neo4j connection and database utilities |
| `graphrag.py` | Evidence retrieval and question-specific graph queries |
| `groq_engine.py` | Groq integration, grounded responses, and output validation |
| `ollama_engine.py` | Local model interface and shared evidence-validation utilities |
| `ranking.py` | Loading and processing compound evidence rankings |
| `graph_visualization.py` | Interactive compound-centered graph visualization |
| `answerability_detector.py` | Rule-based scientific evidence sufficiency checks |
| `requirements.txt` | Python dependencies |
| `config.toml` | Streamlit theme configuration |

The full knowledge graph is hosted in Neo4j AuraDB. The application does not require the original node and relationship CSV files to be stored in the deployment repository.

The original curated datasets should be preserved separately for research reproducibility and academic documentation.

---

## 9. Installation and Local Setup

### Prerequisites

- Python
- Git (optional for manual download)
- A configured Neo4j database containing the project graph
- A Groq API key for hosted AI explanations

### Step 1 — Clone the Repository

```bash
git clone https://github.com/nakshathravds25-ux/AI-Assisted-Anti-AMR-Phytochemical-KG.git
```

```bash
cd AI-Assisted-Anti-AMR-Phytochemical-KG
```

Access to the repository is required if it remains private.

### Step 2 — Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Alternatively, use the virtual environment's Python executable directly.

### Step 3 — Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

Create a local `.env` file in the project root.

```dotenv
NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=YOUR_DATABASE_PASSWORD
NEO4J_DATABASE=YOUR_DATABASE_NAME

GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-20b
```

Replace the placeholders with your actual configuration.

**Never commit `.env` files, credentials, or API keys to GitHub.**

### Step 5 — Test the Neo4j Connection

```powershell
python database.py
```

A successful connection should return the knowledge graph node and relationship statistics.

### Step 6 — Start the Application

```powershell
python -m streamlit run app.py
```

Streamlit will display a local URL, usually:

```text
http://localhost:8501
```

Open the URL in a browser.

---

## 10. Cloud Deployment

The application is deployed using **Streamlit Community Cloud**.

### Live Website

https://phytograph-research-atlas.streamlit.app/

### Deployment Configuration

| Setting | Configuration |
|---|---|
| Platform | Streamlit Community Cloud |
| Source | GitHub repository |
| Branch | `main` |
| Main Application | `app.py` |
| Database | Neo4j AuraDB |
| Hosted AI Provider | Groq |
| Secrets Management | Streamlit Cloud Secrets |

### Streamlit Cloud Secrets

The deployed application uses environment variables configured through Streamlit's private Secrets settings.

Example format:

```toml
NEO4J_URI = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "YOUR_DATABASE_PASSWORD"
NEO4J_DATABASE = "YOUR_DATABASE_NAME"

GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_MODEL = "openai/gpt-oss-20b"
```

Actual credentials must never be included in repository files, documentation, screenshots, or public logs.

Availability of the application depends on the hosting platform, database instance, network connectivity, and applicable provider limits.

---

## 11. Functional Testing and Evaluation

The project has undergone local development testing and initial deployed application testing.

Testing has included:

- Neo4j database connection and graph statistics
- Retrieval of compound–target relationships
- Direct graph-derived compound-list responses
- Compound evidence ranking display
- Interactive knowledge graph visualization
- Groq-assisted scientific explanations
- Evidence citation handling
- Insufficient-evidence detection for unsupported clinical claims
- Safeguards against unsupported direct-binding assertions
- Cloud application configuration and connectivity

### Example Evidence Checks

**Compound–Target Retrieval**

Question: Which phytochemicals interact with OXA-48?

Expected behavior: Retrieve mapped compound–target relationships from Neo4j, displaying evidence identifiers and distinguishing graph associations from confirmed physical binding.

**Clinical Claim Safeguard**

Question: Does Kaempferol cure antibiotic-resistant infections in humans?

Expected behavior: Indicate that retrieved preclinical or mechanistic evidence does not establish human clinical effectiveness.

**Direct Binding Safeguard**

Question: Does Eugenol directly bind NorA?

Expected behavior: Distinguish indirect target-related evidence from experimentally confirmed physical binding.

### Evaluation Limitations

These checks demonstrate selected application behaviors.

They do **not** establish independently measured scientific accuracy, recall, precision, clinical predictive performance, or comprehensive model reliability.

A larger reference-labeled evaluation dataset and independent source review would be required for formal performance assessment.

---

## 12. Scientific and Research Limitations

PhytoGraph is an exploratory computational research prototype.

Important limitations include:

1. **Variable evidence quality:** Relationships may be supported by different types and levels of evidence.

2. **Incomplete coverage:** The graph represents a curated subset of medicinal plants, compounds, pathogen records, and targets rather than all known biological relationships.

3. **Graph association versus biological proof:** An association in Neo4j does not automatically establish a direct molecular interaction.

4. **Experimental versus clinical findings:** In-vitro antimicrobial activity, enzyme inhibition, docking predictions, and animal studies cannot independently establish clinical effectiveness in humans.

5. **Heuristic ranking:** Evidence Priority Scores are not calibrated probabilities or measures of therapeutic success.

6. **Publication provenance:** Multiple relationships may originate from the same paper; publication counts and source independence require verification.

7. **Language model limitations:** AI-generated explanations can still be incomplete or inaccurate despite retrieval grounding and rule-based validation.

8. **No experimental validation by the application:** The web platform does not itself perform laboratory assays or clinical testing.

All scientific conclusions should be checked against the original publications and, where appropriate, validated experimentally.

---

## 13. Future Scope

Potential future improvements include:

- Expanded evidence-verified phytochemical and pathogen coverage
- More comprehensive publication provenance and source deduplication
- Independent validation of chemical identifiers and structures
- Stronger evidence grading and confidence estimation
- Formal retrieval evaluation using reference-labeled questions
- Systematic assessment of AI answer accuracy and citation faithfulness
- More advanced graph-based compound prioritization
- Integration of molecular structures and experimentally validated target information
- Improved comparison of candidate compounds across pathogens
- Greater automation of scientific data updates
- Expanded research dashboards and interactive analysis tools

These are planned research directions rather than currently validated capabilities.

---

## 14. Project Status

**Current Status: Cloud Deployed and Functionally Tested**

The following components have been implemented:

- Expanded phytochemical and medicinal plant dataset
- Neo4j knowledge graph integration
- Evidence-prioritized compound rankings
- Interactive graph visualization
- GraphRAG evidence retrieval
- Groq-supported AI research assistant
- Rule-based answerability screening
- Streamlit web application
- GitHub repository integration
- Cloud deployment through Streamlit Community Cloud

The application has been tested for core functionality. Additional systematic evaluation and scientific evidence verification remain future work.

### Access the Application

**PhytoGraph Research Atlas**

https://phytograph-research-atlas.streamlit.app/

---

## 15. Academic Disclaimer

This project was developed for academic research and educational demonstration.

PhytoGraph does not provide medical advice, recommend treatments, establish drug safety, or certify the efficacy of phytochemical compounds against antimicrobial-resistant infections.

Findings generated by the platform should be interpreted as research-supporting evidence, not clinically validated therapeutic recommendations.

---

## 16. Project Title

**An AI-Assisted Knowledge Graph Framework for Identifying Anti-AMR Phytochemicals from Traditional Medicine**

**Application:** PhytoGraph Research Atlas

**Research Area:** Artificial Intelligence, Knowledge Graphs, Bioinformatics, Traditional Medicine, and Antimicrobial Resistance.
