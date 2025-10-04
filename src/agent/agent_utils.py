from datetime import datetime
from google import genai
from google.genai import types

def screenshot_to_text(images_list, api_key):
    """
    Input: List of image paths (from local storage)
           Assuming only 2 images in images_list [before_click, after_click]
    Output: Detailed textual description of changes and extracted clues
    """
    event_time = datetime.now()
    formatted_time = event_time.strftime('%Y-%m-%d %H:%M:%S')
    system_prompt = f"""
    You are an AI assistant specialized in analyzing pairs of screenshots. 
    The event you are analyzing occurred at exactly: {formatted_time}.
    The user will provide two images: 
    - Image 1: before a mouse click
    - Image 2: after the mouse click

    Your tasks:
    1. **Provide a detailed semantic description of the scene**:  
    - Describe what is visible: objects, symbols, patterns, shapes, text, numbers, icons, or decorative elements.  
    - Note positioning, colors, arrangements, or connections that could be significant.  
    - Treat both large items (panels, windows, dialogs) and small details (wall markings, small icons, tiny objects) as potentially meaningful.

    2. **Compare the two images carefully** and describe all meaningful differences.  
    - Include both major changes (UI panels, inventory, new objects) and subtle changes (small objects, decorations, shapes, icons, symbols, highlights, color shifts, patterns).  
    - Mention even minor variations if no obvious change is seen.


    3. **Clue or relevance analysis**:  
    - For each described element, suggest how or why it might be relevant to the application’s context (e.g., puzzle-solving, navigation, progress tracking).  
    - Do not assume the application type; keep the explanation general.

    Format your response, making sure to include the event time:
    - *Event Time:* {formatted_time}
    - *Observed Change:* (A concise, one-sentence summary of the click's result.)
    - *Detailed Description:* (A thorough list of all visual differences.)
    - *State Elements & Notable Objects:* (Description of important persistent items.)
    - *Inferred Action:* (A brief interpretation of the user's action.)
    """

    image_before_path = images_list[0]
    image_after_path = images_list[1]

    # Read image bytes
    with open(image_before_path, "rb") as f:
        image1_bytes = f.read()
    with open(image_after_path, "rb") as f:
        image2_bytes = f.read()

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image1_bytes, mime_type="image/png"),
            types.Part.from_bytes(data=image2_bytes, mime_type="image/png"),
            system_prompt.strip(),
        ]
    )

    return response.text


def get_user_response(user_query, relevant_chat, current_screenshot, chunks, api_key):
    """
    Inputs: 
    1. user_query: string
    2. relevant_chat: string
    3. current_screenshot: string (image_path from local storage)
    4. chunks: list of relevant texts

    Output: 
    Response: string
    """
    with open(current_screenshot, "rb") as f:
        image1_bytes = f.read()

    # Stronger system prompt
    system_prompt = """
    You are an expert AI assistant. Your goal is to help a user by analyzing the state of their application.
    You will be given the following:
    1.  The user's question.
    2.  A screenshot of the application's current state.
    3.  A chronological history of the user's past actions and the results.

    Your job:
    - Look carefully at the provided screenshot.
    - Use the retrieved reference text (chunks) as factual knowledge.
    - If something has been seen/interacted before which is relevant, do tell what has been seen/interacted before (with reference of small part of chunk).
    - Consider the ongoing conversation history for context.
    - Always give clear, step-by-step reasoning or hints, not just answers.
    - If the answer is uncertain, state assumptions explicitly instead of guessing wildly.
    - Keep your response concise and helpful for in-game decision making.
    """

    # Gather all retrieved info
    info = ""
    for i, chunk_path in enumerate(chunks):
        with open(chunk_path, "r") as f:
            chunk = f.read()
        info += f"[{i}] {chunk}\n"

    # User-specific prompt
    user_prompt = f"""
    The user asked: "{user_query}"

    Conversation so far:
    {relevant_chat}

    Retrieved knowledge:
    {info}

    Now: Based on the screenshot, chat history, and temporal retrieved knowledge, 
    provide the most useful guidance and make the most of use of previous contexts, for the user to progress in solving the puzzle.
    """

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image1_bytes, mime_type="image/png"),
            f"{system_prompt.strip()}\n\n{user_prompt.strip()}",
        ]
    )

    return response.text

