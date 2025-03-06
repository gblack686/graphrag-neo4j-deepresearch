from neo4j import GraphDatabase
import ssl
import time

NEO4J_URI = "neo4j+s://075db98b.databases.neo4j.io"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM"
AURA_INSTANCEID = "075db98b"

possible_uris = [
    "bolt://075db98b.databases.neo4j.io",
    "bolt+ssc://075db98b.databases.neo4j.io",
    "bolt+s://075db98b.databases.neo4j.io",
    "neo4j://075db98b.databases.neo4j.io",
    "neo4j+ssc://075db98b.databases.neo4j.io",
    "neo4j+s://075db98b.databases.neo4j.io"
]

AUTH = ("neo4j", NEO4J_PASSWORD)

print("Testing different URI protocols...")
# Run all possible URIs and print the result
for uri in possible_uris:
    print(f"\nTesting connection to {uri}")
    try:
        driver = GraphDatabase.driver(uri, auth=AUTH)
        driver.verify_connectivity()
        print(f"✅ Connection successful to {uri}")
        driver.close()
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
    # Add a small delay between attempts
    time.sleep(1)
