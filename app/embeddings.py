from langchain_huggingface import HuggingFaceEmbeddings


_embeddings = None


def create_embeddings():

    global _embeddings

    if _embeddings is None:

        print(
            "[EMBEDDINGS] Loading embedding model..."
        )

        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        print(
            "[EMBEDDINGS] Model loaded."
        )

    return _embeddings