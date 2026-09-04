from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from .prompts import rag_prompt


def create_rag_chain():

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0
    )

    parser = StrOutputParser()

    chain = rag_prompt | llm | parser

    return chain