"""Script to delete all data and schema elements from Neo4j."""

from neo4j import GraphDatabase

# Neo4j connection details
uri = "bolt+ssc://075db98b.databases.neo4j.io"
auth = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")

def clear_schema_metadata(tx):
    """Clear schema metadata and caches."""
    print("Clearing schema metadata...")
    # Clear query caches
    tx.run("CALL db.clearQueryCaches()")
    
    # Force schema refresh by creating and immediately dropping a temporary index
    try:
        tx.run("CREATE INDEX temp_cleanup_index IF NOT EXISTS FOR (n:__TEMP_CLEANUP__) ON (n.__temp)")
        tx.run("DROP INDEX temp_cleanup_index IF EXISTS")
    except:
        pass  # Ignore any errors from the temporary operations

def delete_all_constraints(tx):
    """Delete all constraints in the database."""
    # First, get all constraints
    constraints = tx.run("SHOW CONSTRAINTS").data()
    
    # Then drop each constraint
    for constraint in constraints:
        constraint_name = constraint.get('name')
        if constraint_name:
            print(f"Dropping constraint: {constraint_name}")
            tx.run(f"DROP CONSTRAINT {constraint_name}")

def delete_all_indexes(tx):
    """Delete all indexes in the database."""
    # First, get all indexes
    indexes = tx.run("SHOW INDEXES").data()
    
    # Then drop each index
    for index in indexes:
        index_name = index.get('name')
        if index_name:
            print(f"Dropping index: {index_name}")
            tx.run(f"DROP INDEX {index_name}")

def delete_all_nodes_and_relationships(tx):
    """Delete all nodes and relationships in the database."""
    # First delete all relationships and nodes
    query = "MATCH (n) DETACH DELETE n"
    result = tx.run(query)
    counters = result.consume().counters
    
    # Then clean up any remaining data
    cleanup_queries = [
        "MATCH ()-[r]-() DELETE r",  # Delete any remaining relationships
        "MATCH (n) DELETE n",        # Delete any remaining nodes
    ]
    for query in cleanup_queries:
        tx.run(query)
    
    return counters

def get_property_keys(tx):
    """Get all property keys in use."""
    return tx.run("CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey").data()

def main():
    try:
        print("Connecting to Neo4j...")
        driver = GraphDatabase.driver(uri, auth=auth)
        driver.verify_connectivity()
        print("✅ Successfully connected to Neo4j")

        with driver.session(database="neo4j") as session:
            # First delete all constraints
            print("\nDeleting all constraints...")
            session.execute_write(delete_all_constraints)
            print("✅ All constraints deleted")
            
            # Then delete all indexes
            print("\nDeleting all indexes...")
            session.execute_write(delete_all_indexes)
            print("✅ All indexes deleted")
            
            # Delete all nodes and relationships
            print("\nDeleting all nodes and relationships...")
            counters = session.execute_write(delete_all_nodes_and_relationships)
            print(f"Deletion complete. Statistics:")
            print(f"Nodes deleted: {counters.nodes_deleted}")
            print(f"Relationships deleted: {counters.relationships_deleted}")
            
            # Verify the cleanup
            print("\nVerifying cleanup...")
            result = session.run("MATCH (n) RETURN count(n) as nodes").single()
            if result and result["nodes"] == 0:
                print("✅ Database is empty")
            else:
                print("⚠️ Some nodes may remain")
            
            # Check remaining property keys
            print("\nProperty Keys in Schema:")
            print("Note: Property keys are part of Neo4j's schema metadata and cannot be deleted directly.")
            print("They will persist but won't affect new data or queries.\n")
            
            keys = session.execute_read(get_property_keys)
            if keys:
                print("Current property keys in schema:")
                for key in keys:
                    print(f"  - {key['propertyKey']}")
            else:
                print("No property keys found in schema metadata.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.close()
            print("\nNeo4j connection closed")

if __name__ == "__main__":
    main() 