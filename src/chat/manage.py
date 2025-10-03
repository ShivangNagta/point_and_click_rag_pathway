# ---------------------------
# Chat history management
# ---------------------------
chat_history = []

def add_to_chat_history(user_query: str, ai_response: str):
    """Store user query and AI response in history."""
    chat_history.append({
        "user": user_query,
        "ai": ai_response
    })
    return chat_history

def format_history(chat_history):
    if not chat_history:
        return "No previous chat"
    return "\n".join(
        [f"User: {h['user']}\nAI: {h['ai']}" for h in chat_history]
    )
