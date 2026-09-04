from langchain_chroma import Chroma

from .embeddings import create_embeddings


def create_vectorstore(
    chunks,
    collection_name="documents"
):

    embeddings = create_embeddings()

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="data/chroma_db"
    )

    return vectorstore