from openai import OpenAI

client = OpenAI()


def rewrite_question_for_retrieval(
    question: str,
    conversation_history: list[dict] | None = None,
) -> str:
    if not conversation_history:
        return question

    history_lines = []

    for message in conversation_history:
        history_lines.append(
            f"{message['role'].upper()}: {message['content']}"
        )

    history_text = "\n".join(history_lines)

    prompt = f"""
You rewrite conversational follow-up questions into standalone search queries.

Use the conversation history only to understand what the user is referring to.

Rewrite the current question so it can be understood without seeing the previous conversation.

Do not answer the question.
Do not add information that is not present in the conversation.
Keep the rewritten query concise.

Conversation History:
{history_text}

Current Question:
{question}

Standalone Search Query:
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    rewritten_question = response.output_text.strip()

    return rewritten_question or question


def generate_grounded_answer(
    question: str,
    context_chunks: list[str],
    conversation_history: list[dict] | None = None,
) -> str:
    context = "\n\n".join(context_chunks)

    history_text = ""

    if conversation_history:
        history_lines = []

        for message in conversation_history:
            history_lines.append(
                f"{message['role'].upper()}: {message['content']}"
            )

        history_text = "\n".join(history_lines)

    prompt = f"""
You are a company knowledge assistant.

Use the conversation history only to understand what the user is referring to.

Answer the user's current question using ONLY the retrieved document context.

If the answer is not supported by the retrieved context, say:
"I couldn't find that information in the uploaded knowledge base."

Conversation History:
{history_text}

Retrieved Document Context:
{context}

Current Question:
{question}
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text