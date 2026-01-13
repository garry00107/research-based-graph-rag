"""
RAG Evaluation Module

Compares standard RAG vs Sheet RAG to measure hallucination reduction.
Generates test queries and evaluates response quality.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import json
import time


@dataclass
class EvaluationResult:
    """Result of comparing Standard RAG vs Sheet RAG"""
    query: str
    standard_response: str
    sheet_response: str
    standard_sources: List[Dict]
    sheet_sources: List[Dict]
    sheet_validation: Dict
    standard_latency_ms: float
    sheet_latency_ms: float
    sheet_confidence: float
    notes: str = ""


class RAGEvaluator:
    """
    Evaluates and compares Standard RAG vs Sheet RAG.
    
    Focuses on:
    1. Hallucination detection (claims not in sources)
    2. Source coverage (how much of response is grounded)
    3. Cross-layer consistency (Sheet RAG specific)
    4. Response quality metrics
    """
    
    # Test queries designed to trigger potential hallucinations
    HALLUCINATION_TEST_QUERIES = [
        # Factual queries - should have definitive answers
        {
            "query": "What is the exact number of attention heads used in the Transformer model?",
            "type": "factual",
            "note": "Tests for specific numerical claims"
        },
        {
            "query": "List all the authors of the Attention is All You Need paper",
            "type": "factual",
            "note": "Tests for complete enumeration"
        },
        {
            "query": "What was the training time for the base Transformer model?",
            "type": "factual",
            "note": "Tests for specific metrics"
        },
        
        # Comparative queries - may encourage speculation
        {
            "query": "How does the Transformer compare to LSTM in terms of parallelization?",
            "type": "comparative",
            "note": "May include claims not in documents"
        },
        {
            "query": "What are the main differences between self-attention and cross-attention?",
            "type": "comparative",
            "note": "Requires precise technical knowledge"
        },
        
        # Out-of-scope queries - should admit uncertainty
        {
            "query": "What improvements did GPT-4 make over the original Transformer?",
            "type": "out_of_scope",
            "note": "Should admit if info not available"
        },
        {
            "query": "How many parameters does the largest Transformer model have?",
            "type": "out_of_scope",
            "note": "Tests for hallucinated numbers"
        },
        
        # Complex queries - multiple facts needed
        {
            "query": "Explain the complete architecture of the Transformer encoder stack",
            "type": "complex",
            "note": "Requires multiple accurate facts"
        },
        {
            "query": "What regularization techniques are used and why?",
            "type": "complex",
            "note": "Requires reasoning + facts"
        },
        
        # Edge case queries - ambiguous or tricky
        {
            "query": "What are the limitations of the attention mechanism?",
            "type": "edge_case",
            "note": "May include ungrounded claims"
        }
    ]
    
    def __init__(self, standard_rag, sheet_rag):
        """
        Initialize evaluator with both RAG engines.
        
        Args:
            standard_rag: RAGEngine instance
            sheet_rag: SheetRAGEngine instance
        """
        self.standard_rag = standard_rag
        self.sheet_rag = sheet_rag
        self.results: List[EvaluationResult] = []
    
    def run_query(self, query: str) -> EvaluationResult:
        """
        Run a single query on both engines and compare results.
        """
        # Query standard RAG
        start = time.time()
        std_response = self.standard_rag.query(query)
        std_latency = (time.time() - start) * 1000
        
        # Query Sheet RAG
        start = time.time()
        sheet_result = self.sheet_rag.query(query, use_cross_validation=True)
        sheet_latency = (time.time() - start) * 1000
        
        # Extract standard RAG sources
        std_sources = []
        if hasattr(std_response, 'source_nodes'):
            for node in std_response.source_nodes:
                std_sources.append({
                    "text": node.node.get_text()[:300],
                    "score": node.score
                })
        
        # Calculate Sheet RAG confidence
        validation = sheet_result.get("validation", {})
        avg_confidence = validation.get("avg_confidence", 0) if validation else 0
        
        result = EvaluationResult(
            query=query,
            standard_response=str(std_response),
            sheet_response=sheet_result["response"],
            standard_sources=std_sources,
            sheet_sources=sheet_result["sources"],
            sheet_validation=validation,
            standard_latency_ms=std_latency,
            sheet_latency_ms=sheet_latency,
            sheet_confidence=avg_confidence
        )
        
        self.results.append(result)
        return result
    
    def run_evaluation_suite(self, queries: List[Dict] = None) -> Dict[str, Any]:
        """
        Run complete evaluation suite on both engines.
        
        Args:
            queries: Optional custom queries, defaults to HALLUCINATION_TEST_QUERIES
            
        Returns:
            Complete evaluation report
        """
        if queries is None:
            queries = self.HALLUCINATION_TEST_QUERIES
        
        print(f"🔬 Running evaluation with {len(queries)} queries...")
        self.results = []
        
        for i, q in enumerate(queries):
            print(f"  [{i+1}/{len(queries)}] {q['query'][:50]}...")
            try:
                result = self.run_query(q["query"])
                result.notes = q.get("note", "")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate evaluation report from results"""
        if not self.results:
            return {"error": "No results to report"}
        
        # Calculate metrics
        total = len(self.results)
        
        # Latency comparison
        avg_std_latency = sum(r.standard_latency_ms for r in self.results) / total
        avg_sheet_latency = sum(r.sheet_latency_ms for r in self.results) / total
        
        # Confidence metrics (Sheet RAG only)
        confidences = [r.sheet_confidence for r in self.results if r.sheet_confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Source coverage
        avg_std_sources = sum(len(r.standard_sources) for r in self.results) / total
        avg_sheet_sources = sum(len(r.sheet_sources) for r in self.results) / total
        
        # Validation stats
        validation_stats = {
            "with_validation": sum(1 for r in self.results if r.sheet_validation),
            "high_confidence": sum(1 for r in self.results if r.sheet_confidence >= 0.7),
            "low_confidence": sum(1 for r in self.results if 0 < r.sheet_confidence < 0.5)
        }
        
        report = {
            "summary": {
                "total_queries": total,
                "avg_standard_latency_ms": round(avg_std_latency, 2),
                "avg_sheet_latency_ms": round(avg_sheet_latency, 2),
                "latency_overhead_percent": round((avg_sheet_latency - avg_std_latency) / avg_std_latency * 100, 2) if avg_std_latency > 0 else 0,
                "avg_sheet_confidence": round(avg_confidence, 3),
                "avg_standard_sources": round(avg_std_sources, 2),
                "avg_sheet_sources": round(avg_sheet_sources, 2)
            },
            "validation_stats": validation_stats,
            "detailed_results": [
                {
                    "query": r.query,
                    "notes": r.notes,
                    "standard_response_preview": r.standard_response[:200] + "...",
                    "sheet_response_preview": r.sheet_response[:200] + "...",
                    "sheet_confidence": r.sheet_confidence,
                    "sheet_layer_coverage": r.sheet_validation.get("avg_layer_coverage", 0) if r.sheet_validation else 0
                }
                for r in self.results
            ]
        }
        
        return report
    
    def _check_grounding(self, response: str, sources: List[Dict]) -> Dict[str, Any]:
        """
        Check if response claims are grounded in sources.
        
        Simple heuristic: check for overlap between response and source text.
        """
        if not sources:
            return {"grounded": False, "coverage": 0}
        
        source_text = " ".join(s.get("text", "") for s in sources).lower()
        response_words = set(response.lower().split())
        source_words = set(source_text.split())
        
        if not response_words:
            return {"grounded": False, "coverage": 0}
        
        overlap = len(response_words & source_words)
        coverage = overlap / len(response_words)
        
        return {
            "grounded": coverage > 0.3,
            "coverage": round(coverage, 3)
        }
    
    def print_comparison(self, result: EvaluationResult):
        """Pretty print a single comparison result"""
        print("\n" + "="*80)
        print(f"📋 Query: {result.query}")
        print("="*80)
        
        print("\n🔹 Standard RAG Response:")
        print(f"   {result.standard_response[:300]}...")
        print(f"   📊 Latency: {result.standard_latency_ms:.0f}ms | Sources: {len(result.standard_sources)}")
        
        print("\n🔸 Sheet RAG Response:")
        print(f"   {result.sheet_response[:300]}...")
        print(f"   📊 Latency: {result.sheet_latency_ms:.0f}ms | Sources: {len(result.sheet_sources)}")
        print(f"   ✅ Confidence: {result.sheet_confidence:.2f}")
        
        if result.sheet_validation:
            val = result.sheet_validation
            print(f"   📈 Validated: {val.get('count', 0)} results across {val.get('avg_layer_coverage', 0):.1f} layers avg")
        
        print()


def run_evaluation(standard_rag, sheet_rag, custom_queries: List[str] = None) -> Dict:
    """
    Convenience function to run evaluation.
    
    Args:
        standard_rag: RAGEngine instance
        sheet_rag: SheetRAGEngine instance
        custom_queries: Optional list of custom query strings
        
    Returns:
        Evaluation report dict
    """
    evaluator = RAGEvaluator(standard_rag, sheet_rag)
    
    if custom_queries:
        queries = [{"query": q, "type": "custom"} for q in custom_queries]
        return evaluator.run_evaluation_suite(queries)
    else:
        return evaluator.run_evaluation_suite()
