
import os
import re

from dotenv import load_dotenv
from database import get_driver, _secret
from ranking import load_rankings

load_dotenv()

DATABASE = _secret("NEO4J_DATABASE", "neo4j")


# Common scientific names and their abbreviations.
# These are matching aliases, not new graph evidence.
ENTITY_ALIASES = {
    "Escherichia coli": [
        "Escherichia coli",
        "E. coli",
        "E coli",
    ],
    "Klebsiella pneumoniae": [
        "Klebsiella pneumoniae",
        "K. pneumoniae",
        "K pneumoniae",
    ],
    "New Delhi metallo-beta-lactamase 1": [
        "NDM-1",
        "NDM1",
        "New Delhi metallo-beta-lactamase",
    ],
    "OXA-48": ["OXA-48", "OXA48"],
    "KPC-2": ["KPC-2", "KPC2"],
    "PBP2a": ["PBP2a"],
    "NorA": ["NorA"],
    "AcrB": ["AcrB"],
    "FtsZ": ["FtsZ"],
    "LasR": ["LasR"],
    "RhlR": ["RhlR"],
}

TARGET_TERMS = [
    "NDM-1",
    "OXA-48",
    "KPC-2",
    "PBP2a",
    "NorA",
    "AcrB",
    "FtsZ",
    "LasR",
    "RhlR",
]

PUBLICATION_TERMS = [
    "publication",
    "publications",
    "independent studies",
    "independent papers",
    "independent sources",
    "distinct studies",
    "distinct papers",
    "unique sources",
    "same paper",
    "same study",
]


def contains_term(text, term):
    """Match a scientific name without matching inside another word."""

    pattern = (
        r"(?<![A-Za-z0-9])"
        + re.escape(term)
        + r"(?![A-Za-z0-9])"
    )

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE
    ) is not None


def retrieve_compound_evidence(compound_id):
    """
    Retrieve mapped pathogen and target relationships.

    The returned dictionary keys are kept compatible with
    the existing Ollama and Streamlit modules.
    """

    query = """
    MATCH (c:Compound {Compound_ID: $compound_id})
    MATCH (c)-[r]->(entity)
    WHERE type(r) IN [
        'ACTS_AGAINST_PATHOGEN',
        'INTERACTS_WITH_TARGET'
    ]

    RETURN
        c.Compound_Name AS compound,
        type(r) AS relationship,

        CASE
            WHEN entity:Target THEN entity.Target_Name
            WHEN entity:Pathogen THEN entity.Organism
        END AS entity,

        r.Evidence_Type AS evidence_type,
        r.Activity_Type AS activity,
        r.Biological_Evidence_Category AS category,
        r.Finding AS finding,
        toString(r.Source_URL) AS source,
        r.Link_ID AS link_id

    ORDER BY relationship, entity
    """

    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            result = session.run(
                query,
                compound_id=compound_id
            )
            return [dict(row) for row in result]


def retrieve_target_compounds(target_name):
    """Retrieve mapped compounds for a molecular target."""

    query = """
    MATCH (c:Compound)-[r:INTERACTS_WITH_TARGET]->(t:Target)

    WHERE toLower(t.Target_Name)
          CONTAINS toLower($target)

    RETURN
        c.Compound_Name AS compound,
        'INTERACTS_WITH_TARGET' AS relationship,
        t.Target_Name AS entity,
        r.Evidence_Type AS evidence_type,
        null AS activity,
        r.Biological_Evidence_Category AS category,
        r.Finding AS finding,
        toString(r.Source_URL) AS source,
        r.Link_ID AS link_id

    ORDER BY compound
    LIMIT 50
    """

    with get_driver() as driver:
        with driver.session(database=DATABASE) as session:
            result = session.run(
                query,
                target=target_name
            )
            return [dict(row) for row in result]


def find_compound(question, rankings):
    """Identify a compound mentioned in the question."""

    if not {"Compound_ID", "Compound"}.issubset(
        rankings.columns
    ):
        raise ValueError(
            "Ranking file must contain Compound_ID and Compound"
        )

    compounds = sorted(
        rankings[
            ["Compound_ID", "Compound"]
        ].dropna().itertuples(
            index=False,
            name=None
        ),
        key=lambda item: len(str(item[1])),
        reverse=True
    )

    for compound_id, compound_name in compounds:
        name = str(compound_name).strip()

        if len(name) < 3:
            continue

        if contains_term(question, name):
            return compound_id, name

    return None, None


