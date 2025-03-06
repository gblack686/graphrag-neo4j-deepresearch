"""Script to provide a comprehensive summary of the Neo4j instance.
Lists all graphs, indexes, constraints, labels, relationships, and basic statistics.
Also saves all information to CSV files in the graph_stats directory.
"""

import os
import csv
import logging
from typing import Dict, List
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tabulate import tabulate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format for cleaner output
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = Path("graph_stats")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def save_to_csv(data: List[Dict], filename: str, output_dir: Path):
    """Save data to a CSV file."""
    if not data:
        return
    
    filepath = output_dir / filename
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Saved data to {filepath}")

def get_database_info(tx) -> Dict:
    """Get basic information about the database size."""
    query = """
    MATCH (n)
    RETURN 
        count(n) as node_count,
        size([()-[r]->() | r]) as relationship_count
    """
    result = tx.run(query).single()
    return {
        "nodes": result["node_count"],
        "relationships": result["relationship_count"]
    }

def get_label_counts(tx) -> List[Dict]:
    """Get counts for each node label."""
    query = """
    CALL db.labels() YIELD label
    CALL {
        WITH label
        MATCH (n:`${label}`)
        RETURN count(n) as count
    }
    RETURN label, count
    ORDER BY count DESC
    """
    return [{"label": record["label"], "count": record["count"]}
            for record in tx.run(query)]

def get_relationship_counts(tx) -> List[Dict]:
    """Get counts for each relationship type."""
    query = """
    CALL db.relationshipTypes() YIELD relationshipType
    CALL {
        WITH relationshipType
        MATCH ()-[r:`${relationshipType}`]->()
        RETURN count(r) as count
    }
    RETURN relationshipType, count
    ORDER BY count DESC
    """
    return [{"type": record["relationshipType"], "count": record["count"]}
            for record in tx.run(query)]

def get_indexes(tx) -> List[Dict]:
    """Get all indexes in the database."""
    return tx.run("SHOW INDEXES").data()

def get_constraints(tx) -> List[Dict]:
    """Get all constraints in the database."""
    return tx.run("SHOW CONSTRAINTS").data()

def get_property_key_counts(tx) -> List[Dict]:
    """Get counts of property keys used in the database."""
    query = """
    CALL db.propertyKeys() YIELD propertyKey
    MATCH (n)
    WHERE n[propertyKey] IS NOT NULL
    RETURN propertyKey, count(n) as usage_count
    ORDER BY usage_count DESC
    """
    return tx.run(query).data()

def get_databases(tx) -> List[Dict]:
    """Get list of all databases in the instance."""
    return tx.run("SHOW DATABASES").data()

def get_graph_structure(tx) -> Dict:
    """Get detailed information about the graph structure."""
    # Get node patterns
    node_query = """
    MATCH (n)
    WITH labels(n) as labels
    RETURN labels, count(*) as count
    ORDER BY count DESC
    """
    
    # Get relationship patterns
    rel_query = """
    MATCH (n)-[r]->(m)
    WITH type(r) as type, labels(n) as sourceLabels, labels(m) as targetLabels
    RETURN type, sourceLabels, targetLabels, count(*) as count
    ORDER BY count DESC
    """
    
    return {
        "nodes": tx.run(node_query).data(),
        "relationships": tx.run(rel_query).data()
    }

def print_section(title: str):
    """Print a section title in a formatted way."""
    logger.info("\n" + "=" * 80)
    logger.info(f" {title} ")
    logger.info("=" * 80)

