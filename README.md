# PhytoGraph Research Atlas

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://phytograph-research-atlas.streamlit.app/)

**🚀 Live Application:** https://phytograph-research-atlas.streamlit.app/

### An AI-Assisted Knowledge Graph Framework for Identifying Anti-AMR Phytochemicals from Traditional Medicine

An AI-assisted research platform integrating medicinal plants, phytochemical evidence, antimicrobial-resistance-related pathogen records, and molecular targets through knowledge graphs and GraphRAG.

PhytoGraph Research Atlas is an AI-assisted research platform that integrates medicinal plants, phytochemical compounds, antimicrobial-resistance-related pathogen records, and molecular targets into a structured knowledge graph.

The platform combines **Neo4j, Graph Retrieval-Augmented Generation (GraphRAG), evidence-based compound prioritization, and AI-assisted scientific question answering** to support the exploration of phytochemicals relevant to antimicrobial resistance (AMR).

**Hosted Application:** https://phytograph-research-atlas.streamlit.app/  
**GitHub Repository:** https://github.com/nakshathravds25-ux/AI-Assisted-Anti-AMR-Phytochemical-KG  
**Deployment Platform:** Streamlit Community Cloud

> **Research scope:** PhytoGraph is an exploratory research-support system. Its rankings and retrieved associations do not establish clinical efficacy, drug safety, or proven treatment outcomes.

---

## 1. Project Overview

Antimicrobial resistance (AMR) is a major global health challenge that reduces the effectiveness of existing antimicrobial treatments.

Medicinal plants contain a wide variety of phytochemical compounds that may exhibit antimicrobial activity or interact with biological mechanisms associated with antimicrobial resistance. However, information about medicinal plants, their compounds, resistant pathogens, molecular targets, and supporting scientific publications is distributed across multiple research sources.

PhytoGraph addresses this information-integration challenge by organizing relevant biological entities and their evidence-supported associations into a connected knowledge graph.

The platform is designed to:

- Integrate medicinal plant and phytochemical information.
- Organize compound–pathogen and compound–target evidence.
- Connect pathogens with resistance-associated molecular targets.
- Explore biological relationships through interactive graph visualization.
- Prioritize selected compounds using a transparent evidence-based scoring framework.
- Retrieve relevant graph evidence for scientific questions.
- Generate AI-assisted explanations grounded in retrieved records.
- Identify questions for which the available evidence is insufficient or requires further review.

The overall goal is to make anti-AMR phytochemical research more structured, traceable, and accessible.

---

## 2. Project Objectives

The primary objectives are:

1. **Knowledge integration:** Build a connected representation of medicinal plants, phytochemicals, pathogens, and molecular targets.

2. **Dataset expansion:** Organize and expand biological relationships using curated scientific evidence.

3. **Evidence mapping:** Associate graph relationships with available publication identifiers, source information, experimental findings, and evidence descriptions.

4. **Compound prioritization:** Develop a heuristic ranking framework to identify compounds with comparatively stronger mapped research evidence.

5. **Knowledge graph exploration:** Provide interactive visualization of the complete knowledge graph and compound-centred networks.

6. **GraphRAG implementation:** Retrieve relevant biological relationships from Neo4j before generating research answers.

7. **Scientific safeguards:** Reduce unsupported claims by distinguishing retrieved evidence from clinical conclusions and experimentally confirmed molecular interactions.

8. **Research accessibility:** Develop a web-based interface for exploring the dataset and interacting with the knowledge graph.

---

## 3. Knowledge Graph Dataset

The current knowledge graph contains **598 nodes and 4,299 relationships**.

### 3.1 Entity Statistics

| Entity Type | Count |
|---|---:|
| Medicinal Plants | 100 |
| Phytochemical Compounds | 425 |
| Pathogen / Resistance Records | 24 |
| Molecular Targets | 49 |
| **Total Nodes** | **598** |

### 3.2 Relationship Statistics

