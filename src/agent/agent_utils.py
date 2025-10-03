from google import genai
from google.genai import types

def screenshot_to_text(images_list, api_key):
    """
    Input: List of image paths (from local storage)
           Assuming only 2 images in images_list [before_click, after_click]
    Output: Detailed textual description of changes and extracted clues
    """
    system_prompt = """
    You are an AI assistant specialized in analyzing game screenshots. 
    The user will provide two images: 
      - Image 1: before a mouse click
      - Image 2: after the mouse click

    Your tasks:
    1. Carefully compare the two images and describe **all meaningful differences** caused by the click. 
       - Focus on top messages, dialog boxes, or notifications that might have changed.
       - Highlight any new objects, icons, or environmental changes.
    2. Provide a **detailed semantic description** of the scene:
       - Characters, items, symbols, numbers, text, or UI changes.
       - Relevant background details or environment features that could be clues.
    3. Track the **inventory**: 
       - Note what is visible in the inventory before and after.
       - Mention if something disappeared, appeared, or changed.
    4. Output should be structured to help solve puzzles, not just describe pixels.

    Format your response in this way:
    - **Observed Changes:** (list differences between before and after)  
    - **Clue Candidates:** (items, text, hints that could be puzzle-relevant)  
    - **Inventory State:** (items before vs after, possible usefulness)  
    - **Possible Next Step:** (brief hint on how this change might help the player progress)
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
    You are an expert AI game assistant helping the user solve puzzles inside a game. 
    Your job:
    - Look carefully at the provided screenshot.
    - Use the retrieved reference text (chunks) as factual game knowledge.
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

    Now: Based on the screenshot, chat history, and retrieved knowledge, 
    provide the most useful guidance for the user to progress in solving the puzzle.
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

