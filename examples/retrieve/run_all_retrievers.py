"""This script runs all Dune retrievers sequentially and logs their execution.
It provides a convenient way to test all retrieval methods at once.

Prerequisites:
    - All individual retriever scripts must be present in the same directory
    - All prerequisites for individual retrievers must be met
    - OpenAI API key must be set in environment variables
"""

import os
import sys
import logging
from datetime import datetime
import importlib.util
from typing import List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('examples/retrieve/results', 'retriever_runs.log'))
    ]
)
logger = logging.getLogger(__name__)

def import_script(script_path: str) -> Optional[object]:
    """Dynamically import a Python script."""
    try:
        spec = importlib.util.spec_from_file_location("module", script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {script_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to import {script_path}: {str(e)}")
        return None

def run_retriever(script_name: str) -> bool:
    """Run a single retriever script and return success status."""
    script_path = os.path.join("examples/retrieve", script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running {script_name}...")
    print(f"\n{'='*50}")
    print(f"Running {script_name}")
    print(f"{'='*50}")
    
    try:
        module = import_script(script_path)
        if module is None:
            return False
        return True
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def main():
    """Main function to run all retrievers."""
    # Create results directory if it doesn't exist
    os.makedirs("examples/retrieve/results", exist_ok=True)
    
    # List of retriever scripts to run
    retrievers = [
        "dune_similarity_search.py",
        "dune_vector_cypher_search.py",
        "dune_hybrid_search.py",
        "dune_hybrid_cypher_search.py",
        "dune_similarity_search_for_vector.py",
        "dune_text2cypher_search.py"
    ]
    
    # Track execution results
    results = []
    start_time = datetime.now()
    
    # Run each retriever
    for retriever in retrievers:
        success = run_retriever(retriever)
        results.append((retriever, success))
    
    # Print summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print("Execution Summary")
    print("="*50)
    print(f"Total time: {duration}")
    print("\nResults:")
    
    successful = 0
    for retriever, success in results:
        status = "✓ Success" if success else "✗ Failed"
        print(f"{status}: {retriever}")
        if success:
            successful += 1
    
    print(f"\nSuccessfully ran {successful} out of {len(retrievers)} retrievers")
    
    # Log summary
    logger.info(f"Completed running all retrievers. Success rate: {successful}/{len(retrievers)}")

if __name__ == "__main__":
    main() 