def find_entity_mentions(question):
    """
    Identify pathogen or target names mentioned in a question.

    A single scientific entity may have several common aliases.
    """

    matches = []

    for canonical, aliases in ENTITY_ALIASES.items():
        for alias in aliases:
            if contains_term(question, alias):
                matches.append(canonical)
                break

    return matches


def evidence_matches_entity(record, canonical):
    """
    Match the question's entity against a retrieved graph node.

    The matching is based on the entity name and its aliases.
    It does not infer an experimental relationship from text.
    """

    entity = str(record.get("entity") or "")

    aliases = ENTITY_ALIASES.get(
        canonical,
        [canonical]
    )

    return any(
        contains_term(entity, alias)
        for alias in aliases
    )


def is_publication_question(question):
    """Determine whether all evidence sources need comparison."""

    return any(
        term in question.casefold()
        for term in PUBLICATION_TERMS
    )


def filter_relevant_evidence(evidence, question):
    """
    Return question-specific evidence.

    General compound questions retain all mapped relationships.
    Specific pathogen/target questions retain direct matches.
    Publication-comparison questions retain all relationships.
    """

    evidence = list(evidence or [])

    if not evidence:
        return [], False

    if is_publication_question(question):
        return evidence, False

    mentioned_entities = find_entity_mentions(question)

    if not mentioned_entities:
        return evidence, False

    filtered = [
        record
        for record in evidence
        if any(
            evidence_matches_entity(record, entity)
            for entity in mentioned_entities
        )
    ]

    # Even when no match exists, keep filtering active.
    # Do not substitute unrelated relationships as evidence.
    return filtered, True


def answer_question(question):
    """
    Retrieve evidence for a scientific research question.

    Returns:
        (summary: str, evidence: list[dict])

    Compatible with:
        app.py
        ollama_engine.py
        evaluation/evaluate_graphrag.py
    """

    if not isinstance(question, str) or not question.strip():
        return "Please enter a research question.", []

    question = question.strip()

    rankings = load_rankings()

    # --------------------------------------------------
    # 1. Compound-based retrieval
    # --------------------------------------------------

    compound_id, compound_name = find_compound(
        question,
        rankings
    )

    if compound_id is not None:

        all_evidence = retrieve_compound_evidence(
            compound_id
        )

        if not all_evidence:
            return (
                f"No mapped pathogen or target evidence "
                f"was found for {compound_name}.",
                []
            )

        evidence, specific = filter_relevant_evidence(
            all_evidence,
            question
        )

        if not evidence and specific:
            return (
                f"No direct mapped relationship was found "
                f"for {compound_name} and the specific "
                f"pathogen or target mentioned in your question. "
                f"This does not establish that no biological "
                f"relationship exists.",
                []
            )

        if specific:
            summary = (
                f"Found {len(evidence)} question-specific "
                f"evidence relationship(s) for "
                f"{compound_name}. Review the findings and "
                f"publication sources. These records do not "
                f"establish clinical effectiveness."
            )

        elif is_publication_question(question):
            summary = (
                f"Retrieved {len(evidence)} relationships "
                f"for {compound_name} for publication-source "
                f"comparison. Multiple relationships may "
                f"originate from the same publication. "
                f"Check source identifiers before counting "
                f"independent studies."
            )

        else:
            summary = (
                f"Found {len(evidence)} evidence relationships "
                f"for {compound_name}. Review the findings "
                f"and publication sources below. These "
                f"relationships do not by themselves "
                f"establish clinical effectiveness."
            )

        return summary, evidence

    # --------------------------------------------------
    # 2. Target-based retrieval
    # --------------------------------------------------

    for target in TARGET_TERMS:

        aliases = ENTITY_ALIASES.get(
            target,
            [target]
        )

        if any(
            contains_term(question, alias)
            for alias in aliases
        ):

            evidence = retrieve_target_compounds(
                target
            )

            if not evidence:
                return (
                    f"No mapped compound-target relationships "
                    f"were found for {target}.",
                    []
                )

            return (
                f"Found {len(evidence)} mapped "
                f"compound-target relationships for "
                f"{target}. The retrieved records may "
                f"contain different levels of evidence. "
                f"These relationships do not establish "
                f"clinical effectiveness.",
                evidence
            )

    # --------------------------------------------------
    # 3. No supported entity identified
    # --------------------------------------------------

    return (
        "I could not identify a supported compound or "
        "molecular target in this question. Try asking "
        "about Isoliquiritin, Eugenol, Quercetin, "
        "NDM-1 or OXA-48.",
        []
    )
