"""
Functions for graph operations and manipulations.
"""
from typing import Dict, List, Any
from neo4j import GraphDatabase

def create_graph_connection(uri: str, username: str, password: str) -> GraphDatabase.driver:
    """
    Create a connection to the Neo4j database.
    
    Args:
        uri (str): The URI of the Neo4j database
        username (str): Username for authentication
        password (str): Password for authentication
        
    Returns:
        GraphDatabase.driver: A Neo4j driver instance
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        return driver
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Neo4j database: {str(e)}")

def close_graph_connection(driver: GraphDatabase.driver) -> None:
    """
    Safely close the Neo4j database connection.
    
    Args:
        driver (GraphDatabase.driver): The Neo4j driver instance to close
    """
    if driver is not None:
        driver.close()

# Add more graph-related functions here 