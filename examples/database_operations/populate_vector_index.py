"""
This script demonstrates how to populate or update vector embeddings in a Neo4j database.
It uses the upsert_vector function to either:
- Insert a new vector embedding if the node doesn't exist
- Update an existing vector embedding if the node exists

Use Cases:
- Adding embeddings to nodes that were created without them
- Updating embeddings when using a new embedding model
- Manually inserting embeddings for specific nodes

Parameters:
    id: The unique identifier of the node to update
    embedding_property: The name of the property that stores the vector embedding
    vector: The actual embedding values as a list of floats

Example Usage:
    # Update a single node's embedding
    upsert_vector(driver, node_id=123, property_name="embedding", 
                 vector=[0.1, 0.2, ...])

    # Batch update multiple nodes
    for node_id, embedding in embeddings_dict.items():
        upsert_vector(driver, node_id, "embedding", embedding)

Note: Make sure the vector dimensions match the vector index configuration.
      For example, if using OpenAI embeddings, the vector should be 1536-dimensional.
"""

import neo4j
from neo4j_graphrag.indexes import upsert_vector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Neo4j connection settings - using our working connection
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"

def update_node_embedding(node_id: int, embedding: list[float]):
    """
    Updates or inserts an embedding for a specific node.

    Args:
        node_id (int): The ID of the node to update
        embedding (list[float]): The vector embedding to store
                               Should be 1536-dimensional for OpenAI embeddings

    Raises:
        Exception: If the connection fails or the vector dimensions don't match the index
    """
    print(f"Updating embedding for node {node_id}...")
    
    with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            upsert_vector(
                driver=driver,
                id=node_id,
                embedding_property="embedding",  # Must match the property name in vector index
                vector=embedding
            )
            print(f"✓ Successfully updated embedding for node {node_id}")
        except Exception as e:
            print(f"✗ Error updating embedding: {str(e)}")

if __name__ == "__main__":
    # Example usage with a sample 1536-dimensional vector
    # In practice, you would get this from an embedding model
    sample_id = 1
    sample_vector = [0.0] * 1536  # Placeholder vector of correct dimension
    
    update_node_embedding(sample_id, sample_vector)
