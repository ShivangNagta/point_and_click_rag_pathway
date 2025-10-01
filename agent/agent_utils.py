from google import genai
from google.genai import types

API_KEY = "APNI-KEY-DAALO"

def screenshot_to_text(images_list, api_key=API_KEY):
    """
    input: List of image paths (from local storage)
    Assuming only 2 images in images_list
    output: text: generated text
    """
    system_prompt = f"""

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
            "Compare these two before and after mouse-click game screens and explain the differences, and also extract features in detail that can be used on a clue "
            "especially any change in the top message.",
            "Also keep the items in inventory in mind, the things might be useful for later clues."
        ]
    )
    return response.text

def get_user_response(user_query, relevant_chat, current_screenshot, chunks, api_key=API_KEY):
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
    #system prompt needs changes
    system_prompt = f"""
    You are an AI agent helping the user playing game in solving some puzzle. Help him out.
    \n
    """
    info = ""
    for i, chunk in enumerate(chunks):
        info += f"{i}. {chunk}\n"

    user_prompt = f"""
    User Query: {user_query},\n
    Relevant Chat: {relevant_chat},\n
    Relevant Info: {info},\n
    """

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image1_bytes, mime_type="image/png"),
            f"{system_prompt}\n {user_prompt}",
        ]
    )

    return response.text

