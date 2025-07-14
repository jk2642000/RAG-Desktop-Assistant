import gc
import psutil
import os
from typing import Dict, Any, Optional
import weakref
from .logger import rag_logger

class MemoryManager:
    """Manages memory usage and model loading/unloading"""
    
    def __init__(self, max_memory_mb: int = 2048):
        self.max_memory_mb = max_memory_mb
        self.loaded_models = {}
        self.model_refs = weakref.WeakValueDictionary()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }
    
    def should_unload_models(self) -> bool:
        """Check if models should be unloaded due to memory pressure"""
        memory = self.get_memory_usage()
        return memory['rss_mb'] > self.max_memory_mb
    
    def register_model(self, model_name: str, model_obj: Any, size_mb: float = 0):
        """Register a model for memory tracking"""
        self.loaded_models[model_name] = {
            'object': model_obj,
            'size_mb': size_mb,
            'last_used': 0
        }
        self.model_refs[model_name] = model_obj
        
        memory = self.get_memory_usage()
        rag_logger.info(f"Model '{model_name}' loaded. Memory: {memory['rss_mb']:.1f}MB")
    
    def unload_model(self, model_name: str):
        """Unload a specific model"""
        if model_name in self.loaded_models:
            model_info = self.loaded_models[model_name]
            del model_info['object']
            del self.loaded_models[model_name]
            
            if model_name in self.model_refs:
                del self.model_refs[model_name]
            
            gc.collect()
            memory = self.get_memory_usage()
            rag_logger.info(f"Model '{model_name}' unloaded. Memory: {memory['rss_mb']:.1f}MB")
    
    def cleanup_unused_models(self):
        """Clean up models that are no longer referenced"""
        to_remove = []
        for model_name in self.loaded_models:
            if model_name not in self.model_refs:
                to_remove.append(model_name)
        
        for model_name in to_remove:
            self.unload_model(model_name)
    
    def force_cleanup(self):
        """Force cleanup of all models and memory"""
        model_names = list(self.loaded_models.keys())
        for model_name in model_names:
            self.unload_model(model_name)
        
        # Aggressive cleanup
        gc.collect()
        gc.collect()  # Call twice for better cleanup
        
        memory = self.get_memory_usage()
        rag_logger.info(f"Force cleanup completed. Memory: {memory['rss_mb']:.1f}MB")

# Global memory manager
memory_manager = MemoryManager()