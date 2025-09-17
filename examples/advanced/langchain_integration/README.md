# LangChain Integration Examples

This directory demonstrates advanced AI-powered blueprint generation using LangChain integration with the UnrealBlueprintMCP system.

## 🧠 AI-Powered Features

### 🗣️ Natural Language Blueprint Generation
**File**: `nl_blueprint_generator.py`
- Convert natural language descriptions to blueprints
- Intelligent component selection based on description
- Automatic property inference from context
- Support for complex multi-component blueprints

### 🤖 Intelligent Assistant
**File**: `blueprint_assistant.py`
- Interactive AI assistant for blueprint development
- Context-aware suggestions and optimizations
- Automated code generation and property setup
- Integration with existing project assets

### 🎯 Smart Template Generator
**File**: `smart_template_generator.py`
- Generate blueprint templates from game descriptions
- Automatic architecture planning
- Component dependency analysis
- Performance optimization suggestions

### 🔍 Code Analysis and Suggestions
**File**: `code_analyzer.py`
- Analyze existing blueprints for improvements
- Suggest optimizations and best practices
- Identify potential issues and bugs
- Generate documentation automatically

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup API Keys**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   # or
   echo "OPENAI_API_KEY=your-key" >> .env
   ```

3. **Test Basic Functionality**
   ```bash
   python nl_blueprint_generator.py --description "A fast-moving enemy that shoots projectiles"
   ```

## 📋 Configuration

```python
# LangChain Configuration
LANGCHAIN_CONFIG = {
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are an expert Unreal Engine blueprint developer..."
}
```

## 🎯 Usage Examples

### Natural Language Generation
```python
from nl_blueprint_generator import NLBlueprintGenerator

generator = NLBlueprintGenerator()
result = await generator.generate_from_description(
    "Create a player character that can jump, run, and shoot. "
    "The character should have health and ammunition systems."
)
```

### Interactive Assistant
```python
from blueprint_assistant import BlueprintAssistant

assistant = BlueprintAssistant()
await assistant.start_session()

# User: "I need a weapon that fires in burst mode"
# Assistant will analyze, suggest components, and generate blueprint
```

### Smart Template Generation
```python
from smart_template_generator import SmartTemplateGenerator

generator = SmartTemplateGenerator()
template = await generator.create_game_template(
    game_type="platformer",
    features=["collectibles", "enemies", "power-ups"],
    complexity="medium"
)
```

## 🧠 AI Prompt Engineering

### System Prompts
The examples use carefully crafted system prompts for optimal results:

```python
BLUEPRINT_EXPERT_PROMPT = """
You are an expert Unreal Engine blueprint developer with deep knowledge of:
- Component architecture and best practices
- Performance optimization techniques
- Blueprint visual scripting patterns
- Game development patterns and conventions

When generating blueprints, always consider:
1. Performance implications
2. Maintainability and modularity
3. Unreal Engine best practices
4. Component relationships and dependencies
"""
```

### Context Management
- Maintains conversation history for better understanding
- Uses project-specific context when available
- Adapts suggestions based on existing blueprints

## 🔧 Advanced Features

### Chain of Thought Processing
```python
# Example of multi-step blueprint generation
async def generate_complex_blueprint(description):
    # Step 1: Analyze requirements
    requirements = await analyze_requirements(description)

    # Step 2: Plan architecture
    architecture = await plan_architecture(requirements)

    # Step 3: Generate components
    components = await generate_components(architecture)

    # Step 4: Create blueprint
    blueprint = await create_blueprint(components)

    return blueprint
```

### Multi-Agent Collaboration
```python
# Different AI agents for different tasks
class BlueprintTeam:
    def __init__(self):
        self.architect = ArchitectAgent()  # High-level design
        self.implementer = ImplementerAgent()  # Detailed implementation
        self.optimizer = OptimizerAgent()  # Performance tuning
        self.reviewer = ReviewerAgent()  # Quality assurance
```

## 📊 Performance Optimization

### Token Usage Optimization
- Use template-based prompts to reduce token consumption
- Implement response caching for similar requests
- Batch multiple operations when possible

### Response Quality Improvement
- Use few-shot examples in prompts
- Implement validation and retry logic
- Use structured output formats (JSON schemas)

## ⚠️ Important Notes

### API Usage and Costs
- Monitor API usage and costs carefully
- Implement rate limiting for production use
- Use caching to reduce redundant API calls
- Consider using smaller models for simple tasks

### Quality Assurance
- Always validate AI-generated blueprints
- Test generated code in development environment
- Implement human review for critical blueprints
- Use version control for AI-generated assets

### Privacy and Security
- Never send sensitive project data to external APIs
- Use local models when possible for sensitive projects
- Implement proper API key management
- Review generated code for security implications

## 🔗 Integration with Other Examples

- **Batch Operations**: Use AI to generate bulk blueprint specifications
- **Web Dashboard**: Display AI suggestions in the web interface
- **Game Setup**: Use AI to create initial project templates

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Unreal Engine Blueprint Best Practices](https://docs.unrealengine.com/5.0/en-US/blueprints-best-practices-in-unreal-engine/)
- [AI-Assisted Game Development Patterns](../../docs/AI_DEVELOPMENT_PATTERNS.md)