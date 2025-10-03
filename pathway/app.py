import logging
import os
import pathway as pw
from dotenv import load_dotenv
from pathway.udfs import DefaultCache
from pathway.udfs import ExponentialBackoffRetryStrategy
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.stdlib.indexing import UsearchKnnFactory, USearchMetricKind
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.xpacks.llm.document_store import DocumentStore

pw.set_license_key("demo-license-key-with-telemetry")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

load_dotenv()

def run():
    folder = pw.io.fs.read(
        path="./data",
        format="binary",
        with_metadata=True,
    )

    sources = [folder]

    # Use ParseUnstructured for text files
    parser = parsers.ParseUnstructured()

    text_splitter = splitters.TokenCountSplitter(max_tokens=800)

    embedder = embedders.GeminiEmbedder(model="models/text-embedding-004")

    index = UsearchKnnFactory(
        reserved_space=1000,
        embedder=embedder,
        metric=USearchMetricKind.COS
    )

    llm = llms.LiteLLMChat(
        model="gemini/gemini-2.0-flash",
        cache_strategy=DefaultCache(),
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=2),
        temperature=0,
        capacity=8
    )

    pathway_host: str = "0.0.0.0"
    pathway_port = int(os.environ.get("PATHWAY_PORT", 8000))

    doc_store = DocumentStore(
        docs=sources,
        splitter=text_splitter,
        parser=parser,
        retriever_factory=index
    )

    rag_app = BaseRAGQuestionAnswerer(llm=llm, indexer=doc_store)

    rag_app.build_server(host=pathway_host, port=pathway_port)

    rag_app.run_server(with_cache=True, terminate_on_error=True)

if __name__ == "__main__":
    run()
