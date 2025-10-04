# Reinforced Game RAG

[](https://www.python.org/downloads/)
[](https://opensource.org/licenses/MIT)

**A Real-time, Reinforcement Learning-inspired RAG Assistant for solving Point-and-Click Web Games.**

This project was developed for the **Pathway and IOTA Cluster competition at IIT Ropar**. It leverages a dynamic and real-time Retrieval-Augmented Generation (RAG) pipeline to create an AI assistant that learns from a user's gameplay and provides contextual guidance to solve complex puzzles in any web-based point-and-click game.

## Core Idea

The traditional approach to game guides is static. This project introduces a dynamic, learning assistant. As you play a game, the system observes your actions by comparing screenshots before and after each click. It uses a multimodal LLM to describe the changes that occurred, effectively creating a "memory" of game state transitions. These memories are stored and indexed in real-time by a **Pathway RAG pipeline**.

When you're stuck, you can ask the AI for help. The assistant retrieves the most relevant past actions (memories) from the RAG pipeline, analyzes the current screen, and uses this combined context to provide intelligent, step-by-step hints to guide you forward.

## How It Works

The system operates in two main loops: a continuous **Data Collection Loop** that builds the knowledge base, and an on-demand **User Interaction Loop** that provides assistance.

### 1\. Data Collection Loop (Autonomous)

This loop runs in the background as you play, constantly learning from your actions.

1.  **Load Game**: The user provides a URL to a web-based game, which is loaded into the PyQt5 application's web view.
2.  **Capture Click**: A JavaScript bridge injected into the web page detects every mouse click and notifies the Python backend.
3.  **Screenshot State**: The application takes a screenshot *before* the click and another one immediately *after* the click has been rendered.
4.  **Analyze Change**: The pair of screenshots is sent to a vision model. The model analyzes the visual difference and generates a detailed text description of the action and its outcome (e.g., "Clicked on the red key, which caused the wooden chest to open.").
5.  **Store Memory**: This generated text is saved as a new `.txt` file in the `pathway/data` directory.
6.  **Live Indexing**: The Pathway RAG service, which is watching the `data` directory, automatically detects the new file, processes it, generates embeddings, and adds it to its vector index without any downtime.

### 2\. User Interaction Loop (On-Demand)

This loop is triggered when you ask for help in the chat interface.

1.  **User Query**: You type a question into the chat, like "How do I open this door?".
2.  **Context Capture**: The application immediately takes a screenshot of the current game screen.
3.  **Retrieve Knowledge**: The user's query is sent to the Pathway RAG pipeline, which performs a similarity search and retrieves the most relevant text files (i.e., the most relevant past actions and outcomes).
4.  **Generate Response**: The user's query, the current screenshot, the retrieved text chunks, and the recent chat history are all sent to the Gemini model.
5.  **Provide Guidance**: The LLM synthesizes all this information to provide a helpful, context-aware response, which is then displayed in the chat window.

## Features

  * **Universal Game Support**: Works with any web-based (WebGL, HTML5) point-and-click game that can be loaded via URL.
  * **Real-time Learning**: Automatically builds a knowledge base of game mechanics and puzzle solutions as you play.
  * **Multimodal Context**: Uses both visual (screenshots) and textual (game state descriptions, user queries) information for rich, contextual understanding.
  * **Intelligent Assistance**: Provides hints and guidance based on your actual gameplay history, not a generic walkthrough.
  * **Interactive UI**: A clean, split-screen interface with the game on one side and logging/chat panels on the other.
  * **Asynchronous Processing**: Heavy tasks like LLM calls and file processing are offloaded to a thread pool to keep the UI responsive.
  * **Dockerized Backend**: The Pathway RAG pipeline is containerized with Docker for easy setup and deployment.

## Tech Stack

  * **Frontend & GUI**: PyQt5, QWebEngineView
  * **Backend RAG Pipeline**: [Pathway](https://pathway.com/)
  * **LLM & Vision Model**: Google Gemini 1.5 Flash
  * **Vector Search**: Usearch
  * **Containerization**: Docker, Docker Compose
  * **Core Language**: Python 3.11

## 📂 Project Structure

```
reinforced_game_rag/
├── .env.example
├── docker-compose.yml
├── LICENSE
├── README.md
├── requirements.txt
├── pathway/
│   ├── .env.example
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── data/             # Live data is stored here
└── src/
    ├── __init__.py
    ├── main.py           # Main PyQt application entry point
    ├── agent/
    │   └── agent_utils.py # Functions for interacting with Gemini
    ├── chat/
    │   └── manage.py      # Chat history management
    ├── client_functions/
    │   └── endpoints.py   # Client for Pathway RAG API
    └── file/
        └── create.py      # Saves text descriptions to files
```

## Setup and Installation

### Prerequisites

  * Python 3.11
  * Docker and Docker Compose
  * An LLM API Key (using Google Gemini here)

### Installation Steps

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/your-username/reinforced_game_rag.git
    cd reinforced_game_rag
    ```

2.  **Set Up Environment Variables**

    Create a `.env` file in the root directory by copying the example file:

    ```bash
    cp .env.example .env
    ```

    Now, edit the `.env` file and add your Google Gemini API key:

    ```
    GEMINI_API_KEY=your_gemini_api_key_here
    PATHWAY_HOST=localhost
    PATHWAY_PORT=8000
    K=3
    ```

3.  **Run the RAG Backend (Pathway)**

    In your terminal, start the Dockerized Pathway service. This will build the container and start the RAG server, which will monitor the `pathway/data` directory.

    ```bash
    docker-compose up --build
    ```

    Keep this terminal running. The RAG service is now active and ready to index data.

4.  **Install Frontend Dependencies and Run the App**

    Open a **new terminal window**. Navigate to the project's root directory.

    Install the required Python packages for the PyQt application:

    ```bash
    pip install -r requirements.txt
    ```

    Run the main application:

    ```bash
    python src/main.py
    ```

## Usage

1.  Once the application window appears, enter the URL of a web-based point-and-click game into the "Game URL" input field.
2.  Click the **"Load Game"** button.
3.  Play the game as you normally would. Every click you make is being silently processed in the background, building up the AI's knowledge. The "Logging" panel will show real-time status updates.
4.  When you get stuck, type your question into the chat box at the bottom left and click **"Send"**.
5.  The AI will analyze your situation and provide a hint in the chat window.

## 📄 License

This project is licensed under the MIT License. See the license file for details.