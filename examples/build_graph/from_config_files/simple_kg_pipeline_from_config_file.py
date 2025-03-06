"""In this example, the pipeline is defined in a JSON ('simple_kg_pipeline_config.json')
or YAML ('simple_kg_pipeline_config.yaml') file.

According to the configuration file, some parameters will be read from the env vars
(Neo4j credentials and the OpenAI API key).
"""

import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from neo4j_graphrag.experimental.pipeline.config.runner import PipelineRunner
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult

# Load environment variables from .env file
load_dotenv()

logging.basicConfig()
logging.getLogger("neo4j_graphrag").setLevel(logging.DEBUG)

# Verify required environment variables are set
required_vars = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD", "OPENAI_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {missing_vars}")

root_dir = Path(__file__).parent
file_path = root_dir / "simple_kg_pipeline_config.yaml"
# file_path = root_dir / "simple_kg_pipeline_config.json"

# Text to process
TEXT = """The son of Duke Leto Atreides and the Lady Jessica, Paul is the heir of House Atreides,
an aristocratic family that rules the planet Caladan, the rainy planet, since 10191."""

async def main() -> PipelineResult:
    pipeline = PipelineRunner.from_config_file(file_path)
    return await pipeline.run({"text": TEXT})

if __name__ == "__main__":
    print(asyncio.run(main()))
