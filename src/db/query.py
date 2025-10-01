import requests

def query_vector_db(query_text: str, top_k: int = 3):
    """Send a query to the Pathway HTTP endpoint."""
    url = "http://localhost:8080/query"
    params = {"text": query_text, "k": top_k}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
