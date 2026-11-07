"""Neo4j driver: supports .env locally and Streamlit secrets on Cloud."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def _secret(name, default=None):
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except (ImportError, FileNotFoundError, RuntimeError, KeyError, AttributeError):
        return default


def get_driver():
    uri = _secret("NEO4J_URI", "bolt://127.0.0.1:7687")
    username = _secret("NEO4J_USERNAME", _secret("NEO4J_USER", "neo4j"))
    password = _secret("NEO4J_PASSWORD")
    if not password:
        raise ValueError("NEO4J_PASSWORD is not configured. Use .env locally or Streamlit secrets.")
    return GraphDatabase.driver(uri, auth=(username, password), connection_timeout=10)


def test_connection():
    with get_driver() as driver:
        driver.verify_connectivity()
        with driver.session(database=_secret("NEO4J_DATABASE", "neo4j")) as session:
            record = session.run("""
                MATCH (n) WITH count(n) AS nodes
                OPTIONAL MATCH ()-[r]->()
                RETURN nodes, count(r) AS relationships
            """).single()
            return dict(record)


if __name__ == "__main__":
    print(test_connection())
