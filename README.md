# Text Splitter Pipeline Configurations

This directory contains scripts for processing text using different splitter configurations in Neo4j Graph Database.

## Directory Structure

```
config_pipelines/
├── logs/              # Log files directory
├── README.md          # This file
└── process_all_splitters.py  # Main processing script
```

## Prerequisites

- Python 3.8+
- Neo4j Database
- OpenAI API key
- Required Python packages (install via pip):
  - neo4j
  - neo4j-graphrag
  - pyyaml
  - openai

## Configuration

### 1. Environment Variables

Set the following environment variables before running:

```powershell
# PowerShell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:NEO4J_URI = "bolt+ssc://075db98b.databases.neo4j.io"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM"
```

```bash
# Bash
export OPENAI_API_KEY="your-openai-api-key"
export NEO4J_URI="bolt+ssc://075db98b.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="avo66SsqJi-njCsaJFgHS24iRYaRqW9olR1aQUKsACM"
```

### 2. Splitter Configurations

The script processes five different text splitter configurations:

1. **Fixed Size Splitter** (`config_fixed.yaml`):
   - Splits text into fixed-size chunks (500 chars)
   - 50 character overlap between chunks

2. **Character Splitter** (`config_character.yaml`):
   - Splits on character boundaries
   - Respects newline separators

3. **Sentence Splitter** (`config_sentence.yaml`):
   - Splits on sentence boundaries
   - Maintains sentence integrity

4. **Token Splitter** (`config_token.yaml`):
   - Splits based on token count
   - Useful for LLM context windows

5. **Markdown Splitter** (`config_markdown.yaml`):
   - Splits on markdown headers
   - Preserves document structure

## Running the Pipeline

1. Navigate to the config_pipelines directory:
   ```bash
   cd config_pipelines
   ```

2. Run the processing script:
   ```bash
   python process_all_splitters.py
   ```

## Expected Output

### 1. Neo4j Graph Structure

The script creates the following in Neo4j:

- **Nodes**:
  - `TextChunk` nodes with properties:
    - `text`: Chunk content
    - `index`: Position in sequence
    - `embedding`: Vector embedding
  - `Document` nodes with properties:
    - `name`: Document identifier
    - `text`: Full document text

- **Relationships**:
  - `FROM_DOCUMENT`: Chunks → Document
  - `NEXT_CHUNK`: Sequential chunk links

### 2. Logging

- Log files are created in `logs/` directory
- Format: `splitter_processing_YYYYMMDD_HHMMSS.log`
- Contains:
  - Processing progress
  - Chunk creation stats
  - Embedding generation info
  - Neo4j operations

### 3. Processing Time

- Expect several minutes for complete processing
- Main time factors:
  - OpenAI API calls
  - Neo4j write operations
  - Number and size of chunks

## Verification Queries

Run these Cypher queries in Neo4j to verify results:

```cypher
// Count chunks by splitter type
MATCH (c:TextChunk)
RETURN c.splitter_type, count(c);

// View chunk sequences
MATCH (d:Document)-[:FROM_DOCUMENT]->(c:TextChunk)-[:NEXT_CHUNK*]->(next:TextChunk)
RETURN d.name, c.text, collect(next.text);

// Check embeddings
MATCH (c:TextChunk)
WHERE c.embedding IS NOT NULL
RETURN count(c) as chunks_with_embeddings;
```

## Troubleshooting

1. **OpenAI API Issues**:
   - Verify API key is set correctly
   - Check OpenAI API status
   - Monitor rate limits

2. **Neo4j Connection**:
   - Verify connection credentials
   - Check database accessibility
   - Ensure sufficient permissions

3. **Memory Issues**:
   - Reduce batch size in config
   - Monitor system resources
   - Check available disk space

## Support

For issues or questions:
- Check the logs in `logs/` directory
- Review Neo4j browser logs
- Verify configuration files in `examples/build_graph/from_config_files/build_configs/`