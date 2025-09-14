"""
RAG (Retrieval-Augmented Generation) system for My Beauty AI.
Implements LlamaIndex-based document processing and query engines.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib

from llama_index import (
    SimpleDirectoryReader, VectorStoreIndex, ServiceContext, 
    StorageContext, load_index_from_storage
)
from llama_index.llms import OpenAI
from llama_index.embeddings import OpenAIEmbedding
from llama_index.vector_stores import ChromaVectorStore
from llama_index.node_parser import SimpleNodeParser
from llama_index.query_engine import VectorIndexQueryEngine
from llama_index.retrievers import VectorIndexRetriever
from llama_index.response_synthesizers import ResponseMode

import chromadb
from chromadb.config import Settings

from config import config
from models import RAGDocument, get_db_session

logger = logging.getLogger(__name__)

@dataclass
class QueryResponse:
    """Structured response from RAG query"""
    response: str
    confidence: float
    sources: List[str]
    retrieved_nodes: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class RAGSystem:
    """
    Advanced RAG system for cosmetic ingredient knowledge.
    Provides semantic search and intelligent query answering.
    """

    def __init__(self):
        self.llm = None
        self.embedding_model = None
        self.index = None
        self.query_engine = None
        self.chroma_client = None
        self.collection = None
        self._initialize_components()

    def _initialize_components(self):
        """Initialize LLM, embeddings, and vector store components"""
        try:
            # Initialize OpenAI components
            self.llm = OpenAI(
                api_key=config.openai.api_key,
                model=config.openai.model,
                temperature=config.openai.temperature,
                max_tokens=config.openai.max_tokens
            )

            self.embedding_model = OpenAIEmbedding(
                api_key=config.openai.api_key,
                model=config.openai.embedding_model
            )

            # Initialize ChromaDB
            self._initialize_chroma_db()

            # Set up service context
            service_context = ServiceContext.from_defaults(
                llm=self.llm,
                embed_model=self.embedding_model,
                node_parser=SimpleNodeParser.from_defaults(
                    chunk_size=config.rag.chunk_size,
                    chunk_overlap=config.rag.chunk_overlap
                )
            )

            # Initialize or load existing index
            self._initialize_index(service_context)

            logger.info("RAG system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            raise

    def _initialize_chroma_db(self):
        """Initialize ChromaDB vector store"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(config.chromadb.persist_directory, exist_ok=True)

            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=config.chromadb.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=config.chromadb.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"ChromaDB initialized with collection: {config.chromadb.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def _initialize_index(self, service_context):
        """Initialize or load vector index"""
        storage_path = Path(config.chromadb.persist_directory) / "index_storage"

        try:
            if storage_path.exists():
                # Load existing index
                storage_context = StorageContext.from_defaults(persist_dir=str(storage_path))
                self.index = load_index_from_storage(
                    storage_context=storage_context,
                    service_context=service_context
                )
                logger.info("Loaded existing vector index")
            else:
                # Create new empty index
                vector_store = ChromaVectorStore(chroma_collection=self.collection)
                storage_context = StorageContext.from_defaults(vector_store=vector_store)

                self.index = VectorStoreIndex(
                    nodes=[],
                    storage_context=storage_context,
                    service_context=service_context
                )

                # Persist the empty index
                os.makedirs(storage_path, exist_ok=True)
                self.index.storage_context.persist(persist_dir=str(storage_path))

                logger.info("Created new vector index")

            # Initialize query engine
            self._setup_query_engine()

        except Exception as e:
            logger.error(f"Failed to initialize vector index: {e}")
            raise

    def _setup_query_engine(self):
        """Set up query engine with retrieval and synthesis"""
        try:
            retriever = VectorIndexRetriever(
                index=self.index,
                similarity_top_k=config.chromadb.similarity_top_k
            )

            self.query_engine = VectorIndexQueryEngine(
                retriever=retriever,
                response_mode=ResponseMode.COMPACT,
                service_context=self.index.service_context
            )

            logger.info("Query engine configured successfully")

        except Exception as e:
            logger.error(f"Failed to setup query engine: {e}")
            raise

    def add_documents(self, documents: List[str], metadata_list: List[Dict[str, Any]] = None) -> bool:
        """
        Add documents to the RAG knowledge base.

        Args:
            documents: List of document texts
            metadata_list: Optional list of metadata dicts for each document

        Returns:
            Success status
        """
        try:
            if not documents:
                logger.warning("No documents provided for indexing")
                return False

            # Parse documents into nodes
            node_parser = SimpleNodeParser.from_defaults(
                chunk_size=config.rag.chunk_size,
                chunk_overlap=config.rag.chunk_overlap
            )

            all_nodes = []
            for i, doc_text in enumerate(documents):
                # Create document object
                from llama_index import Document
                doc = Document(
                    text=doc_text,
                    metadata=metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                )

                # Parse into nodes
                nodes = node_parser.get_nodes_from_documents([doc])
                all_nodes.extend(nodes)

            # Add nodes to index
            self.index.insert_nodes(all_nodes)

            # Persist updated index
            storage_path = Path(config.chromadb.persist_directory) / "index_storage"
            self.index.storage_context.persist(persist_dir=str(storage_path))

            logger.info(f"Successfully added {len(documents)} documents ({len(all_nodes)} nodes)")
            return True

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False

    def add_documents_from_directory(self, directory_path: str) -> bool:
        """
        Load and add documents from a directory.

        Args:
            directory_path: Path to directory containing documents

        Returns:
            Success status
        """
        try:
            if not os.path.exists(directory_path):
                logger.error(f"Directory does not exist: {directory_path}")
                return False

            # Load documents from directory
            reader = SimpleDirectoryReader(directory_path)
            documents = reader.load_data()

            if not documents:
                logger.warning(f"No documents found in {directory_path}")
                return False

            # Add documents to index
            self.index.insert_nodes(documents)

            # Persist updated index
            storage_path = Path(config.chromadb.persist_directory) / "index_storage"
            self.index.storage_context.persist(persist_dir=str(storage_path))

            logger.info(f"Successfully loaded {len(documents)} documents from {directory_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load documents from directory: {e}")
            return False

    def query(self, query_text: str, **kwargs) -> QueryResponse:
        """
        Execute a general query against the knowledge base.

        Args:
            query_text: Natural language query
            **kwargs: Additional query parameters

        Returns:
            QueryResponse with answer and metadata
        """
        try:
            if not self.query_engine:
                raise ValueError("Query engine not initialized")

            # Execute query
            response = self.query_engine.query(query_text)

            # Extract source information
            sources = []
            retrieved_nodes = []

            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'metadata'):
                        sources.append(node.metadata.get('source', 'Unknown'))
                        retrieved_nodes.append({
                            'content': node.text[:200] + "..." if len(node.text) > 200 else node.text,
                            'metadata': node.metadata,
                            'score': getattr(node, 'score', 0.0)
                        })

            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(retrieved_nodes)

            return QueryResponse(
                response=str(response),
                confidence=confidence,
                sources=sources,
                retrieved_nodes=retrieved_nodes,
                metadata={
                    'query': query_text,
                    'timestamp': self._get_timestamp(),
                    'model_used': config.openai.model
                }
            )

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResponse(
                response=f"Sorry, I encountered an error processing your query: {str(e)}",
                confidence=0.0,
                sources=[],
                retrieved_nodes=[],
                metadata={'error': str(e)}
            )

    def query_ingredient_interaction(self, ingredient1: str, ingredient2: str, 
                                   context: Dict[str, Any] = None) -> QueryResponse:
        """
        Specialized query for ingredient interactions.

        Args:
            ingredient1: First ingredient name
            ingredient2: Second ingredient name
            context: Additional context (skin type, concerns, etc.)

        Returns:
            QueryResponse with interaction analysis
        """
        # Construct specialized query
        query_parts = [
            f"Can {ingredient1} and {ingredient2} be used together?",
            f"What are the interactions between {ingredient1} and {ingredient2}?",
            "Are there any conflicts or contraindications?"
        ]

        if context:
            if 'skin_type' in context:
                query_parts.append(f"Consider {context['skin_type']} skin type.")
            if 'concerns' in context:
                query_parts.append(f"Skin concerns: {', '.join(context['concerns'])}")

        query_text = " ".join(query_parts)

        return self.query(query_text, context=context)

    def query_routine_optimization(self, products: List[Dict[str, Any]], 
                                 user_profile: Dict[str, Any]) -> QueryResponse:
        """
        Query for routine optimization recommendations.

        Args:
            products: List of products with ingredients
            user_profile: User skin profile and preferences

        Returns:
            QueryResponse with optimization suggestions
        """
        # Extract ingredients from products
        ingredients = []
        for product in products:
            if 'ingredients' in product:
                ingredients.extend(product['ingredients'])

        # Construct optimization query
        query_text = f"""
        Optimize this skincare routine for {user_profile.get('skin_type', 'normal')} skin:

        Products: {[p.get('name', 'Unknown') for p in products]}
        Ingredients: {', '.join(set(ingredients))}
        Skin concerns: {', '.join(user_profile.get('concerns', []))}

        Provide recommendations for:
        1. Application order
        2. Timing (morning/evening)
        3. Frequency of use
        4. Potential conflicts to avoid
        """

        return self.query(query_text.strip())

    def get_ingredient_information(self, ingredient_name: str) -> QueryResponse:
        """
        Get comprehensive information about a specific ingredient.

        Args:
            ingredient_name: Name of the ingredient

        Returns:
            QueryResponse with ingredient information
        """
        query_text = f"""
        Provide comprehensive information about {ingredient_name}:

        1. What is {ingredient_name}?
        2. Benefits and effects on skin
        3. Recommended concentration ranges
        4. Common side effects or considerations
        5. Which skin types benefit most
        6. Ingredients it works well with
        7. Ingredients to avoid combining with
        """

        return self.query(query_text.strip())

    def _calculate_confidence(self, retrieved_nodes: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on retrieval results"""
        if not retrieved_nodes:
            return 0.0

        # Average the retrieval scores
        total_score = sum(node.get('score', 0.0) for node in retrieved_nodes)
        avg_score = total_score / len(retrieved_nodes)

        # Normalize to 0-1 range (assuming scores are similarity scores)
        confidence = min(max(avg_score, 0.0), 1.0)

        return confidence

    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            if self.collection:
                count = self.collection.count()
                return {
                    'total_documents': count,
                    'collection_name': config.chromadb.collection_name,
                    'embedding_model': config.openai.embedding_model,
                    'index_initialized': self.index is not None
                }
            return {'error': 'Collection not initialized'}

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {'error': str(e)}

    def clear_knowledge_base(self) -> bool:
        """Clear all documents from the knowledge base"""
        try:
            if self.collection:
                # Delete the collection
                self.chroma_client.delete_collection(config.chromadb.collection_name)

                # Recreate empty collection
                self.collection = self.chroma_client.create_collection(
                    name=config.chromadb.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

                # Reinitialize index
                self._initialize_index(self.index.service_context)

                logger.info("Knowledge base cleared successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False

def initialize_knowledge_base(data_directory: str = None) -> RAGSystem:
    """
    Initialize the RAG system and optionally load initial documents.

    Args:
        data_directory: Optional path to directory with initial documents

    Returns:
        Initialized RAG system
    """
    try:
        rag_system = RAGSystem()

        if data_directory and os.path.exists(data_directory):
            success = rag_system.add_documents_from_directory(data_directory)
            if success:
                logger.info(f"Loaded initial documents from {data_directory}")
            else:
                logger.warning(f"Failed to load documents from {data_directory}")

        return rag_system

    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        raise

# Export main classes and functions
__all__ = [
    'RAGSystem',
    'QueryResponse',
    'initialize_knowledge_base'
]
