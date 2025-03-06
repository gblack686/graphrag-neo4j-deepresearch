"""This example demonstrates how to use WeaviateNeo4jRetriever, ie vectors are
stored in the Weaviate database.

See the [README](./README.md) for more
information about how spin up a Weaviate and Neo4j databases if needed.

In this example, we are embeddings a text and provide a remote embeder to the
WeaviateNeo4jRetriever.
"""

from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import WeaviateNeo4jRetriever
from weaviate.connect.helpers import connect_to_local

NEO4J_URL = "neo4j://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")


def main() -> None:
    with GraphDatabase.driver(NEO4J_URL, auth=NEO4J_AUTH) as neo4j_driver:
        with connect_to_local() as w_client:
            retriever = WeaviateNeo4jRetriever(
                driver=neo4j_driver,
                client=w_client,
                collection="Jeopardy",
                id_property_external="neo4j_id",
                id_property_neo4j="id",
            )

            # Weaviate is configured to embed the text on the server side
            # see populate_dbs.py for the configuration
            res = retriever.search(query_text="biology", top_k=2)
            print(res)


if __name__ == "__main__":
    main()
