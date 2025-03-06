"""This example demonstrates how to perform semantic similarity search on our Dune knowledge graph
using vector embeddings. It uses the Neo4j vector index to find relevant text chunks
based on semantic similarity to the query.

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
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create output directory structure
BASE_OUTPUT_DIR = "examples/retrieve/results"
RETRIEVER_TYPE = "similarity_search"
CSV_DIR = os.path.join(BASE_OUTPUT_DIR, "csv", RETRIEVER_TYPE)
JSON_DIR = os.path.join(BASE_OUTPUT_DIR, "json", RETRIEVER_TYPE)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
logger.info(f"Output directories created: {CSV_DIR}, {JSON_DIR}")

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"
INDEX_NAME = "dune_vector_search"

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
            'query': query_text,
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
    
    return csv_filename, json_filename

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    # Initialize the retriever
    retriever = VectorRetriever(
        driver=driver,
        index_name=INDEX_NAME,
        embedder=OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=os.getenv("OPENAI_API_KEY")
        ),
        neo4j_database=DATABASE
    )

    # Example queries about Dune
    queries = [
        "Who is Paul Atreides?",
        "What is House Atreides' relationship with planet Caladan?",
        "Who are Paul's parents?",
        "What is known about Caladan's climate?"
    ]
    
    # Process each query and save results
    for query_text in queries:
        print(f"\nProcessing query: {query_text}")
        print("-" * 50)
        
        # Initialize timings
        timings = {
            'start_time': time.time(),
            'embedding_time': 0,
            'vector_search_time': 0,
            'total_time': 0
        }
        
        # Get results from the retriever
        embedding_start = time.time()
        query_embedding = retriever.embedder.embed_query(query_text)
        timings['embedding_time'] = time.time() - embedding_start
        
        vector_start = time.time()
        result = retriever.search(query_text=query_text, top_k=3)
        timings['vector_search_time'] = time.time() - vector_start
        
        timings['total_time'] = time.time() - timings['start_time']
        
        # Save results to files
        csv_file, json_file = save_results(result, query_text, timings)
        
        # Print results and timing information to console
        print(f"\nTiming Information:")
        print(f"Embedding Generation: {timings['embedding_time']:.3f}s")
        print(f"Vector Search: {timings['vector_search_time']:.3f}s")
        print(f"Total Time: {timings['total_time']:.3f}s")
        
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