| Relationship | Direction | Count |
|---|---|---:|
| `CONTAINS_COMPOUND` | Plant → Compound | 3,898 |
| `INTERACTS_WITH_TARGET` | Compound → Target | 174 |
| `ACTS_AGAINST_PATHOGEN` | Compound → Pathogen | 178 |
| `ASSOCIATED_WITH_TARGET` | Pathogen → Target | 49 |
| **Total Relationships** | | **4,299** |

### 3.3 Graph Entity Description

The knowledge graph contains four principal node types:

- **Plant:** Medicinal plant species.
- **Compound:** Phytochemical compounds associated with medicinal plants or biological evidence.
- **Pathogen:** Bacterial pathogen and antimicrobial-resistance-related records.
- **Target:** Molecular or protein targets associated with pathogen biology or compound-related evidence.

Relationships connect these entities according to the available curated records.

A graph relationship represents a recorded association. Its existence does not automatically establish causation, direct molecular binding, or clinical effectiveness.

### 3.4 Evidence and Source Information

Where available, relationship records retain information such as:

- Evidence type and category
- Biological finding
- Experimental method
- Antimicrobial activity information
- Resistance relevance
- Publication identifiers
- Source URLs
- Relationship identifiers
- Evidence notes and caution flags

The availability and completeness of these fields can vary between records. Original publications should be consulted when interpreting scientific findings.

---

## 4. System Architecture

PhytoGraph combines a graph database, evidence retrieval layer, ranking module, AI-assisted explanation layer, and scientific answerability checks.

### 4.1 System Workflow

```text
        Scientific and Traditional Medicine Data
                         |
                         v
              Data Integration and Curation
                         |
                         v
                 Neo4j Knowledge Graph
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
        Graph Search   Evidence    Compound
        and Filtering  Retrieval   Prioritization
             |           |           |
             +-----------+-----------+
                         |
                         v
                 GraphRAG Processing
                         |
                         v
                Retrieved Evidence Records
                         |
                         v
               Scientific Safeguard Checks
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Evidence-Based          AI-Assisted
          Retrieval             Explanation
             |                       |
             +-----------+-----------+
                         |
                         v
                 Streamlit Interface
```

### 4.2 Main Architecture Components

| Component | Responsibility |
|---|---|
| Neo4j | Stores biological entities and their relationships |
| Cypher | Retrieves graph nodes and relationships |
| GraphRAG | Identifies relevant graph evidence for research questions |
| Ranking Module | Loads and processes compound evidence-priority scores |
| Answerability Detector | Screens whether retrieved evidence is sufficient for the requested claim |
| Groq Integration | Provides hosted language-model explanations |
| Ollama Integration | Provides an optional local language-model interface |
| Streamlit | Provides the interactive research application |
| PyVis | Renders interactive graph visualizations |

The application retrieves evidence from Neo4j before using the language model for explanatory responses.

For supported compound-list questions, graph-derived results can be returned directly rather than relying on the language model to generate compound names.

---

## 5. Application Features

### 5.1 Research Dashboard

The dashboard provides an overview of the research knowledge graph.

It includes:

- Total medicinal plant count
- Total phytochemical count
- Pathogen and resistance-record count
- Molecular target count
- Knowledge graph relationship statistics
- Research workflow information
- Evidence interpretation guidance

### 5.2 Evidence Coverage Explorer

The Evidence Coverage Explorer provides access to the current mapped compound evidence export. It foregrounds the evidence fields and record coverage; it does not recalculate the stored V3 heuristic score.

Features include:

- Searchable directory of mapped compound evidence profiles
- Filtering by recorded evidence coverage (both evidence types, pathogen-only, or target-only)
- Comparison of antimicrobial and target evidence grades
- Publication, pathogen-record and target-connection coverage
- Evidence caution flags
- Optional inspection of the legacy precomputed V3 score for traceability
- Supporting evidence indicators
- Publication and pathogen coverage information
- Caution flags and evidence interpretation

The current export contains 137 mapped compound profiles.

The remaining compounds are not automatically classified as inactive. They are simply not included in the current scoring export.

### 5.3 Interactive Knowledge Graph Explorer

The graph explorer supports two visualization modes:

**Full Knowledge Graph**

