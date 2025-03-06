"""This script lists all indexes in the Neo4j database,
including fulltext, vector, and regular indexes.
"""

import neo4j
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection settings
URI = "bolt+ssc://075db98b.databases.neo4j.io"
AUTH = ("neo4j", "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM")
DATABASE = "neo4j"

# Cypher query to list all indexes
LIST_INDEXES_QUERY = """
SHOW INDEXES
YIELD name, type, labelsOrTypes, properties, options
RETURN name, type, labelsOrTypes, properties, options
ORDER BY type, name
"""

def format_index_info(record):
    """Format index information for display"""
    labels = record['labelsOrTypes']
    if not isinstance(labels, (list, tuple)):
        labels = [str(labels)]
    
    properties = record['properties']
    if not isinstance(properties, (list, tuple)):
        properties = [str(properties)]
    
    return f"""
Name: {record['name']}
Type: {record['type']}
Labels/Types: {', '.join(labels)}
Properties: {', '.join(properties)}
Options: {record['options'] if record['options'] else 'None'}
{'=' * 50}"""

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session(database=DATABASE) as session:
        print("\nListing all indexes in the database:")
        print("=" * 50)
        
        result = session.run(LIST_INDEXES_QUERY)
        records = list(result)
        
        if not records:
            print("No indexes found in the database.")
        else:
            # Group indexes by type
            indexes_by_type = {}
            for record in records:
                index_type = record['type']
                if index_type not in indexes_by_type:
                    indexes_by_type[index_type] = []
                indexes_by_type[index_type].append(record)
            
            # Print indexes grouped by type
            for index_type, indexes in indexes_by_type.items():
                print(f"\n{index_type} Indexes:")
                print("-" * 50)
                for index in indexes:
                    print(format_index_info(index))
                    
        print("\nTotal number of indexes:", len(records)) 