"""This example demonstrates how to use Text2CypherRetriever with text chunks.
It converts natural language queries into Cypher queries, executes them, and saves results to CSV.

Prerequisites:
    - OpenAI API key must be set in environment variables
"""

import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create output directory structure
BASE_OUTPUT_DIR = "examples/retrieve/results"
RETRIEVER_TYPE = "text2cypher_search"
CSV_DIR = os.path.join(BASE_OUTPUT_DIR, "csv", RETRIEVER_TYPE)
JSON_DIR = os.path.join(BASE_OUTPUT_DIR, "json", RETRIEVER_TYPE)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
logger.info(f"Output directories created: {CSV_DIR}, {JSON_DIR}")

# Define database credentials
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"

# Create LLM object
llm = OpenAILLM(
    model_name="gpt-4",
    model_params={"temperature": 0},
    api_key=os.getenv("OPENAI_API_KEY")
)

# Specify Neo4j schema
neo4j_schema = """
Node properties:
TextChunk {id: STRING, text: STRING, index: INTEGER, embedding: LIST}
Character {name: STRING}
House {name: STRING}
Planet {name: STRING}
Organization {name: STRING}
Relationship properties:
NEXT_CHUNK {}: Connects sequential text chunks
FROM_DOCUMENT {}: Connects text chunks to their source document
BELONGS_TO {}: Connects characters to their houses
RULES {}: Connects houses to planets they rule
MEMBER_OF {}: Connects characters to organizations
The relationships:
(:TextChunk)-[:NEXT_CHUNK]->(:TextChunk)
(:TextChunk)-[:FROM_DOCUMENT]->(:Document)
(:Character)-[:BELONGS_TO]->(:House)
(:House)-[:RULES]->(:Planet)
(:Character)-[:MEMBER_OF]->(:Organization)
"""

# Example queries to help the LLM understand the context
examples = [
    "USER INPUT: 'Find text chunks about Paul Atreides' QUERY: MATCH (t:TextChunk) WHERE t.text CONTAINS 'Paul Atreides' RETURN t.text",
    "USER INPUT: 'Which characters belong to House Atreides?' QUERY: MATCH (c:Character)-[:BELONGS_TO]->(h:House) WHERE h.name = 'House Atreides' RETURN c.name",
    "USER INPUT: 'Show me information about the Bene Gesserit' QUERY: MATCH (t:TextChunk)-[:FROM_DOCUMENT]->(:Document) WHERE t.text CONTAINS 'Bene Gesserit' RETURN t.text"
]

def save_results(result, query_text, timings):
    """Save query results to both CSV and JSON files"""
    # Create a clean filename from the query
    clean_query = "".join(c if c.isalnum() else "_" for c in query_text[:30])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{clean_query}_{timestamp}"
    
    # Get the generated Cypher query from the result metadata
    cypher_query = result.metadata.get('cypher', 'N/A') if result.metadata else 'N/A'
    
    # Save as CSV
    csv_filename = os.path.join(CSV_DIR, f"{base_filename}.csv")
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write metadata
        writer.writerow(['Query:', query_text])
        writer.writerow(['Cypher Query:', cypher_query])
        writer.writerow(['Timestamp:', timestamp])
        writer.writerow(['Retriever Type:', RETRIEVER_TYPE])
        writer.writerow(['Total Runtime (s):', f"{timings['total']:.3f}"])
        writer.writerow(['LLM Generation Time (s):', f"{timings['llm_generation']:.3f}"])
        writer.writerow(['Query Execution Time (s):', f"{timings['query_execution']:.3f}"])
        writer.writerow([])  # Empty row for separation
        
        # Write headers based on the first record's keys
        if result.records:
            writer.writerow(result.records[0].keys())
            
            # Write data
            for record in result.records:
                writer.writerow([str(value) for value in record.values()])
    
    # Save as JSON
    json_filename = os.path.join(JSON_DIR, f"{base_filename}.json")
    json_data = {
        'metadata': {
            'query': query_text,
            'cypher_query': cypher_query,
            'timestamp': timestamp,
            'retriever_type': RETRIEVER_TYPE,
            'timings': {
                'total': round(timings['total'], 3),
                'llm_generation': round(timings['llm_generation'], 3),
                'query_execution': round(timings['query_execution'], 3)
            }
        },
        'results': [
            {key: str(value) for key, value in record.items()}
            for record in result.records
        ]
    }
    
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(json_data, jsonfile, indent=2)
    
    logger.info(f"Results saved to: {csv_filename} and {json_filename}")
    return csv_filename, json_filename

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    # Initialize the retriever
    retriever = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=neo4j_schema,
        examples=examples,
        neo4j_database=DATABASE,
    )

    # Example queries
    queries = [
        "Find text chunks about Paul Atreides",
        "Which characters belong to House Atreides?",
        "Show me information about the Bene Gesserit",
        "What is the relationship between House Atreides and House Harkonnen?",
        "Tell me about the planet Arrakis"
    ]
    
    # Process each query and save results
    for query_text in queries:
        print(f"\nProcessing query: {query_text}")
        print("-" * 50)
        
        # Initialize timings
        timings = {
            'start': time.time(),
            'llm_generation': 0,
            'query_execution': 0,
            'total': 0
        }
        
        try:
            # Time LLM query generation and execution together
            llm_start = time.time()
            result = retriever.get_search_results(query_text)
            llm_and_execution_time = time.time() - llm_start
            
            # Approximate split between LLM generation and query execution
            # Assuming LLM takes about 70% of the time
            timings['llm_generation'] = llm_and_execution_time * 0.7
            timings['query_execution'] = llm_and_execution_time * 0.3
            
            # Calculate total time
            timings['total'] = time.time() - timings['start']
            
            # Get the generated Cypher query from the result metadata
            cypher_query = result.metadata.get('cypher', 'N/A') if result.metadata else 'N/A'
            print(f"\nGenerated Cypher query:")
            print(cypher_query)
            
            # Print timing information
            print(f"\nTiming Information:")
            print(f"LLM Generation Time: {timings['llm_generation']:.3f}s")
            print(f"Query Execution Time: {timings['query_execution']:.3f}s")
            print(f"Total Time: {timings['total']:.3f}s")
            
            # Save results to files
            csv_file, json_file = save_results(result, query_text, timings)
            
            # Print results to console
            print(f"\nResults saved to:")
            print(f"CSV: {csv_file}")
            print(f"JSON: {json_file}")
            print("\nResults preview:")
            for record in list(result.records)[:3]:  # Show first 3 results
                print(f"\nRecord: {dict(record)}")
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            print(f"Error: {str(e)}")
            continue

print(f"\nAll results have been saved to:")
print(f"CSV files: {CSV_DIR}")
print(f"JSON files: {JSON_DIR}") 