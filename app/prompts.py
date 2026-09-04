from langchain_core.prompts import ChatPromptTemplate


rag_prompt = ChatPromptTemplate.from_messages([

    (
        "system",
        """
You are an AI research assistant.

Answer the user's question using ONLY
the provided context.

Use the conversation history to understand
references such as "it", "its", "they",
or "this".

If the answer cannot be found in the context,
say that the information is not available
in the documents.

Context:
{context}

Conversation history:
{history}
"""
    ),

    (
        "human",
        """
Question:
{question}
"""
    )
])