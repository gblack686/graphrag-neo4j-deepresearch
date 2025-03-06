"""
Functions for knowledge graph operations and building.
"""
from typing import Dict, List, Any, Optional
import asyncio
import logging
from neo4j import GraphDatabase, Driver
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.pipeline.pipeline import PipelineResult
from neo4j_graphrag.llm import OpenAILLM, LLMInterface

def create_kg_pipeline(
    driver: Driver,
    entities: List[Any],
    relations: List[Any],
    potential_schema: List[tuple],
    database: str = "neo4j",
    from_pdf: bool = False,
    model_name: str = "gpt-4",
) -> SimpleKGPipeline:
    """
    Create a knowledge graph pipeline instance.
    
    Args:
        driver (Driver): Neo4j driver instance
        entities (List[Any]): List of entity definitions
        relations (List[Any]): List of relation definitions
        potential_schema (List[tuple]): Schema definition for the knowledge graph
        database (str): Name of the Neo4j database
        from_pdf (bool): Whether the source is a PDF
        model_name (str): Name of the LLM model to use
        
    Returns:
        SimpleKGPipeline: Configured pipeline instance
    """
    llm = OpenAILLM(
        model_name=model_name,
        model_params={
            "max_tokens": 2000,
            "response_format": {"type": "json_object"},
        },
    )
    
    return SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=OpenAIEmbeddings(),
        entities=entities,
        relations=relations,
        potential_schema=potential_schema,
        from_pdf=from_pdf,
        neo4j_database=database,
    )

async def build_kg_from_text(
    pipeline: SimpleKGPipeline,
    text: str,
) -> PipelineResult:
    """
    Build a knowledge graph from input text.
    
    Args:
        pipeline (SimpleKGPipeline): Configured pipeline instance
        text (str): Input text to process
        
    Returns:
        PipelineResult: Result of the pipeline execution
    """
    return await pipeline.run_async(text=text)

def process_text_to_kg(
    uri: str,
    auth: tuple,
    text: str,
    entities: List[Any],
    relations: List[Any],
    potential_schema: List[tuple],
    database: str = "neo4j",
) -> PipelineResult:
    """
    Process text and create a knowledge graph in one function call.
    
    Args:
        uri (str): Neo4j database URI
        auth (tuple): Authentication tuple (username, password)
        text (str): Text to process
        entities (List[Any]): Entity definitions
        relations (List[Any]): Relation definitions
        potential_schema (List[tuple]): Schema definition
        database (str): Database name
        
    Returns:
        PipelineResult: Result of the pipeline execution
    """
    with GraphDatabase.driver(uri, auth=auth) as driver:
        pipeline = create_kg_pipeline(
            driver=driver,
            entities=entities,
            relations=relations,
            potential_schema=potential_schema,
            database=database
        )
        result = asyncio.run(build_kg_from_text(pipeline, text))
    return result 