Provides an interactive view of the connected graph, with filtering options for node categories and relationship types.

**Search by Compound**

Allows users to search the complete registered compound collection, including compounds that are not part of the 137-compound ranking export.

Graph exploration features include:

- Full knowledge graph visualization
- Compound-centred network visualization
- Search for graph nodes
- Relationship-type filtering
- Node-category filtering
- Graph navigation and zooming
- Interactive node selection and movement
- Relationship labels and evidence details
- Resetting graph filters

The visualization uses PyVis and retrieves graph information from Neo4j.

**Important:** Graph layout, node positions, edge lengths, and visual proximity are visualization properties. They do not represent biological distance, interaction strength, or evidence confidence.

### 5.4 AI-Assisted Research Assistant

The AI Research Assistant accepts scientific questions about phytochemicals, pathogens, and molecular targets.

Example questions:

- Which phytochemicals have mapped relationships with OXA-48?
- What target-related evidence is available for Eugenol?
- What antimicrobial evidence is recorded for Isoliquiritin?
- Which compounds are associated with NDM-1?
- Does the available evidence establish direct binding between a compound and a molecular target?
- Does the available evidence demonstrate clinical effectiveness in humans?

The research assistant can provide:

- Graph-derived compound and target information
- Retrieved evidence relationships
- Publication and source references where available
- AI-assisted scientific explanations
- Insufficient-evidence responses
- Requests for additional source verification

The system is designed to distinguish recorded graph associations from stronger experimental or clinical claims.

---

## 6. Evidence Coverage and Legacy Prioritization Export

The current application uses the **Evidence Coverage Explorer** to compare the contents of the prepared compound-evidence export. It displays recorded evidence categories, internal grade fields, provisional source counts, pathogen coverage, target connections and caution flags.

The ranking module (`ranking.py`) loads `data/V3_EVIDENCE_PRIORITIZATION_137.csv`. It does not calculate the V3 score at runtime.

### 6.1 Documented Scoring Dimensions

The earlier project documentation describes the following intended maximum weight allocations:

| Evidence Dimension | Documented Maximum |
|---|---:|
| Pathogen-study evidence grade | 30 |
| Molecular-target evidence grade | 25 |
| Resistance-specificity information | 20 |
| Distinct research source breadth | 15 |
| Pathogen-record breadth | 10 |
| **Total** | **100** |

**Reproducibility limitation:** this repository snapshot does not include the executable scoring-generation procedure that defines the component-grade assignment rules, normalization, conversion to points, and aggregation into `V3_Heuristic_Score`. The stored value (for example, 78.91 for Eugenol) therefore cannot currently be independently reproduced from the application code. The application retains the score only as a legacy precomputed field for traceability; it is not used to filter or sort profiles in the Evidence Coverage Explorer.

### 6.2 Evidence Field Interpretation

- `Evidence_Coverage` indicates whether the export contains pathogen-side evidence, target-side evidence, or both.
- `Activity_Grade` and `Target_Grade` are internal values supplied in the export. They are not percentages of bacterial killing or probabilities of physical binding.
- `Specificity_Proxy` is a resistance-specificity proxy field. Its precise construction is not defined by the executable code in this repository.
- Publication counts are provisional deduplicated estimates and may require manual verification.
- Pathogen and target link counts describe recorded graph relationships, not necessarily independent publications.
- A zero caution-flag count does not establish safety or complete verification.

### 6.3 Coverage

| Metric | Count |
|---|---:|
| Total registered compounds | 425 |
| Compound profiles in the current evidence export | 137 |
| Compounds without a profile in the current export | 288 |

The 288 compounds absent from the export remain part of the registered compound collection. Their absence does not establish a lack of biological activity.

The data is stored in:

`data/V3_EVIDENCE_PRIORITIZATION_137.csv`

The prototype's evidence coverage is intended to support literature-oriented exploration. It is not a clinical prediction or therapeutic decision tool.

---

## 7. Scientific Answerability Safeguards

An important part of PhytoGraph is its rule-based answerability screening system.

