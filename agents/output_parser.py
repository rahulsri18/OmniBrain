# agents/output_parser.py
from typing import List, Any

def parse_retriever_output(documents: List[Any]) -> List[str]:
    if not documents:
        return ["No relevant context found."]

    cleaned_docs = []
    for doc in documents:
        if hasattr(doc, "page_content"):
            cleaned_docs.append(doc.page_content.strip())
        elif isinstance(doc, dict) and "text" in doc:
            cleaned_docs.append(doc["text"].strip())
        elif isinstance(doc, str):
            cleaned_docs.append(doc.strip())
        else:
            cleaned_docs.append(str(doc).strip())

    return cleaned_docs