# System Patterns

## Architecture Patterns

### Hybrid OCR Pipeline
- **Pattern**: Strategy pattern with cost-aware routing
- **Components**: Tesseract (local), Qwen2.5-VL (local LLM), Google Vision (cloud), GPT-4 Vision (cloud)
- **Routing**: Confidence-based provider selection with budget controls
- **Fallback**: Automatic degradation to local providers when over budget

### Document Processing Pipeline
- **Pattern**: Pipeline pattern with staged processing
- **Stages**: OCR → Relationship Detection → Concept Clustering → Structure Generation
- **Data Flow**: Each stage enhances and transforms the data
- **Error Handling**: Graceful degradation at each stage

### Clean Room Development
- **Pattern**: Independent implementation without licensed dependencies
- **Current State**: Clean room decoder implemented but needs enhancement
- **Goal**: Match sn2md's 2.8M pixel extraction without using their code

## Code Patterns

### Test-Driven Development
- **Coverage**: 76% with comprehensive test suite
- **Categories**: Unit, integration, e2e, performance tests
- **Mocking**: External API calls mocked by default
- **Performance**: Tests validate <30s OCR, <10s processing targets

### Type Safety
- **MyPy**: Full compliance with strict typing
- **Type Hints**: All functions and methods typed
- **Validation**: Runtime type checking for critical paths

### Error Handling
- **Pattern**: Try-except with specific exception handling
- **Logging**: Comprehensive logging at all levels
- **Fallbacks**: Automatic fallback mechanisms for all external dependencies

## Documentation Patterns

### Multi-Agent Coordination
- **CLAUDE.md**: Development protocols for Claude Code
- **Memory Bank**: Persistent context across sessions
- **Handoff Documents**: Inter-agent communication through artifacts

### Living Documentation
- **Updates**: Documentation updated with code changes
- **Testing**: Documentation accuracy validated through tests
- **Version Control**: All documentation under git control

## Deployment Patterns

### CI/CD Pipeline
- **Quality Gates**: Linting, type checking, tests, coverage
- **Staging**: Smoke tests and performance benchmarks
- **Production**: Health checks and monitoring
- **Rollback**: Automated rollback on failure

### Configuration Management
- **Environment Variables**: Sensitive data in environment
- **YAML Configuration**: Structured configuration files
- **Feature Flags**: Gradual feature rollout capability