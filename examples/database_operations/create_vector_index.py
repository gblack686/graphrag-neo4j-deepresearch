import neo4j
from neo4j_graphrag.indexes import create_vector_index
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add examples directory to Python path
examples_dir = Path(__file__).parent.parent
sys.path.append(str(examples_dir))

from utils import generate_vector_index_name

# Load environment variables
load_dotenv()

# Neo4j connection settings - using our working connection
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"

def generate_vector_index_name(
    label: str,
    property_name: str,
    dimensions: int,
    similarity: str
) -> str:
    """
    Generates a standardized name for vector indexes following the pattern:
    vector_[label]_[property]_[dimensions]_[similarity]
    
    Args:
        label (str): Node label the index is created for
        property_name (str): Name of the property containing the vector
        dimensions (int): Number of dimensions in the vector
        similarity (str): Similarity function used (e.g. 'cosine', 'euclidean')
    
    Returns:
        str: Generated index name
    """
    return f"vector_{label.lower()}_{property_name}_{dimensions}_{similarity}"

# Vector index configuration
DIMENSION = 1536  # OpenAI's embedding dimension
INDEX_NAME = generate_vector_index_name(
    label="Chunk",
    property_name="embedding",
    dimensions=DIMENSION,
    similarity="cosine"
)

def create_dune_vector_index():
    print(f"Creating vector index '{INDEX_NAME}'...")
    
    with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
        try:
            create_vector_index(
                driver,
                INDEX_NAME,
                label="Chunk",  # Using Chunk label since that's where our embeddings are
                embedding_property="embedding",  # Property name used in our graph
                dimensions=DIMENSION,
                similarity_fn="cosine"  # Using cosine similarity for semantic search
            )
            print(f"✓ Successfully created vector index '{INDEX_NAME}'")
        except Exception as e:
            print(f"✗ Error creating vector index: {str(e)}")

if __name__ == "__main__":
    create_dune_vector_index()