def main():
    # Use the connection that worked in test_neo4j_connection.py
    uri = "bolt+ssc://075db98b.databases.neo4j.io"
    auth = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
    
    # Create output directory for CSV files
    output_dir = ensure_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        logger.info(f"Connecting to Neo4j at {uri}")
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        logger.info("✅ Successfully connected to Neo4j")

        # First, get list of all databases (each database contains a graph)
        with driver.session(database="system") as system_session:
            print_section("Available Graph Databases")
            databases = system_session.execute_read(get_databases)
            if databases:
                db_info = [{
                    "name": db.get("name"),
                    "status": db.get("currentStatus"),
                    "default": db.get("default", False),
                    "address": db.get("address", "N/A"),
                    "role": db.get("role", "N/A"),
                    "requestedStatus": db.get("requestedStatus", "N/A")
                } for db in databases]
                logger.info(tabulate(db_info, headers="keys", tablefmt="grid"))
                save_to_csv(db_info, f"graph_databases.csv", output_dir)
            else:
                logger.info("No graph databases found.")

        # Process each available database/graph
        for db in databases:
            db_name = db.get("name")
            if db_name in ["system", "neo4j"]:  # Process only data databases
                with driver.session(database=db_name) as session:
                    print_section(f"Graph Database: {db_name}")
                    
                    # Graph Structure Overview
                    print_section(f"Graph Structure ({db_name})")
                    try:
                        structure = session.execute_read(get_graph_structure)
                        if structure:
                            # Display node patterns
                            logger.info("\nNode Patterns:")
                            node_patterns = [{
                                "labels": ":".join(item["labels"]) if item.get("labels") else "(no label)",
                                "count": item["count"]
                            } for item in structure["nodes"]]
                            if node_patterns:
                                logger.info(tabulate(node_patterns, headers="keys", tablefmt="grid"))
                            
                            # Display relationship patterns
                            logger.info("\nRelationship Patterns:")
                            rel_patterns = [{
                                "source": ":".join(item["sourceLabels"]) if item.get("sourceLabels") else "(no label)",
                                "relationship": item["type"],
                                "target": ":".join(item["targetLabels"]) if item.get("targetLabels") else "(no label)",
                                "count": item["count"]
                            } for item in structure["relationships"]]
                            if rel_patterns:
                                logger.info(tabulate(rel_patterns, headers="keys", tablefmt="grid"))
                            
                            # Save structure information
                            save_to_csv(node_patterns, f"graph_structure_nodes_{db_name}.csv", output_dir)
                            save_to_csv(rel_patterns, f"graph_structure_relationships_{db_name}.csv", output_dir)
                    except Exception as e:
                        logger.error(f"Error getting graph structure: {str(e)}")

                    # Database Overview
                    print_section("Size Overview")
                    db_info = session.execute_read(get_database_info)
                    logger.info(f"Total Nodes: {db_info['nodes']:,}")
                    logger.info(f"Total Relationships: {db_info['relationships']:,}")
                    
                    # Save overview with database name
                    save_to_csv([{
                        "database": db_name,
                        "timestamp": timestamp,
                        "total_nodes": db_info["nodes"],
                        "total_relationships": db_info["relationships"]
                    }], f"graph_size_{db_name}.csv", output_dir)

                    # Node Labels
                    print_section(f"Node Labels ({db_name})")
                    labels = session.execute_read(get_label_counts)
                    if labels:
                        logger.info(tabulate(labels, headers="keys", tablefmt="grid"))
                        # Add database name to each record
                        for label in labels:
                            label["database"] = db_name
                        save_to_csv(labels, f"node_labels_{db_name}.csv", output_dir)
                    else:
                        logger.info("No node labels found.")

                    # Relationship Types
                    print_section(f"Relationship Types ({db_name})")
                    relationships = session.execute_read(get_relationship_counts)
                    if relationships:
                        logger.info(tabulate(relationships, headers={"type": "Type", "count": "Count"}, tablefmt="grid"))
                        # Add database name to each record
                        for rel in relationships:
                            rel["database"] = db_name
                        save_to_csv(relationships, f"relationship_types_{db_name}.csv", output_dir)
                    else:
                        logger.info("No relationships found.")

                    # Indexes
                    print_section(f"Indexes ({db_name})")
                    indexes = session.execute_read(get_indexes)
                    if indexes:
                        index_info = [{
                            "database": db_name,
                            "name": idx.get("name", "N/A"),
                            "type": idx.get("type", "N/A"),
                            "labelsOrTypes": ", ".join(idx.get("labelsOrTypes", []) or []),
                            "properties": ", ".join(idx.get("properties", []) or [])
                        } for idx in indexes]
                        logger.info(tabulate(index_info, headers="keys", tablefmt="grid"))
                        save_to_csv(index_info, f"indexes_{db_name}.csv", output_dir)
                    else:
                        logger.info("No indexes found.")

                    # Constraints
                    print_section(f"Constraints ({db_name})")
                    constraints = session.execute_read(get_constraints)
                    if constraints:
                        constraint_info = [{
                            "database": db_name,
                            "name": con.get("name", "N/A"),
                            "type": con.get("type", "N/A"),
                            "labelsOrTypes": ", ".join(con.get("labelsOrTypes", []) or []),
                            "properties": ", ".join(con.get("properties", []) or [])
                        } for con in constraints]
                        logger.info(tabulate(constraint_info, headers="keys", tablefmt="grid"))
                        save_to_csv(constraint_info, f"constraints_{db_name}.csv", output_dir)
                    else:
                        logger.info("No constraints found.")

                    # Property Keys
                    print_section(f"Most Used Property Keys ({db_name})")
                    property_keys = session.execute_read(get_property_key_counts)
                    if property_keys:
                        # Add database name to each record
                        for prop in property_keys:
                            prop["database"] = db_name
                        logger.info(tabulate(
                            property_keys[:20],  # Show top 20 most used properties
                            headers={"propertyKey": "Property Key", "usage_count": "Usage Count"},
                            tablefmt="grid"
                        ))
                        if len(property_keys) > 20:
                            logger.info(f"\n... and {len(property_keys) - 20} more property keys")
                        save_to_csv(property_keys, f"property_keys_{db_name}.csv", output_dir)
                    else:
                        logger.info("No property keys found.")

            logger.info(f"\nAll statistics have been saved to CSV files in the '{output_dir}' directory")

    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.close()
            logger.info("\nNeo4j connection closed")

if __name__ == "__main__":
    main() 