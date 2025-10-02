from src.db.utils import save_text_to_file
from src.db.pathway_pipeline import auto_update_vec_db_async
from src.db.query import query_vector_db
from src.agent.agent_utils import screenshot_to_text, get_user_response
import os
from dotenv import load_dotenv

PATH_TO_TEXTS_ON_CLICK = "captured_texts.txt"

load_dotenv()

API = os.getenv('GEMINI_KEY')

if __name__ == "__main__":
    # Update Vector database in background asynchrounously whenever new information available
    auto_update_vec_db_async(PATH_TO_TEXTS_ON_CLICK)

    # App loop for Kanwar paaji
    while (True):
        # App Logic
        #
        #
        # Kanwar paaji will generate image1 and image2 and screenshot
        #
        #
        # Meow Meow

        USER_CLICK = True
        if (USER_CLICK):
            user_click_information = screenshot_to_text(["image1", "image2"], "API_KEY")
            save_text_to_file(user_click_information)

        USER_CHAT_QUERY = False
        if (USER_CHAT_QUERY):
            # retrieve_chunks
            # build reponse
            user_query = "something_from_user"
            screenshot_information = screenshot_to_text(["screenshot"], "API_KEY")
            query_text = f"""User Query: {user_query}
                             If user mentions anything about the current state of the game then the textual information of the game's screenshot is here as follows: {screenshot_information}
            """
            chunks_in_json = query_vector_db(query_text, top_k=10)
            user_reponse = get_user_response(user_query, "RELEVANT CHAT", "screenshot", chunks_in_json, "API_KEY")

            # Update GUI




