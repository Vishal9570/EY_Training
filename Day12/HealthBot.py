'''Design Choices

Use Azure AI Search Hybrid Search instead of Weaviate on AKS because the requirement says HIPAA + Azure-only data residency. Azure AI Search reduces infra management, supports keyword + vector search, filtering, and enterprise security.

Use 1024-token chunks with 150 overlap because clinical text has lists, tables, and protocols. Very small chunks lose medical context, while very large chunks increase latency.

Use multi-index strategy by clinical domain like cardiology, oncology, pharmacy, emergency-care. This improves accuracy and reduces retrieval latency.

Use RAG for most questions, but skip RAG only when the query is general conversation or does not require clinical knowledge.'''


# Bloack Diagram:
'''
Clinician UI
    |
    v
API Gateway / Auth
    |
    v
Query Classifier
    |
    v
Domain Router
    |
    v
Azure AI Search
(Hybrid Search: BM25 + Vector)
    |
    v
Top-K Clinical Chunks
    |
    v
Reranker + Safety Filter
    |
    v
Claude / Azure OpenAI LLM
    |
    v
Grounded Answer + Citations
    |
    v
Audit Logs + Monitoring'''

import os
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="HealthBot Clinical RAG")

CLINICAL_DOCS = [
    """
    Diabetes Protocol:
    Monitor fasting blood glucose regularly. Lifestyle modification,
    diet control, exercise, and medication adherence are important.
    Insulin may be required for uncontrolled diabetes.
    """,
    """
    Hypertension Guideline:
    Blood pressure should be monitored regularly. Treatment may include
    lifestyle changes, reduced salt intake, exercise, and antihypertensive drugs.
    """,
    """
    Drug Interaction:
    Warfarin has major interactions with NSAIDs and some antibiotics.
    Patients should be monitored for bleeding risk.
    """,
    """
    Emergency Protocol:
    Chest pain with sweating, breathlessness, or radiating pain should be
    treated as a possible cardiac emergency.
    """,
    """
    Oncology Protocol:
    Cancer treatment may include surgery, chemotherapy, radiation therapy,
    immunotherapy, or targeted therapy depending on cancer type and stage.
    """
]

embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
    openai_api_version="2024-02-01"
)

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_CHAT_DEPLOYMENT"),
    openai_api_version="2024-02-01",
    temperature=0
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=150
)

docs: List[Document] = []

for i, text in enumerate(CLINICAL_DOCS):
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": f"clinical_doc_{i+1}"}]
    )
    docs.extend(chunks)

vectorstore = FAISS.from_documents(docs, embedding_model)

class QueryRequest(BaseModel):
    question: str

def retrieve_context(question: str):
    results = vectorstore.similarity_search_with_score(question, k=3)
    context = ""
    citations = []

    for doc, score in results:
        context += doc.page_content + "\n\n"
        citations.append({
            "source": doc.metadata["source"],
            "score": float(score)
        })

    return context, citations

@app.post("/ask")
def ask_healthbot(request: QueryRequest):
    context, citations = retrieve_context(request.question)

    prompt = f"""
You are HealthBot, a clinical RAG assistant.
Answer only using the provided clinical context.
If the answer is not found, say: "I do not have enough clinical context."
Do not invent medical advice.

Clinical Context:
{context}

Question:
{request.question}

Return a concise answer with citations.
"""

    response = llm.invoke(prompt)

    return {
        "question": request.question,
        "answer": response.content,
        "citations": citations
    }

@app.get("/health")
def health():
    return {"status": "HealthBot is running"}