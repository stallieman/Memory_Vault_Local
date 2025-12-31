"""
Local RAG with Ollama + ChromaDB Knowledge Base
Interactive Q&A using local Ollama LLM with C:\\Notes as knowledge base.
"""

import os
import sys
import requests
from pathlib import Path
from ingestion import DocumentIngestion

# Configuration via environment variables
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral-nemo:12b-instruct-2407-q4_K_M")
TOP_K = int(os.environ.get("RAG_TOP_K", "4"))
TOP_K_FULL = int(os.environ.get("RAG_TOP_K_FULL", "2"))
SNIPPET_CHARS = int(os.environ.get("RAG_SNIPPET_CHARS", "400"))
MAX_CHARS_FULL = int(os.environ.get("RAG_MAX_CHARS_FULL", "4500"))


def check_ollama_connection() -> tuple[bool, list[str]]:
    """
    Check if Ollama is running and get available models.
    Returns (is_connected, list_of_model_names).
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return True, models
    except requests.exceptions.ConnectionError:
        return False, []
    except requests.exceptions.Timeout:
        return False, []
    except Exception as e:
        print(f"⚠ Unexpected error checking Ollama: {e}")
        return False, []


def get_effective_model(available_models: list[str]) -> str:
    """
    Get the effective model to use.
    If OLLAMA_MODEL is in available_models, use it.
    Otherwise, suggest available models.
    """
    if OLLAMA_MODEL in available_models:
        return OLLAMA_MODEL
    
    # Check if the base model name (without tag) matches
    base_model = OLLAMA_MODEL.split(":")[0]
    for model in available_models:
        if model.startswith(base_model):
            print(f"⚠ Exact model '{OLLAMA_MODEL}' not found.")
            print(f"  Using similar model: '{model}'")
            return model
    
    # No matching model found
    print(f"⚠ Model '{OLLAMA_MODEL}' not found in Ollama.")
    if available_models:
        print(f"  Available models: {', '.join(available_models)}")
        print(f"  Using first available: '{available_models[0]}'")
        return available_models[0]
    
    # No models available at all
    print("✗ No models found in Ollama. Please pull a model first:")
    print(f"  ollama pull {OLLAMA_MODEL}")
    return OLLAMA_MODEL  # Will fail at chat time


def retrieve_context(kb: DocumentIngestion, question: str) -> list[dict]:
    """
    Retrieve relevant context chunks from the knowledge base.
    Returns a list of dicts with text, metadata, id, and score.
    """
    result = kb.query(question, n_results=TOP_K)
    
    if not result["results"] or not result["results"]["ids"][0]:
        return []
    
    documents = result["results"]["documents"][0]
    metadatas = result["results"]["metadatas"][0]
    distances = result["results"]["distances"][0]
    ids = result["results"]["ids"][0]

    context_chunks = []
    for i, (doc, meta, dist, doc_id) in enumerate(zip(documents, metadatas, distances, ids)):
        if i >= TOP_K_FULL:
            break
            
        text = doc.strip()
        if len(text) > MAX_CHARS_FULL:
            text = text[:MAX_CHARS_FULL].rstrip() + "..."
        
        context_chunks.append({
            "text": text,
            "metadata": meta,
            "id": doc_id,
            "score": 1 - float(dist)
        })
    
    return context_chunks


def ask_ollama(question: str, context_chunks: list[dict], model: str) -> str:
    """
    Send a question with context to Ollama and get the response.
    """
    system_prompt = """You are a helpful assistant that answers questions using ONLY the provided context.
If the answer is not in the context, say you don't know.
Always answer concisely and in Dutch."""

    # Build context text with source citations
    context_parts = []
    for chunk in context_chunks:
        meta = chunk["metadata"]
        header = f"[Source: {meta.get('relative_path', meta.get('filename', 'unknown'))}]"
        context_parts.append(header + "\n\n" + chunk["text"])
    
    context_text = "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""Context:
{context_text}

Question: {question}"""}
    ]

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": messages,
                "options": {"temperature": 0.1, "num_ctx": 8192}
            },
            timeout=300
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        return "Error: Ollama request timed out."
    except Exception as e:
        return f"Error calling Ollama: {str(e)}"


def main():
    """Main interactive loop for RAG Q&A."""
    print("=" * 60)
    print("Local RAG with Ollama + C:\\Notes")
    print("=" * 60)
    
    # Check Ollama connection
    print("\n🔍 Checking Ollama connection...")
    is_connected, available_models = check_ollama_connection()
    
    if not is_connected:
        print("\n" + "=" * 60)
        print("✗ ERROR: Ollama is not running.")
        print("  Start Ollama Desktop or run `ollama serve`.")
        print("=" * 60)
        sys.exit(1)
    
    print(f"✓ Ollama is running at {OLLAMA_BASE_URL}")
    print(f"  Available models: {', '.join(available_models) if available_models else 'None'}")
    
    # Determine effective model
    effective_model = get_effective_model(available_models)
    print(f"\n📦 Using model: {effective_model}")
    
    # Initialize knowledge base
    print("\n📚 Initializing knowledge base...")
    try:
        kb = DocumentIngestion()
    except Exception as e:
        print(f"✗ Error initializing knowledge base: {e}")
        sys.exit(1)
    
    print(f"\n✓ Ready!")
    print(f"  - Data directory: C:\\Notes")
    print(f"  - Model: {effective_model}")
    print(f"  - Context chunks: {TOP_K_FULL}")
    print("-" * 60)
    print("Type your question and press Enter. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break

        if not question:
            continue
            
        if question.lower() in {"exit", "quit", "q"}:
            print("\n👋 Goodbye!")
            break

        print("\n🔍 Searching knowledge base...")
        context = retrieve_context(kb, question)
        
        if not context:
            print("⚠ No relevant results found in knowledge base.\n")
            continue

        print(f"✓ Found {len(context)} relevant chunks.")
        
        # Show sources
        print("  Sources:")
        for chunk in context:
            meta = chunk["metadata"]
            source = meta.get("relative_path", meta.get("filename", "unknown"))
            print(f"    - {source} (score: {chunk['score']:.2f})")
        
        print(f"\n🤖 Asking {effective_model}...")
        answer = ask_ollama(question, context, effective_model)
        
        print("\n" + "=" * 60)
        print("Answer:")
        print("-" * 60)
        print(answer)
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
