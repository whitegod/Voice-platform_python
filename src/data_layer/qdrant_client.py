"""
Qdrant Vector Database Client
Semantic search and Retrieval-Augmented Generation (RAG)
"""

import logging
import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient as QdrantSDK
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import uuid

logger = logging.getLogger(__name__)


class QdrantVectorDB:
    """
    Qdrant client for vector similarity search and RAG.
    Stores and retrieves contextual knowledge.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "vaas_embeddings",
        vector_size: int = 384,  # Default for all-MiniLM-L6-v2
        distance: Optional[Distance] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: API key for authentication
            collection_name: Default collection name
            vector_size: Dimension of vectors
            distance: Distance metric
            embedding_model: Sentence transformer model
        """
        self.host = host
        self.port = port
        self.api_key = api_key
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Use environment variable for distance metric
        distance_str = os.getenv("QDRANT_DISTANCE_METRIC", "cosine").lower()
        distance_mapping = {
            "cosine": Distance.COSINE,
            "dot": Distance.DOT,
            "euclid": Distance.EUCLID,
            "euclidean": Distance.EUCLID  # Alias for compatibility
        }
        self.distance = distance if distance is not None else distance_mapping.get(distance_str, Distance.COSINE)
        
        self.client = None
        self.embedder = None
        self.embedding_model = embedding_model or os.getenv("QDRANT_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        logger.info(f"Initializing Qdrant client: {host}:{port}")
        self._connect()
        self._load_embedder()

    def _connect(self):
        """Establish connection to Qdrant"""
        try:
            self.client = QdrantSDK(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                timeout=30
            )
            logger.info("Qdrant connection established")
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def _load_embedder(self):
        """Load sentence transformer for embeddings"""
        try:
            self.embedder = SentenceTransformer(self.embedding_model)
            logger.info(f"Loaded embedding model: {self.embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    async def create_collection(
        self,
        collection_name: Optional[str] = None,
        vector_size: Optional[int] = None
    ) -> bool:
        """
        Create a new collection.

        Args:
            collection_name: Collection name (uses default if None)
            vector_size: Vector dimension (uses default if None)

        Returns:
            True if successful
        """
        try:
            collection_name = collection_name or self.collection_name
            vector_size = vector_size or self.vector_size
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection '{collection_name}' already exists")
                return True

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=self.distance
                )
            )
            
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            embedding = self.embedder.encode(text, convert_to_tensor=False)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = self.embedder.encode(texts, convert_to_tensor=False)
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise

    async def insert(
        self,
        texts: List[str],
        metadata: Optional[List[Dict]] = None,
        collection_name: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Insert texts with embeddings into collection.

        Args:
            texts: List of texts to insert
            metadata: List of metadata dicts
            collection_name: Target collection
            tenant_id: Tenant identifier for isolation

        Returns:
            True if successful
        """
        try:
            collection_name = collection_name or self.collection_name
            metadata = metadata or [{}] * len(texts)
            
            if len(texts) != len(metadata):
                raise ValueError("texts and metadata must have same length")

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} texts")
            embeddings = self.embed_batch(texts)

            # Create points
            points = []
            for i, (text, emb, meta) in enumerate(zip(texts, embeddings, metadata)):
                point_id = str(uuid.uuid4())
                
                # Add tenant_id to payload for isolation
                payload = {
                    "text": text,
                    **meta
                }
                if tenant_id:
                    payload["tenant_id"] = tenant_id

                points.append(
                    PointStruct(
                        id=point_id,
                        vector=emb,
                        payload=payload
                    )
                )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Inserted {len(points)} points into {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert vectors: {e}")
            return False

    async def search(
        self,
        query: str,
        limit: int = 5,
        collection_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        score_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts.

        Args:
            query: Query text
            limit: Maximum results to return
            collection_name: Target collection
            tenant_id: Filter by tenant
            score_threshold: Minimum similarity score

        Returns:
            List of matching results with scores
        """
        try:
            collection_name = collection_name or self.collection_name
            
            # Generate query embedding
            logger.info(f"Searching for: '{query[:100]}...'")
            query_vector = self.embed_text(query)

            # Build filter for tenant isolation
            search_filter = None
            if tenant_id:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="tenant_id",
                            match=MatchValue(value=tenant_id)
                        )
                    ]
                )

            # Search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["text", "tenant_id"]}
                })

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_collection(self, collection_name: Optional[str] = None) -> bool:
        """Delete a collection"""
        try:
            collection_name = collection_name or self.collection_name
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    async def get_collection_info(
        self,
        collection_name: Optional[str] = None
    ) -> Optional[Dict]:
        """Get collection information"""
        try:
            collection_name = collection_name or self.collection_name
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

    async def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            collections = self.client.get_collections()
            logger.info("Qdrant health check passed")
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

