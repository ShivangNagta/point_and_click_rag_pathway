from src.file.create import save_text_to_file
from src.agent.agent_utils import screenshot_to_text, get_user_response
from src.client_functions.endpoints import answer, summarize, retrieve, list_documents, statistics, health_check, search_documents, ask_with_context
from src.chat.manage import format_history, add_to_chat_history, chat_history
import os
from dotenv import load_dotenv

CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_FILE_DIR, ".."))
LIVE_DIR = os.path.join(ROOT_DIR, "pathway", "data")
IMG = f"{ROOT_DIR}/before.png"

load_dotenv()

API = os.getenv("GEMINI_KEY")

if __name__ == "__main__":

    while(True):
        print(chat_history)
        user_text = input()
        formatted_history = format_history(chat_history)
        res = get_user_response(user_text, formatted_history, IMG, [], API)
        print(res)
        add_to_chat_history(user_text, res)


    # # App loop for Kanwar paaji
    # while (True):
    #     # App Logic
    #     #
    #     #
    #     # Kanwar paaji will generate image1 and image2 and screenshot
    #     #
    #     #
    #     # Meow Meow

    #     USER_CLICK = True
    #     if (USER_CLICK):
    #         user_click_information = screenshot_to_text(["image1", "image2"], "API_KEY")
    #         save_text_to_file(user_click_information)

    #     USER_CHAT_QUERY = False
    #     if (USER_CHAT_QUERY):
    #         # retrieve_chunks
    #         # build reponse
    #         user_query = "something_from_user"
    #         screenshot_information = screenshot_to_text(["screenshot"], "API_KEY")
    #         query_text = f"""User Query: {user_query}
    #                          If user mentions anything about the current state of the game then the textual information of the game's screenshot is here as follows: {screenshot_information}
    #         """
    #         chunks_in_json = query_vector_db(query_text, top_k=10)
    #         user_reponse = get_user_response(user_query, "RELEVANT CHAT", "screenshot", chunks_in_json, "API_KEY")

    #         # Update GUI




