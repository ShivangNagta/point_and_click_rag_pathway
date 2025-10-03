"""
Pathway RAG Server Client
Simple procedural functions for interacting with Pathway AI Pipeline REST API.
"""

import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import os

load_dotenv()

DEFAULT_HOST = os.getenv('PATHWAY_HOST')
DEFAULT_PORT = os.getenv('PATHWAY_PORT')


def _get_base_url(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    """Get the base URL for the Pathway server."""
    return f"http://{host}:{port}"


def _make_request(endpoint: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Make HTTP POST request to Pathway server.
    
    Args:
        endpoint: API endpoint path
        host: Server host (default: localhost)
        port: Server port (default: 8000)
        data: Request payload
        
    Returns:
        Response JSON as dictionary
        
    Raises:
        Exception: If request fails
    """
    url = f"{_get_base_url(host, port)}{endpoint}"
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Request to {endpoint} failed: {str(e)}")


# LLM and RAG Functions

def answer(prompt: str, filters: Optional[str] = None, 
          host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> Dict[str, Any]:
    """
    Ask questions about your documents or talk with the LLM.
    
    Args:
        prompt: The question or prompt to send to the RAG system
        filters: Optional metadata filters (e.g., specific files/folders)
        host: Server host
        port: Server port
        
    Returns:
        Dictionary containing 'response' key with the answer
        
    Example:
        >>> result = answer("What are the terms and conditions?")
        >>> print(result['response'])
    """
    payload = {"prompt": prompt}
    if filters:
        payload["filters"] = filters
    
    return _make_request("/v2/answer", host, port, data=payload)


def summarize(texts: List[str], host: str = DEFAULT_HOST, 
             port: int = DEFAULT_PORT) -> Dict[str, Any]:
    """
    Summarize a list of texts.
    
    Args:
        texts: List of text strings to summarize
        host: Server host
        port: Server port
        
    Returns:
        Dictionary containing the summary
        
    Example:
        >>> summarize(["Long text 1...", "Long text 2..."])
    """
    payload = {"texts": texts}
    return _make_request("/v2/summarize", host, port, data=payload)


# Document Indexing Functions

def retrieve(query: str, k: int = 3, metadata_filter: Optional[str] = None,
            host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> List[Dict[str, Any]]:
    """
    Perform similarity search to retrieve relevant documents.
    
    Args:
        query: Search query text
        k: Number of results to return (default: 3)
        metadata_filter: Optional filter on document metadata
        host: Server host
        port: Server port
        
    Returns:
        List of dictionaries containing retrieved documents and scores
        
    Example:
        >>> retrieve("contract terms", k=5)
        >>> retrieve("earnings", metadata_filter="path:2023")
    """
    payload = {
        "query": query,
        "k": k
    }
    if metadata_filter:
        payload["metadata_filter"] = metadata_filter
    
    return _make_request("/v1/retrieve", host, port, data=payload)


def list_documents(host: str = DEFAULT_HOST, 
                  port: int = DEFAULT_PORT) -> List[Dict[str, Any]]:
    """
    Retrieve metadata of all files currently processed by the indexer.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        List of dictionaries containing document metadata
        (path, created_at, modified_at, owner, seen_at)
        
    Example:
        >>> docs = list_documents()
        >>> for doc in docs:
        ...     print(doc['path'])
    """
    return _make_request("/v2/list_documents", host, port)


def statistics(host: str = DEFAULT_HOST, 
              port: int = DEFAULT_PORT) -> Dict[str, Any]:
    """
    Get basic statistics about the indexer's health and status.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        Dictionary containing indexer statistics
        
    Example:
        >>> stats = statistics()
        >>> print(f"Total documents: {stats['total_documents']}")
    """
    return _make_request("/v1/statistics", host, port)


# Convenience Functions

def health_check(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """
    Check if the Pathway server is healthy and responding.
    
    Args:
        host: Server host
        port: Server port
        
    Returns:
        True if server is healthy, False otherwise
    """
    try:
        statistics(host, port)
        return True
    except Exception:
        return False


def search_documents(query: str, k: int = 5, 
                    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> List[str]:
    """
    Search documents and return just the text content.
    
    Args:
        query: Search query
        k: Number of results
        host: Server host
        port: Server port
        
    Returns:
        List of document text snippets
    """
    results = retrieve(query, k=k, host=host, port=port)
    return [doc.get("text", "") for doc in results]


def ask_with_context(question: str, k: int = 3,
                    host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    """
    Ask a question and get just the answer text.
    
    Args:
        question: Question to ask
        k: Number of context documents to retrieve
        host: Server host
        port: Server port
        
    Returns:
        Answer text string
    """
    result = answer(question, host=host, port=port)
    return result.get("response", "")


# Example usage
# if __name__ == "__main__":
#     # Check if server is running
#     if health_check():
#         print("✓ Server is running")
#     else:
#         print("✗ Server is not responding")
#         exit(1)
    
#     # List all documents
#     print("\n--- Documents in Index ---")
#     docs = list_documents()
#     for doc in docs:
#         print(f"- {doc.get('path')}")
    
#     # Get statistics
#     print("\n--- Indexer Statistics ---")
#     stats = statistics()
#     print(stats)
    
#     # Perform similarity search
#     print("\n--- Similarity Search ---")
#     search_results = retrieve("20", k=1)
#     print(f"Found {len(search_results)} results")
    
#     # Ask a question
#     print("\n--- Ask Question ---")
#     ans = ask_with_context("What are the terms and conditions?")
#     print(f"Answer: {ans}")
    
#     # Full answer with metadata
#     print("\n--- Full Answer with Metadata ---")
#     full_answer = answer("What did Maria found")
#     print(full_answer)
