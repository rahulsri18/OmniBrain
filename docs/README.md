\# OmniBrain LangGraph Agent Flow



\## Overview



This document describes the LangGraph workflow used in OmniBrain.



It explains:



\- Overall LangGraph architecture

\- Agent execution flow

\- Node-by-node responsibilities

\- Routing logic

\- GraphState structure

\- Self-RAG execution cycle



\---



\## LangGraph Architecture

&#x20;```text

&#x20;                          START

&#x20;                            │

&#x20;                            ▼

&#x20;                 +----------------------+

&#x20;                 |   Input Guardrail    |

&#x20;                 +----------------------+

&#x20;                            │

&#x20;                            ▼

&#x20;                 +----------------------+

&#x20;                 | Supervisor / Router  |

&#x20;                 +----------------------+

&#x20;                            │

&#x20;      ┌──────────────┬──────────────┬──────────────┐

&#x20;      │              │              │              │

&#x20;      ▼              ▼              ▼              ▼

+-------------+ +-------------+ +-------------+ +-------------+

| Retriever   | | SQL Agent   | | Vision Node | | General LLM |

+-------------+ +-------------+ +-------------+ +-------------+

&#x20;      │              │              │              │

&#x20;      └──────────────┴──────────────┴──────────────┘

&#x20;                            │

&#x20;                            ▼

&#x20;                 +----------------------+

&#x20;                 |  Output Guardrail    |

&#x20;                 +----------------------+

&#x20;                            │

&#x20;                            ▼

&#x20;                 +----------------------+

&#x20;                 |   Fallback Handler   |

&#x20;                 +----------------------+

&#x20;                            │

&#x20;                            ▼

&#x20;                           END

```

\---



\# Node Reference



\## 1. Input Guardrail



\*\*Purpose\*\*



\- Validates user input before entering the LangGraph workflow.

\- Detects unsafe prompts and blocks malicious requests.



\*\*Input\*\*



\- User query



\*\*Output\*\*



\- Validated GraphState



\*\*Next Node\*\*



\- Supervisor / Router



\---



\## 2. Supervisor / Router



\*\*Purpose\*\*



\- Receives the validated user query.

\- Determines which specialized agent should process the request.

\- Selects one of the available execution routes.



\*\*Possible Routes\*\*



\- Retriever

\- SQL Agent

\- Vision Node

\- General LLM



\*\*Input\*\*



\- GraphState

&#x20;---



\# GraphState Structure



The LangGraph workflow shares information between nodes through a common GraphState object.



| Field | Description |

|-------|-------------|

| question | User query received by the system |

| chat\_history | Previous conversation history |

| context | Retrieved document context |

| response | Final generated answer |

| route | Selected execution path |

| metadata | Additional execution metadata |

| sql\_result | SQL execution output |

| retriever\_result | Retrieved vector search results |

| merged\_context | Combined retrieval context |

| loop\_count | Number of Self-RAG retries |

| max\_loops | Maximum retry limit |

| error | Error information, if any |





\*\*Output\*\*



\- Route information



\---



\## 3. Retriever Node



\*\*Purpose\*\*



\- Searches the vector database.

\- Retrieves relevant document chunks.

\- Supplies context for Retrieval-Augmented Generation (RAG).



\*\*Input\*\*



\- User query



\*\*Output\*\*



\- Retrieved document context



\---



\## 4. SQL Agent



\*\*Purpose\*\*



\- Converts natural language into SQL queries.

\- Retrieves structured information from relational databases.



\*\*Input\*\*



\- User query



\*\*Output\*\*



\- SQL query results



\---



\## 5. Vision Node



\*\*Purpose\*\*



\- Processes images, charts, and visual documents.

\- Uses multimodal models for visual understanding.



\*\*Input\*\*



\- Image or chart



\*\*Output\*\*



\- Vision analysis results



\---



\## 6. General LLM



\*\*Purpose\*\*



\- Handles general conversational requests.

\- Generates responses that do not require retrieval or SQL execution.



\*\*Input\*\*



\- User query



\*\*Output\*\*



\- Generated response



\---



\## 7. Output Guardrail



\*\*Purpose\*\*



\- Validates the generated response.

\- Filters unsafe or invalid outputs before returning them to the user.



\*\*Input\*\*



\- Generated response



\*\*Output\*\*



\- Safe response



\---



\## 8. Fallback Handler



\*\*Purpose\*\*



\- Handles execution failures.

\- Returns graceful error messages.

\- Prevents workflow interruption.



\*\*Input\*\*



\- Error state



\*\*Output\*\*



\- Recovery response



\---



\# Self-RAG Execution Flow



The retrieval pipeline follows a Self-RAG strategy.



```text

User Query

&#x20;     │

&#x20;     ▼

Document Retrieval

&#x20;     │

&#x20;     ▼

Document Grading

&#x20;     │

&#x20;     ├──────── Relevant ─────────► Response Generation

&#x20;     │

&#x20;     ▼

Query Rewriting

&#x20;     │

&#x20;     ▼

Retrieve Again

&#x20;     │

&#x20;     ▼

Document Grading

&#x20;     │

&#x20;     ▼

Response Generation

```



The workflow continues until:



\- Relevant context is found.

\- Maximum retry limit is reached.



\---



\# Overall Execution Sequence



```text

User

&#x20;│

&#x20;▼

Input Guardrail

&#x20;│

&#x20;▼

Supervisor / Router

&#x20;│

&#x20;├── Retriever

&#x20;├── SQL Agent

&#x20;├── Vision Node

&#x20;└── General LLM

&#x20;│

&#x20;▼

Output Guardrail

&#x20;│

&#x20;▼

Fallback Handler (if required)

&#x20;│

&#x20;▼

Final Response

```



\---



\# Conclusion



The LangGraph workflow provides a modular multi-agent architecture that supports routing, retrieval, structured querying, multimodal reasoning, safety validation, and fallback handling. This design enables scalable and maintainable execution while supporting Retrieval-Augmented Generation (RAG), SQL querying, and vision-based analysis within a unified workflow.



