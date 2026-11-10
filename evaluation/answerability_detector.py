
"""
Anti-AMR GraphRAG Answerability Detector
Phase 6.7 — Scientific Safeguards

Rule-based evidence sufficiency screening.

Distinguishes:
- Experimental evidence from human clinical outcomes
- Indirect target associations from direct binding
- MIC from IC50 and FICI
- Publication relationships from independent studies

This is NOT an automated scientific fact-checker.
"""

import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"

EVIDENCE_FILE = RESULTS / "evidence_20261106_105217.json"
REFERENCE_FILE = RESULTS / "answerability_review.csv"
OUTPUT_FILE = RESULTS / "answerability_predictions.csv"


def matches_any(text, patterns):
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def evidence_text(record):
    return " ".join(
        str(record.get(key) or "")
        for key in (
            "evidence_type",
            "category",
            "activity",
            "finding",
        )
    ).casefold()


def has_human_outcome_evidence(records):
    """
    Flag possible patient-level clinical evidence.

    Clinical bacterial isolates, mouse studies and
    in-vitro assays are NOT patient outcome studies.

    Any positive result still requires manual review.
    """
    patterns = [
        r"\brandomi[sz]ed clinical trial\b",
        r"\bclinical trial\b",
        r"\bclinical cure rate\b",
        r"\bpatient cure rate\b",
        r"\bpatient survival\b",
        r"\bhuman mortality\b",
        r"\bclinical efficacy in patients\b",
        r"\bpatients? (?:received|treated with)\b",
    ]

    return any(
        matches_any(evidence_text(record), patterns)
        for record in records
    )


def asks_human_clinical_outcome(question):
    q = question.casefold()

    patterns = [
        r"\bclinical (?:effectiveness|efficacy|cure|outcomes?|benefit)\b",
        r"\bclinically (?:proven|effective|validated|established)\b",
        r"\bclinical(?:ly)? established dose\b",
        r"\b(?:human|patient) (?:cure|recovery|survival|mortality) rate\b",
        r"\b(?:cure|treat|heal|save) (?:human )?patients?\b",
        r"\b(?:cures?|treats?|heals?) .{0,80}\bpatients?\b",
        r"\bpatients? .{0,60}\b(?:treated|cured|recovered)\b",
        r"\bsurvival rate\b",
        r"\bmortality\b",
        r"\b(?:people|humans?|patients?) .{0,80}\b(?:survive|recover|benefit)\b",
        r"\b(?:successful|effective) treatment of (?:human )?patients?\b",
        r"\bsuccessful treatment .{0,60}\bhuman patients?\b",
        r"\btherapeutic efficacy .{0,60}\bhuman\b",
        r"\bhuman (?:clinical )?(?:trials?|outcomes?|efficacy)\b",
        r"\bpatient outcomes?\b",
        r"\bpatient survival\b",
        r"\bproven human\b",
        # Clinical-treatment language may place 'humans' after the disease,
        # e.g. 'Does Kaempferol cure resistant infections in humans?'
        r"\b(?:cures?|treats?|heals?|prevents?|clears?|eradicates?)\b.{0,140}\b(?:humans?|patients?|people)\b",
        # Also catch questions phrased with the patient group first.
        r"\b(?:humans?|patients?|people)\b.{0,140}\b(?:cures?|cured|treats?|treated|heals?|healed|recovers?|recover|survives?|survive|benefits?)\b",
        # Clinical effectiveness or safety questions are patient outcomes too.
        r"\b(?:effective|efficacious|safe|works?)\b.{0,100}\b(?:in|for|among)\s+(?:humans?|patients?|people)\b",
        r"\b(?:humans?|patients?|people)\b.{0,100}\b(?:effective|efficacious|safe)\b",
    ]

    return matches_any(q, patterns)


