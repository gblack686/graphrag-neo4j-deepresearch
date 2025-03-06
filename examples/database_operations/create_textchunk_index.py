"""This script creates a fulltext index for TextChunk nodes in the Neo4j database.
This index is required for hybrid search functionality.
"""

import neo4j
from neo4j_graphrag.indexes import create_fulltext_index
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"

# Index configuration
INDEX_NAME = "textchunk_fulltext"
LABEL = "TextChunk"
PROPERTIES = ["text"]

print(f"Creating fulltext index '{INDEX_NAME}' for {LABEL} nodes...")

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    try:
        create_fulltext_index(
            driver,
            name=INDEX_NAME,
            label=LABEL,
            node_properties=PROPERTIES
        )
        print(f"✓ Successfully created fulltext index for {LABEL}")
        
        # Wait for index to be online
        with driver.session(database=DATABASE) as session:
            print("Waiting for index to be online...")
            session.run("CALL db.awaitIndexes()")
            print("Index is now online and ready to use")
            
    except Exception as e:
        print(f"✗ Error creating fulltext index: {str(e)}") 