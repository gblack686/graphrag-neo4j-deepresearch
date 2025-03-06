import neo4j
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")

# Index configurations
FULLTEXT_INDEX_NAME = "dune_text_search"
VECTOR_INDEX_NAME = "dune_vector_search"
DIMENSION = 1536  # OpenAI's embedding dimension

def create_indexes():
    print("Creating indexes for the Dune knowledge graph...")
    
    with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
        # Create fulltext indexes for each entity type
        entity_configs = [
            ("Person", ["name"]),
            ("House", ["name"]),
            ("Planet", ["name", "weather"])
        ]
        
        for label, properties in entity_configs:
            index_name = f"{label.lower()}_fulltext"
            print(f"\nCreating fulltext index '{index_name}' for {label} nodes...")
            try:
                create_fulltext_index(
                    driver,
                    index_name,
                    label=label,
                    node_properties=properties
                )
                print(f"✓ Successfully created fulltext index for {label}")
            except Exception as e:
                print(f"✗ Error creating fulltext index for {label}: {str(e)}")
        
        # Create vector index for semantic search
        print(f"\nCreating vector index '{VECTOR_INDEX_NAME}'...")
        try:
            create_vector_index(
                driver,
                VECTOR_INDEX_NAME,
                label="Chunk",  # The text chunks we created have embeddings
                embedding_property="embedding",
                dimensions=DIMENSION,
                similarity_fn="cosine"  # Using cosine similarity for semantic search
            )
            print("✓ Successfully created vector index")
        except Exception as e:
            print(f"✗ Error creating vector index: {str(e)}")

if __name__ == "__main__":
    create_indexes()
