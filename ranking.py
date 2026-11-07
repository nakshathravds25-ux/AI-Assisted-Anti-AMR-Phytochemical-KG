
from pathlib import Path
import pandas as pd

RANKING_FILE = (
    Path(__file__).parent
    / "data"
    / "V3_EVIDENCE_PRIORITIZATION_137.csv"
)


def load_rankings():
    if not RANKING_FILE.exists():
        raise FileNotFoundError(
            f"Ranking file not found: {RANKING_FILE}"
        )

    df = pd.read_csv(RANKING_FILE)

    print("Ranking columns:", df.columns.tolist())
    print("Ranked compounds:", len(df))

    return df


if __name__ == "__main__":
    rankings = load_rankings()
    print(rankings.head(10).to_string(index=False))