The purpose of this component is to reduce unsupported scientific statements when the retrieved graph evidence does not establish the requested claim.

### 7.1 Answerability Categories

| Category | Meaning |
|---|---|
| `SUPPORTED` | Relevant graph evidence was retrieved for the question. |
| `INSUFFICIENT` | The retrieved records do not establish the requested claim. |
| `REVIEW_REQUIRED` | Potentially relevant evidence exists, but the original scientific source requires further examination. |

`SUPPORTED` means that relevant records were retrieved. It does not mean that the claim has been independently scientifically verified.

### 7.2 Scientific Checks

The safeguards address several important interpretation issues:

**Human clinical outcomes**

In-vitro studies, enzyme inhibition experiments, animal studies, and experiments involving clinical bacterial isolates do not independently establish clinical effectiveness in human patients.

**Direct molecular binding**

A compound–target graph association does not automatically demonstrate direct physical binding. Experimental binding evidence must be distinguished from indirect biological effects, docking predictions, gene-expression changes, and other mechanistic observations.

**MIC, IC50, and FICI interpretation**

These measurements describe different experimental outcomes and should not be treated as interchangeable.

**Publication independence**

Multiple relationships may refer to the same publication. Relationship counts should not automatically be interpreted as independent-study counts.

**Evidence provenance**

Source identifiers and original publications should be checked before drawing scientific conclusions.

### 7.3 Safeguard Limitations

The answerability detector uses rule-based screening and pattern matching.

It is not an automated scientific fact-checker, a substitute for expert review, or proof that an individual publication has been interpreted correctly.

AI-generated explanations can still be incomplete or inaccurate despite retrieval grounding and validation checks.

---

## 8. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend development and application logic |
| Streamlit | Interactive web application |
| Neo4j AuraDB | Knowledge graph storage |
| Cypher | Graph database querying |
| Pandas | Dataset processing |
| PyVis | Interactive graph visualization |
| python-dotenv | Local environment configuration |
| Groq API | Hosted language-model inference |
| GPT-OSS 20B | Configured hosted explanation model |
| Ollama | Optional local model interface |
| GitHub | Source code version control |
| Streamlit Community Cloud | Application hosting |

The hosted AI integration uses the Groq API with `openai/gpt-oss-20b` as its default configured model.

The application also includes an optional local-model interface through Ollama.

---

## 9. Repository Structure

The repository contains the main application, graph database utilities, retrieval modules, ranking logic, visualization code, and evaluation safeguards.

```text
AI-Assisted-Anti-AMR-Phytochemical-KG/
│
├── app.py
├── database.py
├── graph_visualization.py
├── graphrag.py
├── groq_engine.py
├── ollama_engine.py
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
| `app.py` | Main Streamlit application and user interface |
| `database.py` | Neo4j connection and database utilities |
| `graph_visualization.py` | Full graph and compound-centred network visualization |
| `graphrag.py` | Graph evidence retrieval and question processing |
| `groq_engine.py` | Hosted Groq model integration and response validation |
| `ollama_engine.py` | Optional local model integration and evidence utilities |
| `ranking.py` | Loads and processes compound ranking data |
| `answerability_detector.py` | Rule-based scientific answerability screening |
| `requirements.txt` | Python dependency definitions |
| `.streamlit/config.toml` | Streamlit interface theme configuration |

The Neo4j graph is provisioned separately. The application connects to the configured database rather than importing the complete graph from CSV files every time it starts.

---

## 10. Installation and Local Setup

### 10.1 Prerequisites

- Python 3.10 or later
- Access to the project repository
- A configured Neo4j database containing the project graph
- A Groq API key for hosted AI explanations
- Internet connectivity for cloud database and hosted model access

### 10.2 Clone the Repository

```bash
git clone https://github.com/nakshathravds25-ux/AI-Assisted-Anti-AMR-Phytochemical-KG.git
```

Navigate to the project directory:

```bash
cd AI-Assisted-Anti-AMR-Phytochemical-KG
```

### 10.3 Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 10.4 Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 10.5 Configure Environment Variables

Create a `.env` file in the project root.

Example configuration:

```dotenv
# Neo4j Database
NEO4J_URI=neo4j+s://YOUR_INSTANCE.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=YOUR_DATABASE_PASSWORD
NEO4J_DATABASE=neo4j

