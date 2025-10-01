import pathway as pw
from pathway.stdlib.indexing import text
from pathway.stdlib.indexing.faiss import FaissIndex
from sentence_transformers import SentenceTransformer
import threading

# ---------------------------
# 2. Pathway pipeline
# ---------------------------
def start_vector_db_pipeline(file_path: str = "captured_texts.txt"):
    # Step 1: Read file in streaming mode (auto-updates when appended)
    table = pw.io.fs.read(
        file_path,
        format="text",
        mode="streaming",
    )

    # Step 2: Split text into chunks (by delimiter)
    docs = text.split_text(table.text, separator="---END---")

    # Step 3: Embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_fn(batch):
        return model.encode(batch, convert_to_numpy=True).tolist()

    embedded = text.embed(docs, embed_fn)

    # Step 4: Build FAISS index
    index = FaissIndex(embedded)

    # Step 5: Expose HTTP query interface
    pw.io.http.serve(index)

    # Start reactive pipeline (runs continuously)
    pw.run()


# ---------------------------
# 3. Start Pathway in background thread
# ---------------------------
def auto_update_vec_db_async(file_path="captured_texts.txt"):
    thread = threading.Thread(target=start_vector_db_pipeline, args=(file_path,), daemon=True)
    thread.start()
    print("[Pathway] Vector DB pipeline started in background.")
