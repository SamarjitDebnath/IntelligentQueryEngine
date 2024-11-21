# Intelligent Query Engine: A Modern AI-Powered Query System

This repository hosts the **Intelligent Query Engine**, an AI-driven query solution that integrates advanced natural language processing with robust database querying. The system leverages state-of-the-art AI models, vector databases, and traditional relational databases to provide seamless, intelligent interactions with your data.

## Features

- **Google Gemini and Hugging Face Embeddings**: Harnesses the power of cutting-edge language models to understand natural language queries and convert them into precise SQL statements.
- **ChromaDB for Vector Storage**: Efficiently stores and retrieves embeddings for context-aware querying and semantic search.
- **MySQL Backend**: Queries structured data stored in a traditional relational database, ensuring compatibility with existing workflows.
- **LangChain Integration**: Chains complex logic and workflows, enabling multi-step querying and decision-making.
- **Notebook-Based Development**: Experimentation and prototyping in a flexible, interactive environment.

## Key Capabilities

1. **Natural Language to SQL**: Users can ask questions in plain English, and the engine generates accurate SQL queries to fetch results from MySQL.
2. **Semantic Search**: Find relevant information using vector-based similarity searches stored in ChromaDB.
3. **Dynamic Context Management**: Adapts to user queries with contextual understanding powered by Google Gemini and Hugging Face embeddings.
4. **Scalability**: Designed to handle large datasets and complex queries with ease.
5. **Modular Design**: Extensible architecture for integrating additional AI models or database systems.

## Applications

- Business Intelligence: Ask complex questions about your data and receive actionable insights.
- E-commerce: Query inventory, pricing, and sales data in natural language.
- Research: Extract patterns and trends from structured datasets without SQL expertise.
- Data Analytics Teams: Bridge the gap between technical and non-technical users by democratizing access to data.

## Getting Started

This repository includes an initial implementation in a notebook environment. Transitioning to a production-ready system will involve deploying the components to a scalable infrastructure.

### Components
1. **AI Model**: Google Gemini and Hugging Face embeddings (sentence-transformers/all-MiniLM-L6-v2) for query understanding.
2. **Vector Database**: ChromaDB for storing and retrieving embeddings.
3. **Relational Database**: MySQL for structured data storage.
4. **Orchestration**: LangChain for chaining steps like embedding retrieval, query generation, and data fetching.
