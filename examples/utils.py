"""
Shared utility functions for the example scripts.
"""

def generate_vector_index_name(
    label: str = "Chunk",
    property_name: str = "embedding",
    dimensions: int = 1536,
    similarity: str = "cosine"
) -> str:
    """
    Generates a standardized name for vector indexes.
    For our Dune project, we use 'dune_vector_search' as the index name.
    
    Args:
        label (str): Node label the index is created for (default: "Chunk")
        property_name (str): Name of the property containing the vector (default: "embedding")
        dimensions (int): Number of dimensions in the vector (default: 1536)
        similarity (str): Similarity function used (default: "cosine")
    
    Returns:
        str: Generated index name
    """
    return "dune_vector_search"  # Using the existing index name for consistency 