# Groq Hosted AI
GROQ_API_KEY=YOUR_GROQ_API_KEY
GROQ_MODEL=openai/gpt-oss-20b

# Optional local Ollama configuration
OLLAMA_URL=http://127.0.0.1:11435/api/chat
OLLAMA_MODEL=gemma3:1b
```

Replace the placeholders with the actual credentials and configuration for your environment.

`NEO4J_DATABASE` defaults to `neo4j` when not specified. The database username can also be supplied through `NEO4J_USER` if required by the existing configuration.

The Ollama settings are optional and are only needed when using the local-model integration.

**Security requirements:**

- Never upload `.env` to GitHub.
- Never publish API keys or database passwords.
- Never place private credentials in source code.
- Use Streamlit Secrets for cloud deployment.

### 10.6 Test the Neo4j Connection

Run:

```powershell
python database.py
```

The connection utility verifies database connectivity and retrieves the graph node and relationship counts.

If the connection fails, check the Neo4j URI, username, password, database name, and network access.

### 10.7 Run the Application

```powershell
python -m streamlit run app.py
```

Open the local URL provided by Streamlit. The default address is:

```text
http://localhost:8501
```

---

## 11. Cloud Deployment

PhytoGraph is configured for deployment through **Streamlit Community Cloud**.

### Hosted Application

https://phytograph-research-atlas.streamlit.app/

### Deployment Configuration

| Setting | Value |
|---|---|
| Hosting platform | Streamlit Community Cloud |
| Source repository | GitHub |
| Branch | `main` |
| Main application file | `app.py` |
| Database | Neo4j |
| Hosted AI provider | Groq |
| Dependency file | `requirements.txt` |
| Secrets configuration | Streamlit Cloud Secrets |

### 11.1 Configure Streamlit Secrets

In the Streamlit Cloud application settings, add the required credentials in the Secrets section.

Example:

```toml
NEO4J_URI = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "YOUR_DATABASE_PASSWORD"
NEO4J_DATABASE = "neo4j"

