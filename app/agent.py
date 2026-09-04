from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools import create_tools


def create_research_agent(retriever):

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0
    )

    tools = create_tools(retriever)

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt="""
        You are an AI research assistant.

        You help users understand information
        from their documents.

        When the user asks about the documents,
        use the search_documents tool.

        Give clear and accurate answers.

        If the information is not available
        in the documents, say so clearly.
        """
    )

    return agent