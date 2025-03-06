"""This example demonstrates how to perform vector cypher search on our Dune knowledge graph.
It uses vector similarity search combined with Cypher queries to find relevant text chunks and their connected context.

Prerequisites:
    - Vector index must be created (using create_vector_index.py)
    - Text chunks must have embeddings stored in the 'embedding' property
    - OpenAI API key must be set in environment variables
"""

import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import neo4j
import logging
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorCypherRetriever

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Create output directory structure
BASE_OUTPUT_DIR = "examples/retrieve/results"
RETRIEVER_TYPE = "vector_cypher_search"
CSV_DIR = os.path.join(BASE_OUTPUT_DIR, "csv", RETRIEVER_TYPE)
JSON_DIR = os.path.join(BASE_OUTPUT_DIR, "json", RETRIEVER_TYPE)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
logger.info(f"Output directories created: {CSV_DIR}, {JSON_DIR}")

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"
VECTOR_INDEX_NAME = "dune_vector_search"

# Retrieval query to get additional context through graph traversal
RETRIEVAL_QUERY = """
WITH node, score
MATCH (node)-[r]->(related)
RETURN node.text as content,
       node.entity_type as entityType,
       score as similarityScore,
       collect({
           relationship: type(r),
           relatedName: related.name,
           relatedType: labels(related)[0]
       }) as connections
"""

def save_results(result, query_text, timings):
    """Save query results to both CSV and JSON files"""
    # Create a clean filename from the query
    clean_query = "".join(c if c.isalnum() else "_" for c in query_text[:30])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{clean_query}_{timestamp}"
    
    # Save as CSV
    csv_filename = os.path.join(CSV_DIR, f"{base_filename}.csv")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write metadata
        writer.writerow(['Query:', query_text])
        writer.writerow(['Timestamp:', timestamp])
        writer.writerow(['Retriever Type:', RETRIEVER_TYPE])
        writer.writerow(['Vector Index:', VECTOR_INDEX_NAME])
        writer.writerow(['Total Runtime (s):', f"{timings['total']:.3f}"])
        writer.writerow(['Embedding Generation Time (s):', f"{timings['embedding']:.3f}"])
        writer.writerow(['Vector Search Time (s):', f"{timings['vector_search']:.3f}"])
        writer.writerow(['Cypher Execution Time (s):', f"{timings['cypher_execution']:.3f}"])
        writer.writerow([])  # Empty row for separation
        
        # Write headers
        writer.writerow(['Content', 'Entity Type', 'Similarity Score', 'Connected Entities'])
        
        # Write data
        for item in result.items:
            content = item.content
            metadata = item.metadata or {}
            connections = metadata.get('connections', [])
            connected_entities = "; ".join([
                f"{conn['relatedType']} {conn['relatedName']} ({conn['relationship']})"
                for conn in connections if conn['relatedName']
            ])
            writer.writerow([
                content,
                metadata.get('entityType', 'Unknown'),
                metadata.get('similarityScore', 'N/A'),
                connected_entities
            ])
    
    # Save as JSON
    json_filename = os.path.join(JSON_DIR, f"{base_filename}.json")
    json_data = {
        'metadata': {
            'query': query_text,
            'timestamp': timestamp,
            'retriever_type': RETRIEVER_TYPE,
            'vector_index': VECTOR_INDEX_NAME,
            'timings': {
                'total': round(timings['total'], 3),
                'embedding': round(timings['embedding'], 3),
                'vector_search': round(timings['vector_search'], 3),
                'cypher_execution': round(timings['cypher_execution'], 3)
            }
        },
        'results': [
            {
                'content': item.content,
                'entity_type': item.metadata.get('entityType', 'Unknown') if item.metadata else 'Unknown',
                'similarity_score': item.metadata.get('similarityScore', 'N/A') if item.metadata else 'N/A',
                'connections': [
                    {
                        'related_type': conn['relatedType'],
                        'related_name': conn['relatedName'],
                        'relationship': conn['relationship']
                    }
                    for conn in item.metadata.get('connections', []) if conn['relatedName']
                ] if item.metadata else []
            }
            for item in result.items
        ]
    }
    
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_data, jsonfile, indent=2)
    
    logger.info(f"Results saved to: {csv_filename} and {json_filename}")
    return csv_filename, json_filename

def process_query(retriever, query_text):
    """Process a query and save results"""
    logger.info(f"Processing query: {query_text}")
    print(f"\nProcessing query: {query_text}")
    print("-" * 50)
    
    try:
        # Initialize timings
        timings = {
            'start': time.time(),
            'embedding': 0,
            'vector_search': 0,
            'cypher_execution': 0,
            'total': 0
        }
        
        # Time embedding generation
        embedding_start = time.time()
        query_embedding = retriever.embedder.embed_query(query_text)
        timings['embedding'] = time.time() - embedding_start
        
        # Time vector search and cypher execution
        vector_start = time.time()
        with retriever.driver.session(database=retriever.neo4j_database) as session:
            # Vector search
            vector_query = retriever._build_vector_query(query_embedding)
            vector_result = session.run(vector_query)
            timings['vector_search'] = time.time() - vector_start
            
            # Cypher execution
            cypher_start = time.time()
            result = retriever.search(query_text=query_text, top_k=3)
            timings['cypher_execution'] = time.time() - cypher_start
        
        # Calculate total time
        timings['total'] = time.time() - timings['start']
        
        # Print timing information
        print(f"\nTiming Information:")
        print(f"Embedding Generation Time: {timings['embedding']:.3f}s")
        print(f"Vector Search Time: {timings['vector_search']:.3f}s")
        print(f"Cypher Execution Time: {timings['cypher_execution']:.3f}s")
        print(f"Total Time: {timings['total']:.3f}s")
        
        # Save results to files
        csv_file, json_file = save_results(result, query_text, timings)
        
        # Print results to console
        print(f"\nResults saved to:")
        print(f"CSV: {csv_file}")
        print(f"JSON: {json_file}")
        print("\nResults preview:")
        for item in list(result.items)[:3]:
            print(f"\nContent: {item.content}")
            if item.metadata:
                print(f"Entity Type: {item.metadata.get('entityType', 'Unknown')}")
                print(f"Similarity Score: {item.metadata.get('similarityScore', 'N/A'):.4f}")
                connections = item.metadata.get('connections', [])
                if connections:
                    print("Connected Entities:")
                    for conn in connections:
                        if conn.get('relatedName'):
                            print(f"- {conn['relatedType']} {conn['relatedName']} ({conn['relationship']})")
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        print(f"\nError processing query: {str(e)}")

logger.info("Starting vector cypher search script...")
with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    try:
        # Initialize the retriever
        retriever = VectorCypherRetriever(
            driver=driver,
            index_name=VECTOR_INDEX_NAME,
            embedder=OpenAIEmbeddings(
                model="text-embedding-ada-002",
                api_key=os.getenv("OPENAI_API_KEY")
            ),
            retrieval_query=RETRIEVAL_QUERY,
            neo4j_database=DATABASE,
        )

        # Example queries about Dune
        queries = [
            "Tell me about Paul Atreides and his relationships",
            "What is the connection between House Atreides and House Harkonnen?",
            "Describe the Bene Gesserit and their influence",
            "What is the significance of Arrakis and the spice?",
        ]
        
        # Process queries
        for query in queries:
            process_query(retriever, query)
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")

logger.info("Script completed")
print(f"\nAll results have been saved to:")
print(f"CSV files: {CSV_DIR}")
print(f"JSON files: {JSON_DIR}") 