GROQ_API_KEY = "YOUR_GROQ_API_KEY"
GROQ_MODEL = "openai/gpt-oss-20b"
```

Use actual private credentials in the platform's Secrets settings. Do not commit this configuration to the repository.

Cloud availability depends on Streamlit Community Cloud, Neo4j connectivity, Groq service availability, and the relevant provider limits.

---

## 12. Testing and Evaluation

The project has undergone development-stage testing of its database integration, graph retrieval, visualization, and scientific safeguards.

### 12.1 Development Checks

The current project evaluation records include:

| Evaluation Area | Recorded Result |
|---|---|
| Answerability safeguard tests | 13/13 passed |
| Graph retrieval benchmark | 12/12 questions completed |
| Relationships retrieved in retrieval benchmark | 48 |
| Missing source IDs in that retrieval benchmark | 0 |
| Initial answerability holdout | 11/16 (68.75%) |
| Post-fix retest on the same 16 questions | 16/16 |

### 12.2 Interpretation of Evaluation Results

These results represent internal development checks, not an independent scientific validation.

The retrieval benchmark evaluates whether the expected graph retrieval workflow executes and returns the recorded relationships. It does not establish the biological validity of those relationships.

The initial answerability holdout result was 11/16. After a detector correction, the same cases were retested and reached 16/16. Because the detector was modified after observing the initial failures, the post-fix result is a regression check rather than an independent holdout evaluation.

Human review of the reference answerability labels and evidence records remains incomplete.

### 12.3 Further Evaluation Required

A stronger evaluation would require:

- A larger independently labelled question set
- Independent scientific review of retrieved evidence
- Reference answers linked to original publications
- Retrieval precision and recall measurement
- Citation and source-faithfulness assessment
- Evaluation on questions not used during detector development
- Reproducible test scripts and documented evaluation artifacts

The current results should therefore be interpreted as evidence of selected software functionality, not proof of scientific accuracy or clinical predictive performance.

---

## 13. Scientific Limitations

PhytoGraph is an exploratory computational research prototype. Its findings must be interpreted within the limitations of the underlying dataset and methods.

1. **Incomplete biological coverage:** The knowledge graph represents a curated dataset, not every known medicinal plant, phytochemical, pathogen, or molecular target.

2. **Variable evidence quality:** Different relationships may be supported by different experimental methods and levels of evidence.

3. **Association versus proof:** A graph relationship does not automatically demonstrate a direct physical interaction, causal mechanism, or therapeutic effect.

4. **Experimental versus clinical evidence:** In-vitro antimicrobial activity, enzyme inhibition, docking predictions, and animal experiments cannot independently establish human clinical effectiveness.

5. **Exploratory ranking:** The Evidence Priority Score is a heuristic research index, not a calibrated probability or validated measure of treatment success.

6. **Publication independence:** Multiple relationship records may originate from the same publication. Independent source counts require careful deduplication and verification.

7. **Language model limitations:** AI-generated explanations may be incomplete or inaccurate even when graph evidence is retrieved and screening rules are applied.

8. **No clinical validation:** The application does not perform laboratory experiments, clinical trials, or patient-level treatment evaluation.

Scientific conclusions should be checked against the original publications and validated through appropriate experimental research.

---

## 14. Future Scope

Potential future improvements include:

- Expansion of evidence-verified medicinal plant and phytochemical records
- Further systematic compound–pathogen evidence mapping
- Additional pathogen–target relationship verification
- Improved publication provenance and source deduplication
- Validation of chemical identifiers and molecular structures
- More detailed experimental evidence classification
- Independent evaluation of GraphRAG retrieval performance
- Improved AI response and citation-faithfulness assessment
- Integration of molecular structures and experimentally validated target information
- Enhanced compound comparison and prioritization
- More comprehensive scientific review workflows
- Reproducible dataset update and evaluation pipelines

These are proposed research directions, not claims of currently completed functionality.

---

## 15. Project Status

PhytoGraph has progressed through dataset development, knowledge graph integration, evidence prioritization, AI-assisted retrieval, and web application implementation.

### Implemented Components

- 100 medicinal plant nodes
- 425 phytochemical compound nodes
- 24 pathogen/resistance records
- 49 molecular target nodes
- 4,299 mapped graph relationships
- Neo4j knowledge graph integration
- Evidence Priority Score for 137 compounds
- Compound directory and graph search
- Full knowledge graph visualization
- Compound-centred graph visualization
- GraphRAG-based evidence retrieval
- Groq-based AI explanation integration
- Optional Ollama integration
- Rule-based scientific answerability screening
- Streamlit web application
- GitHub source code repository
- Streamlit Community Cloud deployment configuration

The project remains an evolving research prototype. Additional deployment verification, systematic testing, and scientific evidence review are required.

---

## 16. Academic Disclaimer

This project is developed for academic research and educational demonstration.

PhytoGraph Research Atlas does not provide medical advice, prescribe treatments, establish drug safety, or certify the effectiveness of phytochemical compounds against antimicrobial-resistant infections.

Evidence Priority Scores and AI-generated explanations should be interpreted as research-supporting information only.

All scientific findings must be evaluated against their original sources and, where appropriate, validated through experimental and clinical research.

---

## 17. Project Information

**Project Title:**  
An AI-Assisted Knowledge Graph Framework for Identifying Anti-AMR Phytochemicals from Traditional Medicine

**Application Name:**  
PhytoGraph Research Atlas

**Research Domains:**
- Artificial Intelligence
- Knowledge Graphs
- Graph Retrieval-Augmented Generation
- Bioinformatics
- Phytochemistry
- Traditional Medicine
- Antimicrobial Resistance

**Repository:**  
https://github.com/nakshathravds25-ux/AI-Assisted-Anti-AMR-Phytochemical-KG

**Application:**  
https://phytograph-research-atlas.streamlit.app/
