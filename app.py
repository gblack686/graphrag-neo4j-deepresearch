from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import VectorRetriever

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Neo4j connection details
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
INDEX_NAME = os.getenv('INDEX_NAME', 'vector-index-name')

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Initialize embeddings and retriever
embedder = OpenAIEmbeddings(model="text-embedding-3-large")
retriever = VectorRetriever(driver, INDEX_NAME, embedder)

# Initialize LLM
llm = OpenAILLM(model_name="gpt-4", model_params={"temperature": 0})

# Initialize RAG pipeline
rag = GraphRAG(retriever=retriever, llm=llm)

@app.route('/')
def home():
    return jsonify({
        "status": "healthy",
        "message": "GraphRAG API is running",
        "endpoints": {
            "health": "GET /",
            "query": "POST /query",
            "webhook": "POST /webhook"
        }
    })

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        if 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
            
        query_text = data['query']
        top_k = data.get('top_k', 5)  # Optional parameter with default value
        
        response = rag.search(
            query_text=query_text,
            retriever_config={"top_k": top_k}
        )
        
        return jsonify({
            "answer": response.answer,
            "query": query_text,
            "top_k": top_k,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        if 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
            
        query_text = data['query']
        response = rag.search(query_text=query_text, retriever_config={"top_k": 5})
        
        return jsonify({
            "answer": response.answer,
            "query": query_text,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)