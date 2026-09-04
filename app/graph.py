from typing import Annotated, TypedDict

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage
)

from langgraph.graph import (
    StateGraph,
    START,
    END
)

from langgraph.graph.message import add_messages

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)


class AgentState(TypedDict):

    messages: Annotated[
        list[AnyMessage],
        add_messages
    ]

    context: str
    question: str
    answer: str


def create_agent_graph():

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        temperature=0
    )

    def generate_answer(state: AgentState):

        question = state["question"]
        context = state["context"]

        prompt = f"""
You are an AI research assistant.

Answer the user's question using ONLY
the provided document context.

Important rules:

- Use the context carefully.
- If the context contains the answer,
  answer it directly.
- Do not say information is unavailable
  if the answer is clearly present
  in the context.
- Do not use outside knowledge.
- If the answer truly cannot be found
  in the context, say:

"This information is not available
in the uploaded documents."

Document context:
----------------
{context}
----------------

User question:
{question}

Give a clear and concise answer.
"""

        response = llm.invoke(prompt)

        answer = response.content

        if isinstance(answer, list):

            parts = []

            for item in answer:

                if isinstance(item, dict):

                    if "text" in item:
                        parts.append(
                            str(item["text"])
                        )

                else:

                    parts.append(
                        str(item)
                    )

            answer = " ".join(parts)

        else:

            answer = str(answer)

        return {
            "answer": answer,
            "messages": [
                AIMessage(
                    content=answer
                )
            ]
        }

    graph = StateGraph(AgentState)

    graph.add_node(
        "generate_answer",
        generate_answer
    )

    graph.add_edge(
        START,
        "generate_answer"
    )

    graph.add_edge(
        "generate_answer",
        END
    )

    return graph.compile()