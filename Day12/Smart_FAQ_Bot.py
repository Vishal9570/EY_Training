import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_anthropic import ChatAnthropic

FAQS = [
    "What is health insurance? Health insurance helps cover medical expenses.",
    "How do I file a claim? You can file a claim through the company portal.",
    "What is a deductible? A deductible is the amount you pay before insurance starts.",
    "What is a premium? A premium is the amount paid regularly for insurance coverage.",
    "What is cashless treatment? Cashless treatment allows hospital bills to be settled directly.",
    "Can I add my parents to insurance? Yes, parents can be added if the policy supports it.",
    "What is OPD coverage? OPD coverage includes doctor visits without hospital admission.",
    "What is pre-authorization? It is approval required before planned hospitalization.",
    "What is claim rejection? A claim can be rejected if policy terms are not met.",
    "How can I check claim status? You can check claim status on the insurance portal."
]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable.")

docs = [
    Document(page_content=faq, metadata={"faq_id": i + 1})
    for i, faq in enumerate(FAQS)
]

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = FAISS.from_documents(
    documents=docs,
    embedding=embedding_model
)

retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 2, "score_threshold": 0.0}
)

llm = None
if ANTHROPIC_API_KEY:
    llm = ChatAnthropic(model="claude-3-haiku-20240307")

def answer_query(query):
    results_with_score = vectorstore.similarity_search_with_score(query, k=2)

    context = ""
    for doc, score in results_with_score:
        context += f"FAQ: {doc.page_content}\nSimilarity Score: {score:.4f}\n\n"

    if llm:
        prompt = f"""
You are a Smart FAQ Bot.
Answer the user query using only the FAQ context below.
Keep the answer concise and grounded.

Context:
{context}

User Query:
{query}
"""
        response = llm.invoke(prompt)
        return response.content, results_with_score

    best_doc = results_with_score[0][0]
    return best_doc.page_content, results_with_score

print("Smart FAQ Bot is ready. Type 'exit' to quit.")

while True:
    user_query = input("\nAsk your question: ")

    if user_query.lower() == "exit":
        print("Goodbye!")
        break

    response, matched_docs = answer_query(user_query)

    print("\nAnswer:")
    print(response)

    print("\nTop Matches:")
    for doc, score in matched_docs:
        print(f"- FAQ ID {doc.metadata['faq_id']} | Score: {score:.4f}")