# Advanced Examples

This directory contains sophisticated examples demonstrating advanced usage patterns of the UnrealBlueprintMCP system.

## 📁 Directory Structure

### 🔄 Batch Operations
**Path**: `batch_operations/`
- **Purpose**: Demonstrates how to perform bulk operations efficiently
- **Examples**: Create multiple blueprints, batch property updates, mass asset management
- **Use Cases**: Level generation, asset pipeline automation, bulk refactoring

### 🔗 LangChain Integration
**Path**: `langchain_integration/`
- **Purpose**: Shows integration with LangChain for AI-powered blueprint generation
- **Examples**: Natural language to blueprint conversion, intelligent component selection
- **Use Cases**: AI-assisted game development, automated blueprint creation from descriptions

### 🌐 Web Dashboard
**Path**: `web_dashboard/`
- **Purpose**: Real-time web interface for monitoring and controlling MCP operations
- **Examples**: Live performance metrics, remote blueprint management, project overview
- **Use Cases**: Team collaboration, remote development, project monitoring

### 🎮 Game Setup Automation
**Path**: `game_setup_automation/`
- **Purpose**: Complete game project setup and configuration automation
- **Examples**: Project initialization, standard blueprint creation, level setup
- **Use Cases**: Rapid prototyping, template-based development, team onboarding

## 🚀 Getting Started

1. **Prerequisites**
   ```bash
   # Ensure MCP server is running
   source mcp_server_env/bin/activate
   fastmcp dev unreal_blueprint_mcp_server.py
   ```

2. **Install Additional Dependencies**
   ```bash
   # For LangChain examples
   pip install langchain openai

   # For web dashboard
   pip install fastapi uvicorn jinja2

   # For advanced batch operations
   pip install aiofiles asyncio-throttle
   ```

3. **Run Examples**
   Each subdirectory contains its own README with specific instructions.

## 📋 Example Complexity Levels

| Example | Complexity | Prerequisites | Estimated Time |
|---------|------------|---------------|----------------|
| Batch Operations | ⭐⭐⭐ | Basic MCP knowledge | 15-30 minutes |
| LangChain Integration | ⭐⭐⭐⭐ | AI/ML familiarity | 30-60 minutes |
| Web Dashboard | ⭐⭐⭐⭐⭐ | Web development | 60+ minutes |
| Game Setup Automation | ⭐⭐⭐⭐ | Game development | 45-90 minutes |

## 🔧 Configuration

Many examples use a shared configuration file:

```python
# examples/advanced/config.py
MCP_SERVER_URL = "ws://localhost:6277"
UNREAL_PROJECT_PATH = "/path/to/your/unreal/project"
DEFAULT_TIMEOUT = 30.0
BATCH_SIZE = 10
```

## 📚 Additional Resources

- [MCP Protocol Documentation](../../docs/API_REFERENCE.md)
- [Unreal Engine Integration Guide](../../docs/UNREAL_INTEGRATION.md)
- [Performance Best Practices](../../docs/PERFORMANCE_GUIDE.md)
- [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md)

## 🤝 Contributing

When adding new advanced examples:

1. Create a new subdirectory with a descriptive name
2. Include a comprehensive README.md
3. Add proper error handling and logging
4. Include performance considerations
5. Provide both simple and complex usage scenarios
6. Add unit tests where applicable

## ⚠️ Important Notes

- These examples are designed for educational purposes
- Always test in a development environment first
- Some examples require additional API keys or services
- Performance may vary based on project size and complexity
- Ensure proper error handling in production use