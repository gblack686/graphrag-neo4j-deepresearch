"""This script processes text through different text splitting strategies."""

import os
import yaml
import time
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from neo4j_graphrag.experimental.pipeline.config.runner import PipelineRunner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify environment variables are loaded
required_env_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

async def process_config(config_path: str, input_text: str) -> None:
    """Process a single configuration file."""
    config_name = Path(config_path).stem
    logger.info(f"\nProcessing configuration: {config_name}")
    logger.info(f"Using config file: {config_path}")
    
    try:
        # Create pipeline from config
        pipeline = PipelineRunner.from_config_file(config_path)
        
        # Record start time
        start_time = time.time()
        
        # Process the text
        logger.info("Starting pipeline processing...")
        result = await pipeline.run({"text": input_text})
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(f"Successfully processed {config_name}")
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error processing {config_name}: {str(e)}", exc_info=True)

async def main():
    # Directory containing the configurations
    config_dir = Path("examples/build_graph/from_config_files/build_configs")
    
    if not config_dir.exists():
        raise ValueError(f"Config directory not found: {config_dir}")
    
    # Example text to process
    input_text = """
    The planet Arrakis, also known as Dune, is a harsh desert world and the only source of the spice melange.
    House Atreides, led by Duke Leto, accepts the stewardship of Arrakis at the Emperor's command.
    Paul Atreides, son of Duke Leto and Lady Jessica, is heir to House Atreides and trained in both Mentat abilities and Bene Gesserit ways.
    The Fremen are the native inhabitants of Arrakis, skilled in desert survival and riding the giant sandworms.
    """
    
    logger.info(f"Found config directory: {config_dir}")
    logger.info("Starting to process all configurations")
    logger.info(f"Text to process:\n{input_text}\n")
    
    start_time = time.time()
    
    # Create tasks for all configurations
    tasks = []
    config_files = list(config_dir.glob("*.yaml"))
    logger.info(f"Found {len(config_files)} config files")
    
    for config_file in config_files:
        tasks.append(process_config(str(config_file), input_text))
    
    # Run all configurations concurrently
    await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    logger.info(f"\nCompleted processing all configurations")
    logger.info(f"Total time: {total_time:.2f} seconds")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main process error: {str(e)}", exc_info=True) 