"""Script to process text using different splitter configurations from the config files."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Any
import yaml
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import neo4j
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    LLMEntityRelationExtractor,
    OnError,
)
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
from neo4j_graphrag.experimental.components.resolver import (
    SinglePropertyExactMatchResolver,
)
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    SchemaEntity,
    SchemaProperty,
    SchemaRelation,
)
from neo4j_graphrag.experimental.components.text_splitters import (
    FixedSizeSplitter,
    CharacterTextSplitter,
    SentenceTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
)
from neo4j_graphrag.experimental.pipeline import Pipeline
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings

# Set up logging
log_dir = Path("config_pipelines/logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f'splitter_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Check for required environment variables
required_env_vars = ['OPENAI_API_KEY', 'NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Neo4j connection details from .env
uri = os.getenv('NEO4J_URI')
auth = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))

async def process_all_configs() -> None:
    """Process all configuration files in the build_configs directory."""
    try:
        # Get all config files
        config_dir = Path("../examples/build_graph/from_config_files/build_configs")
        config_files = list(config_dir.glob("config_*.yaml"))
        
        logger.info(f"Found {len(config_files)} configuration files to process")
        
        # Connect to Neo4j
        driver = neo4j.GraphDatabase.driver(uri, auth=auth)
        logger.info("Connected to Neo4j")
        
        try:
            # Process each configuration
            for config_file in config_files:
                await process_config(driver, config_file)
                
        finally:
            driver.close()
            logger.info("Neo4j connection closed")
            
    except Exception as e:
        logger.error(f"Error in process_all_configs: {str(e)}")
        raise 