def asks_direct_binding(question):
    q = question.casefold()

    direct = matches_any(q, [
        r"\bdirect (?:physical )?bind(?:ing)?\b",
        r"\bdirectly bind\b",
        r"\bphysical binding\b",
        r"\bphysically binds?\b",
        r"\bbinding (?:to|with)\b",
    ])

    proof = matches_any(q, [
        r"\bprove\b",
        r"\bproven\b",
        r"\bdemonstrate\b",
        r"\bconfirm\b",
        r"\bestablish\b",
        r"\bshow\b",
        r"\bdoes\b",
        r"\bis\b",
        r"\bdirect\b",
    ])

    return direct and proof



def has_direct_binding_evidence(records):
    """
    Check for explicit direct-binding assay descriptions.

    Negated descriptions such as "No direct binding assay
    described" must not be treated as positive evidence.

    This is a screening heuristic, not confirmation
    that the cited experiment demonstrates binding.
    """
    patterns = [
        r"\bsurface plasmon resonance\b",
        r"\bisothermal titration calorimetry\b",
        r"\bmicroscale thermophoresis\b",
        r"\bbio-layer interferometry\b",
        r"\bdirect binding assay\b",
        r"\bmeasured binding affinity\b",
    ]

    negation_patterns = [
        r"\bno\b",
        r"\bnot\b",
        r"\bnever\b",
        r"\bwithout\b",
        r"\babsence of\b",
        r"\black of\b",
        r"\bdidn't\b",
        r"\bdoesn't\b",
        r"\bdon't\b",
        r"\bwasn't\b",
        r"\bweren't\b",
        r"\bisn't\b",
        r"\baren't\b",
        r"\bhasn't\b",
        r"\bhaven't\b",
        r"\bcan't\b",
    ]

    for record in records:
        text = evidence_text(record)

        # Separate independent clauses so that a negation
        # does not automatically cancel a positive finding
        # in a different clause.
        clauses = re.split(
            r"(?<=[.!?;,])\s+|\b(?:but|however|although|whereas|yet)\b",
            text,
            flags=re.IGNORECASE
        )

        for clause in clauses:
            if not matches_any(clause, patterns):
                continue

            # Ignore assay mentions explicitly described
            # as absent, unreported or not performed.
            if matches_any(clause, negation_patterns):
                continue

            return True

    return False



def has_publication_identifiers(records):
    return bool(records) and all(
        str(r.get("source") or "").strip()
        for r in records
    )


