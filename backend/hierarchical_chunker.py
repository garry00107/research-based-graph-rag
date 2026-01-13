"""
Hierarchical Document Chunker for Sheet RAG Architecture

Creates aligned chunks at multiple granularity levels:
- Sentence (fine-grained)
- Paragraph (contextual)
- Section (topical)
- Document Summary (abstract)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
import re
import hashlib


@dataclass
class ChunkNode:
    """Represents a chunk at any granularity level"""
    id: str
    text: str
    level: str  # "sentence", "paragraph", "section", "summary"
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_document(self) -> Document:
        """Convert to LlamaIndex Document for embedding"""
        return Document(
            text=self.text,
            metadata={
                "chunk_id": self.id,
                "level": self.level,
                "parent_id": self.parent_id,
                **self.metadata
            }
        )


class HierarchicalChunker:
    """
    Creates aligned chunks at sentence, paragraph, section, and document levels.
    Maintains parent-child relationships for cross-layer validation.
    """
    
    # Default configuration for each layer
    LAYER_CONFIG = {
        "sentence": {"target_size": 200, "overlap": 0},
        "paragraph": {"target_size": 800, "overlap": 100},
        "section": {"target_size": 2000, "overlap": 200},
        "summary": {"target_size": 4000, "overlap": 0}  # Full document summary chunks
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize chunker with optional custom config.
        
        Args:
            config: Override default layer configurations
        """
        self.config = {**self.LAYER_CONFIG, **(config or {})}
        
        # Initialize sentence splitter for fine-grained splitting
        self.sentence_splitter = SentenceSplitter(
            chunk_size=self.config["sentence"]["target_size"],
            chunk_overlap=self.config["sentence"]["overlap"]
        )
    
    def _generate_id(self, text: str, level: str, index: int) -> str:
        """Generate unique ID for a chunk"""
        hash_input = f"{level}:{index}:{text[:50]}"
        return f"{level}_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns"""
        # Handle common abbreviations to avoid false splits
        text = re.sub(r'(Mr|Mrs|Dr|Prof|Sr|Jr|vs|etc|e\.g|i\.e)\.\s', r'\1<DOT> ', text)
        
        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Restore abbreviation dots
        sentences = [s.replace('<DOT>', '.') for s in sentences]
        
        # Filter empty sentences and strip whitespace
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""
        # Split on double newlines or multiple whitespace lines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter and clean
        return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 20]
    
    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Split text into sections based on common academic paper patterns.
        Returns list of dicts with 'title' and 'content' keys.
        """
        # Common section header patterns in academic papers
        section_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^(\d+\.?\s+[A-Z][^.]+)$',  # Numbered sections (1. Introduction)
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headers
            r'^(Abstract|Introduction|Background|Related Work|Methodology|Methods|'
            r'Experiments|Results|Discussion|Conclusion|References|Acknowledgments)s?:?\s*$',
        ]
        
        combined_pattern = '|'.join(f'({p})' for p in section_patterns)
        
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        
        for line in text.split('\n'):
            is_header = False
            for pattern in section_patterns:
                match = re.match(pattern, line.strip(), re.IGNORECASE | re.MULTILINE)
                if match:
                    # Save previous section if it has content
                    if current_section["content"].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        "title": match.group(1) if match.group(1) else line.strip(),
                        "content": ""
                    }
                    is_header = True
                    break
            
            if not is_header:
                current_section["content"] += line + "\n"
        
        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        # If no sections found, treat entire text as one section
        if not sections:
            sections = [{"title": "Content", "content": text}]
        
        return sections
    
    def _create_document_summary_chunks(self, text: str, doc_metadata: Dict) -> List[ChunkNode]:
        """
        Create document-level summary chunks.
        For very long documents, we create overlapping large chunks.
        """
        chunks = []
        target_size = self.config["summary"]["target_size"]
        
        if len(text) <= target_size:
            # Document is small enough for single summary chunk
            chunk = ChunkNode(
                id=self._generate_id(text, "summary", 0),
                text=text,
                level="summary",
                metadata={**doc_metadata, "chunk_index": 0}
            )
            chunks.append(chunk)
        else:
            # Split into overlapping summary chunks
            words = text.split()
            chunk_words = target_size // 5  # Approximate words per chunk
            overlap_words = chunk_words // 4
            
            start = 0
            index = 0
            while start < len(words):
                end = min(start + chunk_words, len(words))
                chunk_text = ' '.join(words[start:end])
                
                chunk = ChunkNode(
                    id=self._generate_id(chunk_text, "summary", index),
                    text=chunk_text,
                    level="summary",
                    metadata={**doc_metadata, "chunk_index": index}
                )
                chunks.append(chunk)
                
                start = end - overlap_words if end < len(words) else len(words)
                index += 1
        
        return chunks
    
    def chunk_document(self, document: Document) -> Dict[str, List[ChunkNode]]:
        """
        Chunk a document at all granularity levels.
        
        Args:
            document: LlamaIndex Document to chunk
            
        Returns:
            Dictionary with keys for each level containing list of ChunkNodes
        """
        text = document.text
        doc_metadata = document.metadata or {}
        
        result = {
            "sentences": [],
            "paragraphs": [],
            "sections": [],
            "summaries": []
        }
        
        # Level 4: Document summaries (highest level)
        summary_chunks = self._create_document_summary_chunks(text, doc_metadata)
        result["summaries"] = summary_chunks
        
        # Level 3: Sections
        sections_data = self._split_into_sections(text)
        section_chunks = []
        for idx, section in enumerate(sections_data):
            section_text = f"{section['title']}\n\n{section['content']}"
            chunk = ChunkNode(
                id=self._generate_id(section_text, "section", idx),
                text=section_text,
                level="section",
                parent_id=summary_chunks[0].id if summary_chunks else None,
                metadata={
                    **doc_metadata,
                    "section_title": section["title"],
                    "section_index": idx
                }
            )
            section_chunks.append(chunk)
        result["sections"] = section_chunks
        
        # Level 2: Paragraphs
        paragraph_chunks = []
        para_idx = 0
        for section_chunk in section_chunks:
            paragraphs = self._split_into_paragraphs(section_chunk.text)
            for para in paragraphs:
                if len(para) < 30:  # Skip very short paragraphs
                    continue
                chunk = ChunkNode(
                    id=self._generate_id(para, "paragraph", para_idx),
                    text=para,
                    level="paragraph",
                    parent_id=section_chunk.id,
                    metadata={
                        **doc_metadata,
                        "paragraph_index": para_idx,
                        "parent_section": section_chunk.metadata.get("section_title", "")
                    }
                )
                paragraph_chunks.append(chunk)
                section_chunk.children_ids.append(chunk.id)
                para_idx += 1
        result["paragraphs"] = paragraph_chunks
        
        # Level 1: Sentences (finest granularity)
        sentence_chunks = []
        sent_idx = 0
        for para_chunk in paragraph_chunks:
            sentences = self._split_into_sentences(para_chunk.text)
            for sent in sentences:
                if len(sent) < 15:  # Skip very short sentences
                    continue
                chunk = ChunkNode(
                    id=self._generate_id(sent, "sentence", sent_idx),
                    text=sent,
                    level="sentence",
                    parent_id=para_chunk.id,
                    metadata={
                        **doc_metadata,
                        "sentence_index": sent_idx,
                        "parent_paragraph": para_chunk.id
                    }
                )
                sentence_chunks.append(chunk)
                para_chunk.children_ids.append(chunk.id)
                sent_idx += 1
        result["sentences"] = sentence_chunks
        
        return result
    
    def chunk_documents(self, documents: List[Document]) -> Dict[str, List[ChunkNode]]:
        """
        Chunk multiple documents at all granularity levels.
        
        Args:
            documents: List of LlamaIndex Documents
            
        Returns:
            Combined dictionary with all chunks from all documents
        """
        combined = {
            "sentences": [],
            "paragraphs": [],
            "sections": [],
            "summaries": []
        }
        
        for doc in documents:
            doc_chunks = self.chunk_document(doc)
            for level in combined:
                combined[level].extend(doc_chunks[level])
        
        return combined
    
    def get_stats(self, chunks: Dict[str, List[ChunkNode]]) -> Dict[str, Any]:
        """Get statistics about chunked documents"""
        stats = {}
        for level, chunk_list in chunks.items():
            if chunk_list:
                texts = [c.text for c in chunk_list]
                stats[level] = {
                    "count": len(chunk_list),
                    "avg_length": sum(len(t) for t in texts) // len(texts),
                    "min_length": min(len(t) for t in texts),
                    "max_length": max(len(t) for t in texts)
                }
            else:
                stats[level] = {"count": 0}
        return stats


# Convenience function for simple usage
def create_hierarchical_chunks(documents: List[Document], config: Optional[Dict] = None) -> Dict[str, List[Document]]:
    """
    Convenience function to chunk documents and convert to LlamaIndex Documents.
    
    Returns:
        Dictionary mapping level names to lists of Documents ready for embedding
    """
    chunker = HierarchicalChunker(config)
    chunks = chunker.chunk_documents(documents)
    
    return {
        level: [chunk.to_document() for chunk in chunk_list]
        for level, chunk_list in chunks.items()
    }
