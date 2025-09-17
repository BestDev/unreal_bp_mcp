# Batch Operations Examples

This directory demonstrates efficient batch operations for the UnrealBlueprintMCP system, including bulk blueprint creation, mass property updates, and parallel processing patterns.

## 📋 Examples Overview

### 🏗️ Bulk Blueprint Creation
**File**: `bulk_blueprint_creator.py`
- Create multiple blueprints from templates
- Parallel processing for improved performance
- Progress tracking and error handling
- Support for different blueprint types

### 🔄 Mass Property Updates
**File**: `mass_property_updater.py`
- Update properties across multiple blueprints
- Batch property modifications
- Rollback capabilities for failed operations
- Property validation and type checking

### 📦 Asset Pipeline Automation
**File**: `asset_pipeline.py`
- Complete asset processing workflows
- Batch import and setup operations
- Automated asset organization
- Quality assurance checks

### 🎯 Performance Optimizer
**File**: `performance_optimizer.py`
- Batch performance optimization operations
- Memory usage analysis
- Asset optimization suggestions
- Performance benchmarking

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   cd examples/advanced/batch_operations
   pip install -r requirements.txt
   ```

2. **Configure Settings**
   ```python
   # Edit config if needed
   from ..config import DEFAULT_BATCH_SIZE, MCP_SERVER_URL
   ```

3. **Run Basic Example**
   ```bash
   python bulk_blueprint_creator.py --count 10 --type character
   ```

## 📊 Performance Considerations

- **Batch Size**: Optimal size is 5-10 operations per batch
- **Concurrent Connections**: Limit to 3-5 simultaneous connections
- **Memory Usage**: Monitor memory when processing large batches
- **Error Recovery**: Always implement rollback mechanisms

## 🔧 Configuration Options

```python
BATCH_SETTINGS = {
    "max_batch_size": 10,
    "max_concurrent": 5,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "progress_callback": True,
    "error_logging": True
}
```

## 📚 Usage Patterns

### Simple Batch Creation
```python
from bulk_blueprint_creator import BatchBlueprintCreator

creator = BatchBlueprintCreator()
results = await creator.create_batch([
    {"name": "Enemy1", "type": "character"},
    {"name": "Enemy2", "type": "character"},
    {"name": "Weapon1", "type": "weapon"}
])
```

### Advanced Batch Processing
```python
from asset_pipeline import AssetPipeline

pipeline = AssetPipeline()
await pipeline.process_batch(
    assets=asset_list,
    operations=["import", "optimize", "validate"],
    parallel=True,
    on_progress=lambda x: print(f"Progress: {x}%")
)
```

## ⚠️ Important Notes

- Always test batch operations in development environment first
- Use progress callbacks for long-running operations
- Implement proper error handling and rollback mechanisms
- Monitor system resources during large batch operations
- Consider rate limiting for very large batches