"""
Cross-Layer Validator for Sheet RAG Architecture

Validates retrieved chunks across abstraction layers to reduce hallucinations.
Only returns results that have supporting evidence at multiple granularity levels.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass
class ScoredChunk:
    """A retrieved chunk with its relevance score"""
    chunk_id: str
    text: str
    level: str
    score: float
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ValidatedResult:
    """A cross-validated result with confidence metrics"""
    primary_chunk: ScoredChunk
    supporting_chunks: Dict[str, ScoredChunk]  # level -> supporting chunk
    confidence_score: float
    layer_coverage: int  # How many layers have supporting evidence
    validation_details: Dict[str, Any] = None


class CrossLayerValidator:
    """
    Validates retrieved chunks across abstraction layers.
    
    The core principle: A claim found at the sentence level is more trustworthy
    if similar content appears at paragraph, section, and document levels.
    """
    
    # Weight each layer's contribution to final confidence
    DEFAULT_LAYER_WEIGHTS = {
        "sentence": 0.30,
        "paragraph": 0.30,
        "section": 0.25,
        "summary": 0.15
    }
    
    # Minimum similarity to consider as "supporting"
    DEFAULT_SUPPORT_THRESHOLD = 0.5
    
    # Minimum layers that must agree for a result to be valid
    DEFAULT_MIN_LAYERS = 2
    
    def __init__(
        self,
        layer_weights: Optional[Dict[str, float]] = None,
        support_threshold: float = DEFAULT_SUPPORT_THRESHOLD,
        min_layers: int = DEFAULT_MIN_LAYERS
    ):
        """
        Initialize the cross-layer validator.
        
        Args:
            layer_weights: Custom weights for each layer's confidence contribution
            support_threshold: Minimum similarity score to consider as supporting evidence
            min_layers: Minimum number of layers that must agree
        """
        self.layer_weights = layer_weights or self.DEFAULT_LAYER_WEIGHTS
        self.support_threshold = support_threshold
        self.min_layers = min_layers
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        Compute text similarity using character-level Jaccard similarity.
        This is a fallback when embeddings aren't available.
        """
        # Normalize texts
        t1 = set(text1.lower().split())
        t2 = set(text2.lower().split())
        
        if not t1 or not t2:
            return 0.0
        
        intersection = len(t1 & t2)
        union = len(t1 | t2)
        
        return intersection / union if union > 0 else 0.0
    
    def _compute_embedding_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """Compute cosine similarity between two embeddings"""
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)
        
        dot_product = np.dot(e1, e2)
        norm1 = np.linalg.norm(e1)
        norm2 = np.linalg.norm(e2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _find_parent_chain(
        self, 
        chunk: ScoredChunk, 
        all_chunks: Dict[str, List[ScoredChunk]]
    ) -> Dict[str, ScoredChunk]:
        """
        Find the parent chain for a chunk using parent_id relationships.
        Returns dict mapping level -> parent chunk at that level.
        """
        parents = {}
        current_parent_id = chunk.parent_id
        
        # Level hierarchy (child -> parent)
        level_order = ["sentence", "paragraph", "section", "summary"]
        current_level_idx = level_order.index(chunk.level) if chunk.level in level_order else -1
        
        while current_parent_id and current_level_idx < len(level_order) - 1:
            current_level_idx += 1
            parent_level = level_order[current_level_idx]
            
            # Find parent in the next level up
            for candidate in all_chunks.get(parent_level, []):
                if candidate.chunk_id == current_parent_id:
                    parents[parent_level] = candidate
                    current_parent_id = candidate.parent_id
                    break
            else:
                # Parent not found in retrieved results, stop searching
                break
        
        return parents
    
    def _find_supporting_chunks(
        self,
        target_chunk: ScoredChunk,
        layer_results: Dict[str, List[ScoredChunk]],
        use_embeddings: bool = False,
        embeddings: Optional[Dict[str, List[float]]] = None
    ) -> Dict[str, Tuple[ScoredChunk, float]]:
        """
        Find chunks at other levels that support the target chunk.
        
        Returns:
            Dict mapping level -> (supporting_chunk, similarity_score)
        """
        supporting = {}
        
        for level, chunks in layer_results.items():
            if level == target_chunk.level:
                continue
            
            best_match = None
            best_similarity = 0.0
            
            for candidate in chunks:
                # First check: Is this a parent/child relationship?
                is_related = (
                    candidate.chunk_id == target_chunk.parent_id or
                    target_chunk.chunk_id in (candidate.metadata.get("children_ids", []))
                )
                
                # Compute similarity
                if use_embeddings and embeddings:
                    target_emb = embeddings.get(target_chunk.chunk_id)
                    candidate_emb = embeddings.get(candidate.chunk_id)
                    if target_emb and candidate_emb:
                        similarity = self._compute_embedding_similarity(target_emb, candidate_emb)
                    else:
                        similarity = self._compute_text_similarity(target_chunk.text, candidate.text)
                else:
                    similarity = self._compute_text_similarity(target_chunk.text, candidate.text)
                
                # Boost similarity for related chunks
                if is_related:
                    similarity = min(1.0, similarity + 0.2)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = candidate
            
            if best_match and best_similarity >= self.support_threshold:
                supporting[level] = (best_match, best_similarity)
        
        return supporting
    
    def _compute_confidence(
        self,
        primary_chunk: ScoredChunk,
        supporting_chunks: Dict[str, Tuple[ScoredChunk, float]]
    ) -> float:
        """
        Compute overall confidence score based on multi-layer support.
        
        Confidence is higher when:
        1. More layers have supporting evidence
        2. Supporting chunks have higher similarity scores
        3. Supporting chunks also had high retrieval scores
        """
        total_weight = 0.0
        weighted_score = 0.0
        
        # Primary chunk contribution
        primary_weight = self.layer_weights.get(primary_chunk.level, 0.25)
        weighted_score += primary_weight * primary_chunk.score
        total_weight += primary_weight
        
        # Supporting chunks contribution
        for level, (chunk, similarity) in supporting_chunks.items():
            level_weight = self.layer_weights.get(level, 0.25)
            # Combine retrieval score and similarity for this level's contribution
            level_score = (chunk.score * 0.6 + similarity * 0.4)
            weighted_score += level_weight * level_score
            total_weight += level_weight
        
        if total_weight == 0:
            return 0.0
        
        base_confidence = weighted_score / total_weight
        
        # Bonus for multi-layer coverage
        layer_coverage = 1 + len(supporting_chunks)
        coverage_bonus = min(0.2, (layer_coverage - 1) * 0.1)
        
        return min(1.0, base_confidence + coverage_bonus)
    
    def validate(
        self,
        layer_results: Dict[str, List[ScoredChunk]],
        primary_level: str = "sentence",
        embeddings: Optional[Dict[str, List[float]]] = None
    ) -> List[ValidatedResult]:
        """
        Cross-validate results from different layers.
        
        Args:
            layer_results: Dict mapping layer names to lists of ScoredChunks
            primary_level: Which layer to use as the primary source of results
            embeddings: Optional dict mapping chunk_id to embedding vectors
            
        Returns:
            List of ValidatedResults, sorted by confidence score (descending)
        """
        validated_results = []
        use_embeddings = embeddings is not None and len(embeddings) > 0
        
        # Get primary chunks to validate
        primary_chunks = layer_results.get(primary_level, [])
        
        for primary_chunk in primary_chunks:
            # Find supporting evidence at other layers
            supporting = self._find_supporting_chunks(
                primary_chunk,
                layer_results,
                use_embeddings=use_embeddings,
                embeddings=embeddings
            )
            
            layer_coverage = 1 + len(supporting)
            
            # Check if we have minimum required layer coverage
            if layer_coverage < self.min_layers:
                continue
            
            # Compute confidence score
            confidence = self._compute_confidence(primary_chunk, supporting)
            
            # Create validated result
            result = ValidatedResult(
                primary_chunk=primary_chunk,
                supporting_chunks={level: chunk for level, (chunk, _) in supporting.items()},
                confidence_score=confidence,
                layer_coverage=layer_coverage,
                validation_details={
                    "similarities": {level: sim for level, (_, sim) in supporting.items()},
                    "layer_weights_used": self.layer_weights,
                    "threshold": self.support_threshold
                }
            )
            validated_results.append(result)
        
        # Sort by confidence score (descending)
        validated_results.sort(key=lambda r: r.confidence_score, reverse=True)
        
        return validated_results
    
    def validate_bidirectional(
        self,
        layer_results: Dict[str, List[ScoredChunk]],
        embeddings: Optional[Dict[str, List[float]]] = None
    ) -> List[ValidatedResult]:
        """
        Validate from all layers bidirectionally for maximum coverage.
        
        This method:
        1. Validates from sentence level (fine-grained claims)
        2. Validates from section level (broad context)
        3. Merges and deduplicates results
        
        Returns:
            Combined list of ValidatedResults from all perspectives
        """
        all_results = []
        seen_chunk_ids = set()
        
        # Validate from each level
        for level in ["sentence", "paragraph", "section"]:
            if level in layer_results:
                level_results = self.validate(layer_results, primary_level=level, embeddings=embeddings)
                
                for result in level_results:
                    if result.primary_chunk.chunk_id not in seen_chunk_ids:
                        all_results.append(result)
                        seen_chunk_ids.add(result.primary_chunk.chunk_id)
        
        # Re-sort by confidence
        all_results.sort(key=lambda r: r.confidence_score, reverse=True)
        
        return all_results
    
    def get_validation_summary(self, results: List[ValidatedResult]) -> Dict[str, Any]:
        """Get summary statistics for validation results"""
        if not results:
            return {"count": 0}
        
        confidences = [r.confidence_score for r in results]
        coverages = [r.layer_coverage for r in results]
        
        return {
            "count": len(results),
            "avg_confidence": sum(confidences) / len(confidences),
            "max_confidence": max(confidences),
            "min_confidence": min(confidences),
            "avg_layer_coverage": sum(coverages) / len(coverages),
            "fully_validated": sum(1 for c in coverages if c >= 3),
            "by_primary_level": {
                level: sum(1 for r in results if r.primary_chunk.level == level)
                for level in ["sentence", "paragraph", "section", "summary"]
            }
        }


def create_scored_chunks_from_nodes(nodes: List[Any], level: str) -> List[ScoredChunk]:
    """
    Utility function to convert LlamaIndex nodes to ScoredChunks.
    
    Args:
        nodes: List of NodeWithScore from LlamaIndex query
        level: The layer level these nodes came from
        
    Returns:
        List of ScoredChunks
    """
    chunks = []
    for node in nodes:
        chunk = ScoredChunk(
            chunk_id=node.node.metadata.get("chunk_id", node.node.id_),
            text=node.node.get_text(),
            level=level,
            score=node.score if hasattr(node, 'score') else 0.5,
            parent_id=node.node.metadata.get("parent_id"),
            metadata=node.node.metadata
        )
        chunks.append(chunk)
    
    return chunks
