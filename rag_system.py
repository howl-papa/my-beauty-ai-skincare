"""
My Beauty AI RAG System

LlamaIndex-based Retrieval-Augmented Generation system for cosmetic knowledge.
This module handles document indexing, vector storage, and knowledge retrieval.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json

from llama_index.core import (
    VectorStoreIndex, 
    Document, 
    StorageContext,
    Settings,
    SimpleDirectoryReader,
    get_response_synthesizer
)
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_config
from models import KnowledgeDocument, DocumentIngredient, Ingredient
from sqlalchemy.orm import Session
from loguru import logger


class BeautyRAGSystem:
    """
    Retrieval-Augmented Generation system for cosmetic knowledge.

    Handles document ingestion, vector indexing, and intelligent retrieval
    for ingredient interactions, routine recommendations, and safety information.
    """

    def __init__(self, db_session: Session = None):
        self.config = get_config()
        self.db_session = db_session

        # Initialize components
        self._setup_llm()
        self._setup_embeddings()
        self._setup_vector_store()
        self._setup_parsers()
        self._setup_index()

        logger.info("Beauty RAG System initialized successfully")

    def _setup_llm(self):
        """Initialize the language model."""
        Settings.llm = OpenAI(
            model=self.config.openai.model,
            temperature=self.config.openai.temperature,
            max_tokens=self.config.openai.max_tokens,
            api_key=self.config.openai.api_key
        )
        logger.debug(f"LLM initialized: {self.config.openai.model}")

    def _setup_embeddings(self):
        """Initialize embedding model."""
        Settings.embed_model = OpenAIEmbedding(
            model=self.config.openai.embedding_model,
            api_key=self.config.openai.api_key
        )
        logger.debug(f"Embeddings initialized: {self.config.openai.embedding_model}")

    def _setup_vector_store(self):
        """Initialize vector database."""
        if self.config.vector_store.provider == 'chroma':
            # Ensure persist directory exists
            persist_dir = Path(self.config.vector_store.chroma_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)

            # Initialize ChromaDB client
            chroma_client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False)
            )

            # Get or create collection
            collection_name = self.config.vector_store.chroma_collection_name
            try:
                chroma_collection = chroma_client.get_collection(collection_name)
                logger.info(f"Loaded existing Chroma collection: {collection_name}")
            except:
                chroma_collection = chroma_client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": self.config.vector_store.similarity_metric}
                )
                logger.info(f"Created new Chroma collection: {collection_name}")

            # Create vector store
            self.vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        elif self.config.vector_store.provider == 'pinecone':
            # Pinecone implementation would go here
            raise NotImplementedError("Pinecone support not yet implemented")

        else:
            raise ValueError(f"Unsupported vector store provider: {self.config.vector_store.provider}")

    def _setup_parsers(self):
        """Initialize document parsers and text splitters."""
        self.node_parser = SentenceSplitter(
            chunk_size=self.config.vector_store.chunk_size,
            chunk_overlap=self.config.vector_store.chunk_overlap
        )
        Settings.node_parser = self.node_parser
        logger.debug(f"Node parser configured: chunk_size={self.config.vector_store.chunk_size}")

    def _setup_index(self):
        """Initialize or load the vector index."""
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        try:
            # Try to load existing index
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=storage_context
            )
            logger.info("Loaded existing vector index")
        except:
            # Create new index if none exists
            self.index = VectorStoreIndex([], storage_context=storage_context)
            logger.info("Created new vector index")

    def add_documents_from_directory(self, directory_path: str, 
                                   supported_formats: List[str] = None) -> int:
        """
        Add documents from a directory to the knowledge base.

        Args:
            directory_path: Path to directory containing documents
            supported_formats: List of file extensions to process

        Returns:
            Number of documents added
        """
        if supported_formats is None:
            supported_formats = ['.txt', '.pdf', '.docx', '.md']

        try:
            # Load documents
            reader = SimpleDirectoryReader(
                input_dir=directory_path,
                required_exts=supported_formats,
                recursive=True
            )
            documents = reader.load_data()

            if not documents:
                logger.warning(f"No documents found in {directory_path}")
                return 0

            # Process and add to index
            nodes = self.node_parser.get_nodes_from_documents(documents)
            self.index.insert_nodes(nodes)

            # Store metadata in database if session available
            if self.db_session:
                for doc in documents:
                    self._store_document_metadata(doc)

            logger.info(f"Added {len(documents)} documents from {directory_path}")
            return len(documents)

        except Exception as e:
            logger.error(f"Error adding documents from {directory_path}: {e}")
            raise

    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Add a single document to the knowledge base.

        Args:
            content: Document content as string
            metadata: Optional metadata dictionary

        Returns:
            Document ID
        """
        try:
            # Create document
            doc = Document(text=content, metadata=metadata or {})

            # Process and add to index
            nodes = self.node_parser.get_nodes_from_documents([doc])
            self.index.insert_nodes(nodes)

            # Store in database if session available
            doc_id = None
            if self.db_session and metadata:
                doc_id = self._store_document_metadata(doc)

            logger.info(f"Added document: {doc_id or 'unknown'}")
            return doc_id or doc.doc_id

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise

    def _store_document_metadata(self, doc: Document) -> str:
        """Store document metadata in PostgreSQL database."""
        try:
            metadata = doc.metadata or {}

            knowledge_doc = KnowledgeDocument(
                title=metadata.get('title', f'Document {doc.doc_id}'),
                content=doc.text[:10000],  # Store first 10k characters
                document_type=metadata.get('document_type', 'unknown'),
                source_url=metadata.get('source_url'),
                publication_date=metadata.get('publication_date'),
                authors=metadata.get('authors', []),
                journal=metadata.get('journal'),
                doi=metadata.get('doi'),
                credibility_score=metadata.get('credibility_score', 5)
            )

            self.db_session.add(knowledge_doc)
            self.db_session.commit()

            return str(knowledge_doc.document_id)

        except Exception as e:
            logger.error(f"Error storing document metadata: {e}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def create_query_engine(self, similarity_top_k: int = None, 
                          similarity_threshold: float = None) -> RetrieverQueryEngine:
        """
        Create a query engine for answering questions.

        Args:
            similarity_top_k: Number of top similar documents to retrieve
            similarity_threshold: Minimum similarity score for results

        Returns:
            Configured query engine
        """
        # Use config defaults if not specified
        top_k = similarity_top_k or self.config.vector_store.top_k_retrieval
        threshold = similarity_threshold or self.config.vector_store.similarity_threshold

        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k
        )

        # Create post-processor for filtering results
        postprocessor = SimilarityPostprocessor(similarity_cutoff=threshold)

        # Create response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",  # More concise responses
            use_async=False
        )

        # Create query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[postprocessor]
        )

        return query_engine

    def query_ingredients_interaction(self, ingredients: List[str], 
                                    user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query potential interactions between ingredients.

        Args:
            ingredients: List of ingredient names
            user_context: Optional user context (skin type, concerns, etc.)

        Returns:
            Analysis results with conflicts and recommendations
        """
        # Build context-aware query
        query_parts = [
            f"Analyze potential interactions and conflicts between these cosmetic ingredients: {', '.join(ingredients)}."
        ]

        if user_context:
            if user_context.get('skin_type'):
                query_parts.append(f"Consider this is for {user_context['skin_type']} skin type.")
            if user_context.get('skin_concerns'):
                concerns = ', '.join(user_context['skin_concerns'])
                query_parts.append(f"The user has concerns about: {concerns}.")

        query_parts.extend([
            "Focus on:",
            "1. Chemical incompatibilities that could cause reactions",
            "2. pH level conflicts that might reduce effectiveness",
            "3. Physical formulation issues like pilling or separation",
            "4. Concentration-dependent interactions",
            "5. Timing recommendations (AM/PM separation)",
            "6. Any safety concerns or contraindications"
        ])

        query = " ".join(query_parts)

        try:
            # Create specialized query engine
            query_engine = self.create_query_engine(
                similarity_top_k=8,  # More results for comprehensive analysis
                similarity_threshold=0.6  # Lower threshold for broader context
            )

            # Execute query
            response = query_engine.query(query)

            # Parse and structure response
            result = {
                'ingredients': ingredients,
                'analysis': str(response),
                'sources': self._extract_sources(response),
                'confidence': self._calculate_confidence(response),
                'user_context': user_context
            }

            logger.info(f"Analyzed interactions for {len(ingredients)} ingredients")
            return result

        except Exception as e:
            logger.error(f"Error querying ingredient interactions: {e}")
            raise

    def query_routine_optimization(self, products: List[Dict[str, Any]], 
                                 user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimized routine recommendations.

        Args:
            products: List of product dictionaries with names and ingredients
            user_profile: User profile with preferences and skin info

        Returns:
            Optimized routine with timing and order recommendations
        """
        # Extract product names and ingredients
        product_names = [p.get('name', 'Unknown') for p in products]
        all_ingredients = []
        for product in products:
            all_ingredients.extend(product.get('ingredients', []))

        # Build comprehensive query
        query_parts = [
            f"Create an optimized skincare routine using these {len(products)} products: {', '.join(product_names)}.",
            f"The products contain these key ingredients: {', '.join(set(all_ingredients))}."
        ]

        # Add user context
        if user_profile.get('skin_type'):
            query_parts.append(f"User has {user_profile['skin_type']} skin.")

        if user_profile.get('skin_concerns'):
            concerns = ', '.join(user_profile['skin_concerns'])
            query_parts.append(f"Main skin concerns: {concerns}.")

        if user_profile.get('routine_complexity'):
            query_parts.append(f"Preferred routine complexity: {user_profile['routine_complexity']}.")

        query_parts.extend([
            "Provide recommendations for:",
            "1. Optimal application order (thinnest to thickest consistency)",
            "2. Morning vs evening usage for each product",
            "3. Wait times between applications if needed",
            "4. Frequency of use (daily, alternate days, weekly)",
            "5. Any products that should not be used together",
            "6. Seasonal adjustments if applicable",
            "7. Expected timeline for seeing results"
        ])

        query = " ".join(query_parts)

        try:
            # Create query engine optimized for routine advice
            query_engine = self.create_query_engine(
                similarity_top_k=10,
                similarity_threshold=0.65
            )

            # Execute query
            response = query_engine.query(query)

            # Structure response
            result = {
                'products': products,
                'user_profile': user_profile,
                'routine_recommendation': str(response),
                'sources': self._extract_sources(response),
                'confidence': self._calculate_confidence(response)
            }

            logger.info(f"Generated routine optimization for {len(products)} products")
            return result

        except Exception as e:
            logger.error(f"Error generating routine optimization: {e}")
            raise

    def _extract_sources(self, response) -> List[Dict[str, str]]:
        """Extract source information from query response."""
        sources = []

        try:
            # LlamaIndex responses have source_nodes attribute
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_info = {
                        'content_preview': node.text[:200] + "..." if len(node.text) > 200 else node.text,
                        'score': getattr(node, 'score', 0),
                        'metadata': node.metadata or {}
                    }
                    sources.append(source_info)

        except Exception as e:
            logger.warning(f"Could not extract sources: {e}")

        return sources

    def _calculate_confidence(self, response) -> float:
        """Calculate confidence score based on response quality and sources."""
        try:
            # Simple confidence calculation based on:
            # 1. Number of relevant sources
            # 2. Average similarity scores
            # 3. Response length (more detailed = higher confidence)

            source_count = len(self._extract_sources(response))
            avg_score = 0

            if hasattr(response, 'source_nodes') and response.source_nodes:
                scores = [getattr(node, 'score', 0) for node in response.source_nodes]
                avg_score = sum(scores) / len(scores) if scores else 0

            response_length = len(str(response))

            # Normalize factors and combine
            source_factor = min(source_count / 5, 1.0)  # Cap at 5 sources
            score_factor = avg_score  # Already 0-1
            length_factor = min(response_length / 1000, 1.0)  # Cap at 1000 chars

            confidence = (source_factor * 0.4 + score_factor * 0.4 + length_factor * 0.2)
            return round(confidence, 2)

        except Exception as e:
            logger.warning(f"Could not calculate confidence: {e}")
            return 0.5  # Default moderate confidence

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        try:
            # Get document count from vector store
            if hasattr(self.vector_store, '_collection'):
                doc_count = self.vector_store._collection.count()
            else:
                doc_count = "Unknown"

            stats = {
                'document_count': doc_count,
                'vector_store_provider': self.config.vector_store.provider,
                'embedding_model': self.config.openai.embedding_model,
                'chunk_size': self.config.vector_store.chunk_size,
                'similarity_metric': self.config.vector_store.similarity_metric
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {'error': str(e)}

    def clear_index(self):
        """Clear all documents from the index. Use with caution!"""
        try:
            # Recreate the index
            storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            self.index = VectorStoreIndex([], storage_context=storage_context)

            logger.warning("Index cleared - all documents removed")

        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            raise


# Factory function for easy initialization
def create_rag_system(db_session: Session = None) -> BeautyRAGSystem:
    """Create and initialize a Beauty RAG System instance."""
    return BeautyRAGSystem(db_session=db_session)


# Example usage and testing functions
async def example_usage():
    """Example usage of the RAG system."""

    # Initialize RAG system
    rag = create_rag_system()

    # Add some sample knowledge (in practice, load from real sources)
    sample_docs = [
        {
            'content': """
            Retinol and Vitamin C Interaction:
            Retinol (Vitamin A) and L-Ascorbic Acid (Vitamin C) can potentially 
            destabilize each other when used simultaneously. Retinol is most stable 
            at pH 5.5-6.0, while L-Ascorbic Acid requires pH 3.5 or lower for stability.
            Recommendation: Use Vitamin C in morning routine, Retinol in evening routine.
            """,
            'metadata': {
                'title': 'Retinol-Vitamin C Interaction Study',
                'document_type': 'research_summary',
                'credibility_score': 8
            }
        },
        {
            'content': """
            Niacinamide Compatibility:
            Niacinamide (Vitamin B3) is generally well-tolerated with most ingredients.
            Compatible with: Hyaluronic Acid, Peptides, Ceramides, most moisturizing agents.
            pH range: 5.0-7.0, making it versatile for various formulations.
            Can be used morning and evening without photosensitivity concerns.
            """,
            'metadata': {
                'title': 'Niacinamide Compatibility Guide',
                'document_type': 'ingredient_guide',
                'credibility_score': 9
            }
        }
    ]

    # Add documents to knowledge base
    for doc_data in sample_docs:
        rag.add_document(doc_data['content'], doc_data['metadata'])

    # Example: Query ingredient interactions
    ingredients = ['Retinol', 'Niacinamide', 'Hyaluronic Acid']
    user_context = {
        'skin_type': 'combination',
        'skin_concerns': ['anti-aging', 'hydration']
    }

    interaction_result = rag.query_ingredients_interaction(ingredients, user_context)
    print("Ingredient Interaction Analysis:")
    print(interaction_result['analysis'])
    print(f"Confidence: {interaction_result['confidence']}")

    # Example: Query routine optimization
    products = [
        {'name': 'Vitamin C Serum', 'ingredients': ['L-Ascorbic Acid', 'Hyaluronic Acid']},
        {'name': 'Retinol Treatment', 'ingredients': ['Retinol', 'Squalane']},
        {'name': 'Niacinamide Serum', 'ingredients': ['Niacinamide', 'Zinc PCA']}
    ]

    user_profile = {
        'skin_type': 'combination',
        'skin_concerns': ['anti-aging', 'pore_minimizing'],
        'routine_complexity': 'moderate'
    }

    routine_result = rag.query_routine_optimization(products, user_profile)
    print("\nRoutine Optimization:")
    print(routine_result['routine_recommendation'])

    # Get index statistics
    stats = rag.get_index_stats()
    print(f"\nIndex Stats: {stats}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
