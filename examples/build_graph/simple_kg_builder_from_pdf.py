"""This example illustrates how to get started easily with the SimpleKGPipeline
and ingest PDF into a Neo4j Knowledge Graph.

This example assumes a Neo4j db is up and running. Update the credentials below
if needed.

OPENAI_API_KEY needs to be in the env vars.
"""

import asyncio
import os
from pathlib import Path
import logging

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.llm import LLMInterface
from neo4j_graphrag.llm import OpenAILLM

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neo4j db infos from environment variables - using the working protocol
URI = "bolt+ssc://075db98b.databases.neo4j.io"  # Using exact working protocol from test
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")  # Using exact credentials from test
DATABASE = "neo4j"

def test_connection():
    logger.info(f"Testing connection to {URI}")
    logger.info(f"Username: {AUTH[0]}")
    logger.info(f"Password provided: {'Yes' if AUTH[1] != 'password' else 'No'}")
    
    try:
        with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
            # Try a simple query
            logger.info("Attempting to verify connectivity...")
            driver.verify_connectivity()
            logger.info("✅ Connection test successful!")
            
            # Try a simple query
            logger.info("Attempting a simple query...")
            result = driver.execute_query("RETURN 1 as test")
            logger.info(f"✅ Query test successful! Result: {result}")
            return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        logger.error(f"Connection details used: URI={URI}")
        return False

# Debug print to verify env vars (showing only first few chars of password)
print(f"Connecting to: {URI}")
print(f"Username: {AUTH[0]}")
print(f"Password loaded: {'Yes' if AUTH[1] != 'password' else 'No'}")

root_dir = Path(__file__).parents[1]
file_path = root_dir / "data" / "Harry Potter and the Chamber of Secrets Summary.pdf"


# Instantiate Entity and Relation objects. This defines the
# entities and relations the LLM will be looking for in the text.
ENTITIES = ["Person", "Organization", "Location"]
RELATIONS = ["SITUATED_AT", "INTERACTS", "LED_BY"]
POTENTIAL_SCHEMA = [
    ("Person", "SITUATED_AT", "Location"),
    ("Person", "INTERACTS", "Person"),
    ("Organization", "LED_BY", "Person"),
]


async def define_and_run_pipeline(
    neo4j_driver: neo4j.Driver,
    llm: LLMInterface,
) -> PipelineResult:
    # Create an instance of the SimpleKGPipeline
    kg_builder = SimpleKGPipeline(
        llm=llm,
        driver=neo4j_driver,
        embedder=OpenAIEmbeddings(),
        entities=ENTITIES,
        relations=RELATIONS,
        potential_schema=POTENTIAL_SCHEMA,
        neo4j_database=DATABASE,
        close_driver=True,  # Ensure driver is closed after pipeline completes
    )
    return await kg_builder.run_async(file_path=str(file_path))


async def main() -> PipelineResult:
    # Test connection first
    if not test_connection():
        logger.error("Failed to establish connection to Neo4j. Exiting...")
        return None

    logger.info("Initializing OpenAI LLM...")
    llm = OpenAILLM(
        model_name="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY"),
        organization=None,
    )
    
    logger.info("Starting pipeline execution...")
    try:
        with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
            res = await define_and_run_pipeline(driver, llm)
        await llm.async_client.close()
        logger.info("Pipeline execution completed successfully!")
        return res
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return None


if __name__ == "__main__":
    res = asyncio.run(main())
    print(res)
