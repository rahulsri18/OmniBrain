# agents/output_parser.py
from typing import List, Any

def parse_retriever_output(documents: List[Any]) -> List[str]:
    """
    Retrieved documents को एक क्लीन, प्रॉम्ट-फ्रेंडली स्ट्रिंग्स की लिस्ट में बदलता है।
    यह LangChain Document ऑब्जेक्ट्स और रॉ स्ट्रिंग्स दोनों को हैंडल कर सकता है।
    """
    if not documents:
        return ["No relevant context found."]

    cleaned_docs = []
    for doc in documents:
        # अगर डेटा LangChain Document ऑब्जेक्ट है (जिसमें page_content होता है)
        if hasattr(doc, "page_content"):
            cleaned_docs.append(doc.page_content.strip())
        # अगर डेटा Qdrant का पेलोड/डिक्शनरी है
        elif isinstance(doc, dict) and "text" in doc:
            cleaned_docs.append(doc["text"].strip())
        # अगर डेटा पहले से ही डायरेक्ट स्ट्रिंग है
        elif isinstance(doc, str):
            cleaned_docs.append(doc.strip())
        else:
            cleaned_docs.append(str(doc).strip())

    return cleaned_docs