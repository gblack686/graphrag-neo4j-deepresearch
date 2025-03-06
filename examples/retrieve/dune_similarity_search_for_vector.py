"""This example demonstrates how to perform similarity search on our Dune knowledge graph
using a pre-computed vector query. It uses the Neo4j vector index to find relevant text chunks
based on vector similarity to the query vector.

Prerequisites:
    - Vector index must be created (using create_vector_index.py)
    - Text chunks must have embeddings stored in the 'embedding' property
"""

import os
import csv
import json
import time
from datetime import datetime
import neo4j
from neo4j_graphrag.retrievers import VectorRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create output directory structure
BASE_OUTPUT_DIR = "examples/retrieve/results"
RETRIEVER_TYPE = "vector_similarity_search"
CSV_DIR = os.path.join(BASE_OUTPUT_DIR, "csv", RETRIEVER_TYPE)
JSON_DIR = os.path.join(BASE_OUTPUT_DIR, "json", RETRIEVER_TYPE)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
logger.info(f"Output directories created: {CSV_DIR}, {JSON_DIR}")

# Example pre-computed vector (this would typically come from your embedding model)
# This is just a sample vector - replace with an actual embedding vector for better results
SAMPLE_QUERY_VECTOR = [0.1] * 1536  # OpenAI ada-002 embeddings are 1536-dimensional

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"
INDEX_NAME = "dune_vector_search"

def save_results(result, vector_desc, timings):
    """Save query results to both CSV and JSON files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"vector_search_{timestamp}"
    
    # Save as CSV
    csv_filename = os.path.join(CSV_DIR, f"{base_filename}.csv")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write metadata
        writer.writerow(['Vector Description:', vector_desc])
        writer.writerow(['Vector Dimensions:', len(SAMPLE_QUERY_VECTOR)])
        writer.writerow(['Timestamp:', timestamp])
        writer.writerow(['Retriever Type:', RETRIEVER_TYPE])
        writer.writerow(['Index Name:', INDEX_NAME])
        
        # Write timing information
        writer.writerow(['Timings (seconds):'])
        for key, value in timings.items():
            writer.writerow([f'{key}:', f'{value:.3f}'])
            
        writer.writerow([])  # Empty row for separation
        
        # Write headers
        writer.writerow(['Text', 'Score'])
        
        # Write data
        for item in result.items:
            score = item.metadata.get('score', 'N/A') if item.metadata else 'N/A'
            writer.writerow([item.content, score])
    
    # Save as JSON
    json_filename = os.path.join(JSON_DIR, f"{base_filename}.json")
    json_data = {
        'metadata': {
            'vector_description': vector_desc,
            'vector_dimensions': len(SAMPLE_QUERY_VECTOR),
            'timestamp': timestamp,
            'retriever_type': RETRIEVER_TYPE,
            'index_name': INDEX_NAME,
            'timings': timings
        },
        'results': [
            {
                'text': item.content,
                'score': item.metadata.get('score', 'N/A') if item.metadata else 'N/A'
            }
            for item in result.items
        ]
    }
    
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_data, jsonfile, indent=2)
    
    logger.info(f"Results saved to: {csv_filename} and {json_filename}")
    return csv_filename, json_filename

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    # Initialize the retriever
    retriever = VectorRetriever(
        driver=driver,
        index_name=INDEX_NAME,
        neo4j_database=DATABASE,
    )

    print("\nPerforming vector similarity search...")
    print("-" * 50)
    
    # Initialize timings
    timings = {
        'start_time': time.time(),
        'vector_search_time': 0,
        'total_time': 0
    }
    
    # Get results from the retriever
    search_start = time.time()
    result = retriever.search(query_vector=SAMPLE_QUERY_VECTOR, top_k=3)
    timings['vector_search_time'] = time.time() - search_start
    
    timings['total_time'] = time.time() - timings['start_time']
    
    # Save results to files
    vector_desc = "Sample uniform vector (all values 0.1)"
    csv_file, json_file = save_results(result, vector_desc, timings)
    
    # Print timing information
    print(f"\nTiming Information:")
    print(f"Vector Search: {timings['vector_search_time']:.3f}s")
    print(f"Total Time: {timings['total_time']:.3f}s")
    
    # Print results to console
    print(f"\nResults saved to:")
    print(f"CSV: {csv_file}")
    print(f"JSON: {json_file}")
    print("\nResults preview:")
    for item in list(result.items)[:3]:  # Show first 3 results
        print(f"\nText: {item.content}")
        if item.metadata and 'score' in item.metadata:
            print(f"Score: {item.metadata['score']:.4f}")

print(f"\nAll results have been saved to:")
print(f"CSV files: {CSV_DIR}")
print(f"JSON files: {JSON_DIR}") 