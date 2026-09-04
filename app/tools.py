from langchain_core.tools import tool


def create_tools(retriever):

    @tool
    def search_documents(
        query: str
    ) -> str:

        """
        Search the uploaded PDF documents
        for relevant information.

        Use this tool when answering questions
        about the documents.
        """

        documents = retriever.invoke(
            query
        )

        if not documents:

            return (
                "No relevant information was found "
                "in the uploaded documents."
            )

        results = []

        for document in documents:

            page = document.metadata.get(
                "page",
                "unknown"
            )

            source = document.metadata.get(
                "source",
                "unknown"
            )

            if isinstance(page, int):

                page_number = page + 1

            else:

                page_number = page

            results.append(
                f"Source: {source}\n"
                f"Page: {page_number}\n"
                f"Content:\n"
                f"{document.page_content}"
            )

        return "\n\n---\n\n".join(
            results
        )

    return [
        search_documents
    ]