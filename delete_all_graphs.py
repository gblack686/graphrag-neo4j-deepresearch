"""Script to delete all graphs and indexes from Neo4j.
This is useful for cleaning up the database between different graph building experiments.
"""

import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def delete_all_nodes_and_relationships(tx):
    """Delete all nodes and relationships in the database."""
    query = "MATCH (n) DETACH DELETE n"
    result = tx.run(query)
    return result.consume().counters

def delete_all_indexes(tx):
    """Delete all indexes in the database."""
    # First, get all indexes
    indexes = tx.run("SHOW INDEXES").data()
    
    # Then drop each index
    for index in indexes:
        index_name = index.get('name')
        if index_name:
            logger.info(f"Dropping index: {index_name}")
            tx.run(f"DROP INDEX {index_name}")

def delete_all_constraints(tx):
    """Delete all constraints in the database."""
    # First, get all constraints
    constraints = tx.run("SHOW CONSTRAINTS").data()
    
    # Then drop each constraint
    for constraint in constraints:
        constraint_name = constraint.get('name')
        if constraint_name:
            logger.info(f"Dropping constraint: {constraint_name}")
            tx.run(f"DROP CONSTRAINT {constraint_name}")

def main():
    # Get Neo4j connection details from environment variables
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")  # Default to 'neo4j' if not specified

    if not all([uri, user, password]):
        logger.error("Missing required environment variables. Please ensure NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are set.")
        return

    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

        with driver.session(database=database) as session:
            # Delete constraints first (as they might prevent deletion of nodes)
            logger.info("Deleting all constraints...")
            session.execute_write(delete_all_constraints)
            
            # Delete indexes
            logger.info("Deleting all indexes...")
            session.execute_write(delete_all_indexes)
            
            # Delete all nodes and relationships
            logger.info("Deleting all nodes and relationships...")
            counters = session.execute_write(delete_all_nodes_and_relationships)
            
            # Log the results
            logger.info(f"Deletion complete. Statistics:")
            logger.info(f"Nodes deleted: {counters.nodes_deleted}")
            logger.info(f"Relationships deleted: {counters.relationships_deleted}")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
    finally:
        if 'driver' in locals():
            driver.close()
            logger.info("Neo4j connection closed")

if __name__ == "__main__":
    main() 