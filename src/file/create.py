import os
import uuid
from datetime import datetime

# ---------------------------
# Save text chunks in unique files
# ---------------------------
def save_text_to_file(text: str, live_directory: str):
    """Save each new text chunk in a separate uniquely named file."""
    # Ensure the directory exists
    os.makedirs(live_directory, exist_ok=True)
    
    # Create a unique filename (timestamp + uuid)
    filename = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.txt"
    file_path = os.path.join(live_directory, filename)
    
    # Write the text to the new file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text.strip())
    
    return file_path
