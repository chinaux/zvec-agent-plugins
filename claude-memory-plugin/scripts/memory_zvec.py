#!/usr/bin/env python3
"""zvec memory bridge for Claude Code skills.

This script provides skill-based memory operations:
- store: explicitly store important information
- forget: delete specific memories
- recall: search and retrieve memories
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

try:
    import zvec
    HAS_ZVEC = True
except ImportError:
    HAS_ZVEC = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def get_global_config_path() -> Path:
    """Get the global config file path (~/.zvec/zvec.conf)."""
    return Path.home() / ".zvec" / "zvec.conf"


def load_global_config() -> Dict[str, Any]:
    """Load global configuration from ~/.zvec/zvec.conf."""
    config_path = get_global_config_path()
    if not config_path.exists():
        # Return default config if file doesn't exist
        return {
            "dbPath": str(Path.home() / ".zvec" / "memory.zvec"),
            "embedding": {
                "provider": "openai",
                "model": "text-embedding-3-small",
                "apiKey": os.environ.get("OPENAI_API_KEY", ""),
                "apiUrl": "https://api.openai.com/v1/embeddings"
            },
            "autoCapture": True,
            "autoRecall": True,
            "captureMaxChars": 500
        }
    return _load_json(config_path)


def get_zvec_path() -> str:
    """Get the global zvec database path from config."""
    config = load_global_config()
    db_path = config.get("dbPath", str(Path.home() / ".zvec" / "memory.zvec"))
    # Expand ~ to home directory
    if db_path.startswith("~"):
        db_path = os.path.expanduser(db_path)
    return db_path


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_embedding_dimension(model: str) -> int:
    """Get embedding dimension for a specific model."""
    # Common embedding models and their dimensions
    model_dimensions = {
        # OpenAI models
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
        # Alibaba/DashScope models
        "text-embedding-v4": 1024,
        "text-embedding-v3": 1024,
        "text-embedding-v2": 1536,
        "text-embedding-v1": 1536,
        # Sentence Transformers (common sizes)
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
    }
    
    # Try to match the model name
    for model_pattern, dimension in model_dimensions.items():
        if model_pattern in model.lower():
            return dimension
    
    # Default to 1536 if unknown
    print(f"   Warning: Unknown model '{model}', using default dimension 1536")
    return 1536


def get_embedding_config() -> Dict[str, Any]:
    """Load embedding configuration from global config."""
    config = load_global_config()
    embedding_config = config.get("embedding", {})
    # Set default API URL if not specified
    if "apiUrl" not in embedding_config:
        embedding_config["apiUrl"] = "https://api.openai.com/v1/embeddings"
    return embedding_config


def generate_embedding(text: str, config: Dict[str, Any]) -> List[float]:
    """Generate embedding using OpenAI API."""
    provider = config.get("provider", "openai")
    model = config.get("model", "text-embedding-3-small")
    api_key = config.get("apiKey", "")
    api_url = config.get("apiUrl", "https://api.openai.com/v1/embeddings")

    if not api_key:
        raise ValueError("API key not configured")

    if not HAS_OPENAI:
        raise ImportError("OpenAI Python package not installed. Install with: pip install openai")

    try:
        # Initialize OpenAI client (works for OpenAI-compatible APIs)
        # For custom API URLs, set base_url to the base endpoint (without /embeddings)
        base_url = api_url
        if api_url == "https://api.openai.com/v1/embeddings":
            base_url = None  # Use default

        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        #print(f"   Generating embedding with model: {model}", file=sys.stderr)
        #print(f"   API URL: {api_url}", file=sys.stderr)

        # Call OpenAI Embedding API
        response = client.embeddings.create(
            input=[text],  # Use list format for better compatibility
            model=model
        )

        #print(f"   OpenAI API response.usage: {response.usage}", file=sys.stderr)

        # Extract embedding from response
        embedding = response.data[0].embedding
        return embedding

    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")


def initialize_session() -> Dict[str, Any]:
    """Initialize zvec memory collection.
    
    Creates the db directory and prepares for memory operations.
    """
    if not HAS_ZVEC:
        return {
            "ok": False,
            "status_line": "[memory-zvec] ERROR: zvec Python package not installed",
            "additional_context": "Install with: pip install zvec"
        }
    
    # Get global database path
    zvec_path = get_zvec_path()
    
    # Convert to Path object for directory operations
    zvec_dir = Path(zvec_path)
    
    if not zvec_dir.exists():

        if not zvec_dir.parent.exists():
            zvec_dir.parent.mkdir(parents=True, exist_ok=True)

        embedding_config = get_embedding_config()
        model = embedding_config.get("model", "text-embedding-3-small")
        embedding_dim = get_embedding_dimension(model)

        # Define schema
        schema = zvec.CollectionSchema(
            name="memory",
            fields=[
                zvec.FieldSchema("text", zvec.DataType.STRING),
                zvec.FieldSchema("category", zvec.DataType.STRING),
                zvec.FieldSchema("source", zvec.DataType.STRING),
                zvec.FieldSchema("timestamp", zvec.DataType.STRING),
            ],
            vectors=zvec.VectorSchema("embedding", zvec.DataType.VECTOR_FP32, embedding_dim)
        )

        try:
            collection = zvec.create_and_open(path=zvec_path, schema=schema)
        except Exception as e:
            return {
                "ok": False,
                "status_line": "[memory-zvec] ERROR: Failed to create and open collection",
                "additional_context": str(e)
            }
    else:
        pass

    return {
        "ok": True,
        "status_line": f"[memory-zvec] Using global memory database",
        "additional_context": f"Memory database at {zvec_path}"
    }


def commit_session() -> Dict[str, Any]:
    """Commit session by creating collection if needed and optimizing it.
    
    - Creates the memory collection if it doesn't exist
    - Calls optimize() on the collection for better performance
    """
    if not HAS_ZVEC:
        return {
            "status_line": "[memory-zvec] ERROR: zvec not available"
        }
    
    try:
        # Get the global database path
        zvec_path = get_zvec_path()

        # Open or create collection
        try:
            collection = zvec.open(path=zvec_path)
        except Exception as e:
            return {"ok": False, "status_line": "[memory-zvec] Memory database not found"}
  
        # Optimize the collection for better query performance
        try:
            collection.optimize()
            doc_count = collection.stats.doc_count
            return {
                "status_line": f"[memory-zvec] Session committed and optimized ({doc_count} memories in database)"
            }
        except Exception as e:
            # Optimization is optional, don't fail if it doesn't work
            print(f"Warning: Collection optimization failed: {e}", file=sys.stderr)
            doc_count = collection.stats.doc_count
            return {
                "status_line": f"[memory-zvec] Session committed ({doc_count} memories in database)"
            }
        
    except Exception as e:
        return {
            "status_line": f"[memory-zvec] Commit failed: {str(e)}"
        }


def store_memory(text: str, category: str = "general") -> Dict[str, Any]:
    """Store a specific memory in the global database.
    
    Allows explicit storage of important information provided by the user.
    """
    if not HAS_ZVEC:
        return {"ok": False, "status_line": "[memory-zvec] zvec not available"}
    
    try:
        # Get the global database path
        zvec_path = get_zvec_path()
        
        # Load embedding configuration
        embedding_config = get_embedding_config()
        model = embedding_config.get("model", "text-embedding-3-small")
     
        # Open or create collection
        try:
            collection = zvec.open(path=zvec_path)
        except Exception as e:
            return {"ok": False, "status_line": "[memory-zvec] Memory database not found"}
        
        # Generate embedding
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        # Get embedding dimension for fallback
        embedding_dim = get_embedding_dimension(model)

        try:
            embedding = generate_embedding(text, embedding_config)
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}", file=sys.stderr)
            print(f"Warning: Failed to generate embedding: {e}", file=sys.stderr)
            embedding = [0.0] * embedding_dim
        
        # Create document ID
        doc_id = f"m_{uuid.uuid4().hex[:12]}"
        
        # Insert memory
        doc = zvec.Doc(
            id=doc_id,
            fields={"text": text, "category": category, "source": "manual", "timestamp": timestamp},
            vectors={"embedding": embedding}
        )
        collection.insert([doc])
        
        return {
            "ok": True,
            "status_line": f"[memory-zvec] Memory stored successfully (ID: {doc_id})",
            "memory_id": doc_id,
            "category": category
        }
        
    except Exception as e:
        return {
            "ok": False,
            "status_line": f"[memory-zvec] Storage failed: {str(e)}"
        }


def forget_memory(memory_id: str) -> Dict[str, Any]:
    """Delete a specific memory by ID.
    
    Allows users to remove unwanted or outdated memories.
    """
    if not HAS_ZVEC:
        return {"ok": False, "status_line": "[memory-zvec] zvec not available"}
    
    try:
        # Get the global database path
        zvec_path = get_zvec_path()
        
        # Open collection
        try:
            collection = zvec.open(path=zvec_path)
        except Exception as e:
            return {"ok": False, "status_line": "[memory-zvec] Memory database not found"}
        
        # Delete the memory
        try:
            collection.delete([memory_id])
            return {
                "ok": True,
                "status_line": f"[memory-zvec] Memory deleted successfully (ID: {memory_id})",
                "deleted_id": memory_id
            }
        except Exception as e:
            return {
                "ok": False,
                "status_line": f"[memory-zvec] Deletion failed: {str(e)}"
            }
        
    except Exception as e:
        return {
            "ok": False,
            "status_line": f"[memory-zvec] Deletion failed: {str(e)}"
        }


def recall_memories(query: str, top_k: int, task_id: str = None) -> Dict[str, Any]:
    """Search and recall memories from global zvec database.
    
    Searches across ALL sessions for long-term memory retrieval.
    """
    try:
        # Get the global database path
        zvec_path = get_zvec_path()

        # Open collection
        try:
            collection = zvec.open(path=zvec_path)
        except Exception as e:
            return {"memories": [], "error": "No memory database found"}

        # Load embedding config and generate query vector
        embedding_config = get_embedding_config()

        try:
            query_vector = generate_embedding(query, embedding_config)
        except Exception as e:
            print(f"Warning: Failed to generate query embedding: {e}", file=sys.stderr)
            # Fallback: get dimension and use zeros
            model = embedding_config.get("model", "text-embedding-3-small")
            embedding_dim = get_embedding_dimension(model)
            query_vector = [0.0] * embedding_dim

        try:
            results = collection.query(
                zvec.VectorQuery("embedding", vector=query_vector),
                topk=top_k
            )

            memories = [
                {
                    "id": result.id,
                    "text": result.fields.get("text", ""),
                    "category": result.fields.get("category", "general"),
                    "source": result.fields.get("source", "unknown"),
                    "timestamp": result.fields.get("timestamp", ""),
                    "score": result.score
                }
                for result in results
            ]
        except Exception as e:
            print(f"Query error: {e}", file=sys.stderr)
            memories = []

        return {"memories": memories, "task_id": task_id}

    except Exception as e:
        return {"memories": [], "error": str(e), "task_id": task_id, "status": ""}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="zvec memory bridge")
    # uses global config from ~/.zvec/zvec.conf
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # session-start
    subparsers.add_parser("session-start", help="Initialize session")

    # session-end
    subparsers.add_parser("session-end", help="Commit session")
    
    # recall
    recall_parser = subparsers.add_parser("recall", help="Recall memories")
    recall_parser.add_argument("--query", required=True, help="Search query")
    recall_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    recall_parser.add_argument("--task-id", dest="task_id", default=None, help="Task ID for tracking")
    
    # store
    store_parser = subparsers.add_parser("store", help="Store a memory")
    store_parser.add_argument("--text", required=True, help="Memory text to store")
    store_parser.add_argument("--category", default="general", help="Memory category")
    store_parser.add_argument("--task-id", dest="task_id", default=None, help="Task ID for tracking")
    
    # forget
    forget_parser = subparsers.add_parser("forget", help="Forget/delete a memory")
    forget_parser.add_argument("--memory-id", required=True, help="Memory ID to delete")
    forget_parser.add_argument("--task-id", dest="task_id", default=None, help="Task ID for tracking")
    
    args = parser.parse_args()
    
    if args.command == "session-start":
        result = initialize_session()
        print(json.dumps(result))
        
    elif args.command == "session-end":
        result = commit_session()
        print(json.dumps(result))
        
    elif args.command == "recall":
        result = recall_memories(args.query, args.top_k, getattr(args, 'task_id', None))
        print(json.dumps(result))
        
    elif args.command == "store":
        result = store_memory(args.text, args.category)
        result['task_id'] = getattr(args, 'task_id', None)
        print(json.dumps(result))
        
    elif args.command == "forget":
        result = forget_memory(args.memory_id)
        result['task_id'] = getattr(args, 'task_id', None)
        print(json.dumps(result))


if __name__ == "__main__":
    main()