def detect_answerability(question, evidence):
    """
    Return (classification, explanation).

    SUPPORTED:
        Relevant evidence was retrieved for the question.

    INSUFFICIENT:
        The specific requested claim is not established
        by the supplied records.

    REVIEW_REQUIRED:
        Potential evidence exists but needs expert review.

    SUPPORTED does not mean clinically proven or
    scientifically verified.
    """

    q = str(question or "").casefold()
    records = list(evidence or [])

    if not records:
        return (
            "INSUFFICIENT",
            "No relevant evidence records were retrieved."
        )

    # 1. Human outcomes and clinical efficacy
    if asks_human_clinical_outcome(q):
        if has_human_outcome_evidence(records):
            return (
                "REVIEW_REQUIRED",
                "Possible patient-level clinical evidence "
                "was detected. Verify the original study, "
                "population, intervention, outcome and dose."
            )

        return (
            "INSUFFICIENT",
            "The retrieved evidence does not establish "
            "human clinical effectiveness, mortality "
            "benefit, cure rate or clinically validated "
            "curative dose. In-vitro results, clinical "
            "bacterial isolates and animal studies "
            "cannot independently establish these outcomes."
        )

    # 2. Direct physical target binding
    if asks_direct_binding(q):
        if has_direct_binding_evidence(records):
            return (
                "REVIEW_REQUIRED",
                "A potential direct-binding experiment "
                "was mentioned. The original publication "
                "must be reviewed before confirming binding."
            )

        return (
            "INSUFFICIENT",
            "The retrieved records do not demonstrate "
            "direct physical binding to the target. "
            "Efflux assays, gene-expression changes, "
            "antibiotic synergy and docking predictions "
            "do not independently establish binding."
        )

    # 3. Publication independence
    publication_terms = [
        "independent publication",
        "independent studies",
        "independent papers",
        "distinct publication",
        "distinct studies",
        "same publication",
        "same paper",
        "same study",
        "unique sources",
    ]

    if any(term in q for term in publication_terms):
        if has_publication_identifiers(records):
            return (
                "SUPPORTED",
                "Source identifiers are available for "
                "publication comparison. Identifier "
                "accuracy still requires verification."
            )

        return (
            "REVIEW_REQUIRED",
            "Publication provenance is incomplete."
        )

    # 4. Minimum inhibitory concentration
    asks_mic = matches_any(q, [
        r"\bMIC\b",
        r"\bminimum inhibitory concentration\b",
    ])

    if asks_mic:
        if matches_any(q, [
            r"\bevery\b",
            r"\ball\b",
            r"\beach\b",
            r"\bcomplete\b",
            r"\bentire\b",
        ]):
            return (
                "INSUFFICIENT",
                "Comprehensive pathogen-specific MIC "
                "measurements are not established by "
                "these retrieved records."
            )

        pattern = (
            r"\bMIC\b\s*(?:of|=|:|was)?\s*"
            r"\d+(?:\.\d+)?"
        )

        has_mic = any(
            re.search(
                pattern,
                str(r.get("finding") or ""),
                re.IGNORECASE
            )
            for r in records
        )

        if has_mic:
            return (
                "REVIEW_REQUIRED",
                "A possible MIC measurement was found. "
                "Check the organism, strain, units, "
                "experimental conditions and publication."
            )

        return (
            "INSUFFICIENT",
            "No explicit MIC measurement for the "
            "requested context was identified. "
            "IC50 and FICI are not interchangeable "
            "with MIC."
        )

    # 5. General experimental or mechanistic evidence
    return (
        "SUPPORTED",
        "Relevant knowledge graph records were "
        "retrieved. This classification does not "
        "verify individual claims, demonstrate "
        "direct binding, or establish clinical efficacy."
    )


def load_reference_labels():
    labels = {}

    if not REFERENCE_FILE.exists():
        return labels

    with REFERENCE_FILE.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            labels[row["question_id"]] = row.get(
                "reference_answerability", ""
            )

    return labels


def main():
    if not EVIDENCE_FILE.exists():
        print("ERROR: Evidence JSON not found:")
        print(EVIDENCE_FILE)
        return

    with EVIDENCE_FILE.open(encoding="utf-8") as f:
        dataset = json.load(f)

    reference = load_reference_labels()
    rows = []

    print("=" * 60)
    print("ANTI-AMR ANSWERABILITY EVALUATION")
    print("=" * 60)

    for qid, item in dataset.items():
        question = item.get("question", "")
        records = item.get("evidence", [])

        prediction, reason = detect_answerability(
            question, records
        )

        expected = reference.get(qid, "")
        match = (
            prediction == expected if expected else None
        )

        print(
            f"{qid}: predicted={prediction}, "
            f"reference={expected or 'N/A'}, "
            f"match={match}"
        )

        rows.append({
            "question_id": qid,
            "question": question,
            "evidence_count": len(records),
            "predicted_answerability": prediction,
            "reference_answerability": expected,
            "matches_reference": match,
            "prediction_reason": reason,
        })

    if not rows:
        print("No evaluation records found.")
        return

    RESULTS.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0])
        )
        writer.writeheader()
        writer.writerows(rows)

    reviewed = [
        row for row in rows
        if row["reference_answerability"]
    ]

    correct = sum(
        row["matches_reference"] is True
        for row in reviewed
    )

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print("Total questions:", len(rows))
    print("Reference-labeled:", len(reviewed))
    print("Matches:", correct)

    if reviewed:
        print(
            "Agreement:",
            f"{100 * correct / len(reviewed):.1f}%"
        )

    print("Saved:", OUTPUT_FILE)
    print(
        "NOTE: This is a development/regression "
        "evaluation, not independent scientific accuracy."
    )


if __name__ == "__main__":
    main()
