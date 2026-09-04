def create_retriever(vectorstore):

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 6,
            "fetch_k": 12,
            "lambda_mult": 0.7
        }
    )

    return retriever