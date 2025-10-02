# ---------------------------
# 1. Save text chunks
# ---------------------------
def save_text_to_file(text: str, file_path: str = "captured_texts.txt"):
    """Append a new text chunk (paragraph/multi-line) separated by a delimiter."""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n---END---\n")
    return file_path
