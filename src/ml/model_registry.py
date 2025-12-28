"""
JLAW ML Model Registry
======================

Centralized registry of all ML models used in JLAW forensic analysis.
Manages model metadata, caching, versioning, and validation.
"""

from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import hashlib


@dataclass
class ModelInfo:
    """Information about an ML model."""
    name: str
    model_id: str  # HuggingFace model ID or local path
    version: str
    size_mb: int
    sha256_hash: Optional[str]
    required_for: List[str]  # Which nodes require this model
    description: str = ""


class ModelRegistry:
    """
    Registry of all ML models used in JLAW.
    
    This class provides a centralized inventory of ML models with their
    metadata, cache locations, and validation capabilities.
    """
    
    # Model inventory
    MODELS: Dict[str, ModelInfo] = {
        "deberta-v3-base": ModelInfo(
            name="deberta-v3-base",
            model_id="microsoft/deberta-v3-base",
            version="1.0",
            size_mb=440,
            sha256_hash=None,  # Computed on download
            required_for=["Node03", "Node12"],
            description="DeBERTa v3 base model for contradiction detection"
        ),
        "finbert": ModelInfo(
            name="finbert",
            model_id="ProsusAI/finbert",
            version="1.0",
            size_mb=440,
            sha256_hash=None,
            required_for=["Node05", "Node09"],
            description="FinBERT model for financial text analysis"
        ),
        "distilbert-base-uncased": ModelInfo(
            name="distilbert-base-uncased",
            model_id="distilbert-base-uncased",
            version="1.0",
            size_mb=250,
            sha256_hash=None,
            required_for=["Node08"],
            description="DistilBERT for text classification"
        ),
    }
    
    @classmethod
    def get_cache_dir(cls) -> Path:
        """
        Get model cache directory.
        
        Returns:
            Path to cache directory
        """
        cache_dir = Path.home() / ".cache" / "jlaw" / "models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    @classmethod
    def is_model_cached(cls, model_name: str) -> bool:
        """
        Check if model is already cached locally.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if model is cached, False otherwise
        """
        model_info = cls.MODELS.get(model_name)
        if not model_info:
            return False
        
        # Check if model directory exists
        cache_path = cls.get_cache_dir() / model_name
        
        # For HuggingFace models, check for config.json
        if cache_path.exists():
            config_file = cache_path / "config.json"
            if config_file.exists():
                return True
            # Also check pytorch_model.bin or model.safetensors
            if (cache_path / "pytorch_model.bin").exists() or \
               (cache_path / "model.safetensors").exists():
                return True
        
        return False
    
    @classmethod
    def get_required_models_for_nodes(cls, node_list: List[str]) -> List[ModelInfo]:
        """
        Get list of models required for specified nodes.
        
        Args:
            node_list: List of node names (e.g., ["Node03", "Node12"])
            
        Returns:
            List of ModelInfo objects for required models
        """
        required = set()
        for model_info in cls.MODELS.values():
            if any(node in model_info.required_for for node in node_list):
                required.add(model_info)
        return list(required)
    
    @classmethod
    def get_model_path(cls, model_name: str) -> Optional[Path]:
        """
        Get local path to cached model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path to model directory, or None if not cached
        """
        if not cls.is_model_cached(model_name):
            return None
        
        return cls.get_cache_dir() / model_name
    
    @classmethod
    def get_total_size_mb(cls) -> int:
        """
        Get total size of all models in MB.
        
        Returns:
            Total size in megabytes
        """
        return sum(model.size_mb for model in cls.MODELS.values())
    
    @classmethod
    def get_cached_size_mb(cls) -> int:
        """
        Get total size of cached models in MB.
        
        Returns:
            Cached size in megabytes
        """
        total = 0
        for model_name, model_info in cls.MODELS.items():
            if cls.is_model_cached(model_name):
                total += model_info.size_mb
        return total
    
    @classmethod
    def validate_model_integrity(cls, model_name: str) -> bool:
        """
        Validate integrity of cached model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if model is valid, False otherwise
        """
        if not cls.is_model_cached(model_name):
            return False
        
        model_info = cls.MODELS.get(model_name)
        if not model_info:
            return False
        
        # Basic validation: check if key files exist
        cache_path = cls.get_cache_dir() / model_name
        
        # Check for config.json
        if not (cache_path / "config.json").exists():
            return False
        
        # Check for model weights
        has_weights = (
            (cache_path / "pytorch_model.bin").exists() or
            (cache_path / "model.safetensors").exists() or
            (cache_path / "tf_model.h5").exists()
        )
        
        return has_weights
    
    @classmethod
    def list_all_models(cls) -> List[Dict[str, any]]:
        """
        List all registered models with their status.
        
        Returns:
            List of model information dictionaries
        """
        models = []
        for model_name, model_info in cls.MODELS.items():
            models.append({
                'name': model_name,
                'model_id': model_info.model_id,
                'size_mb': model_info.size_mb,
                'cached': cls.is_model_cached(model_name),
                'required_for': model_info.required_for,
                'description': model_info.description
            })
        return models
