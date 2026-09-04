from app.loaders import load_pdf
from app.text_splitter import split_documents
from app.vectorstore import create_vectorstore
from app.retriever import create_retriever
from app.chains import create_rag_chain
from app.chat_history import ChatHistory


def create_rag_system():

    documents = load_pdf(
        "data/documents/DS.pdf"
    )

    chunks = split_documents(
        documents
    )

    vectorstore = create_vectorstore(
        chunks
    )

    retriever = create_retriever(
        vectorstore
    )

    rag_chain = create_rag_chain()

    chat_history = ChatHistory()

    return (
        retriever,
        rag_chain,
        chat_history
    )


def ask_question(
    retriever,
    rag_chain,
    chat_history,
    question
):

    relevant_chunks = (
        retriever.invoke(question)
    )

    context = "\n\n".join(
        chunk.page_content
        for chunk in relevant_chunks
    )

    history = "\n".join(
        f"{message['role']}: "
        f"{message['content']}"
        for message in
        chat_history.get_history()
    )

    response = rag_chain.invoke({
        "context": context,
        "history": history,
        "question": question
    })

    chat_history.add_user_message(
        question
    )

    chat_history.add_ai_message(
        response
    )

    return response