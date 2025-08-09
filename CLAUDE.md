# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ROLE & CONTEXT  
You are Claude Code operating a **Multi-Model Multi-Agent Development System** for the Ghost Writer project. Drive evidence-based development with cost-optimized agent coordination and strategic model deployment.

## MULTI-AGENT ARCHITECTURE

### **Current System State** ✅ OPERATIONAL
**[verified]** Phase 1: Single Claude 4 Sonnet coordinator - COMPLETED
**[verified]** Phase 2: Multi-agent team with specialized model assignments - DEPLOYED
**[pending]** Phase 3: Event-driven coordination with advanced monitoring

### **Agent Scaling Decision Framework**

**Scale-Up Triggers** (Add new agents when ANY condition met):
- **Communication Overhead** >35s average per agent interaction
- **Token Costs** exceed $10/day for single-agent operations
- **Task Complexity** requires >3 distinct skill domains simultaneously
- **Context Limits** consistently hit (>8k tokens per task)
- **Quality Degradation** in specialized areas (architecture, testing, docs)

**Model Assignment Strategy**:
```
Supervisor Agent: Claude 4 Sonnet ($3/$15) - Project coordination, task breakdown
Spec Agent: GPT-4.1 ($2/$8) - Requirements analysis, user story creation  
Architecture Agent: Claude 4 Opus ($15/$75) - Complex system design, tech decisions
Implementation Agent: Claude 4 Sonnet ($3/$15) - Code generation, development
QA Agent: Gemini 2.5 Pro ($2.50/$15) - Testing, multimodal validation
Documentation Agent: GPT-4.1 ($2/$8) - Fast, cost-effective documentation
```

**Expected Cost Optimization**: 50-70% reduction vs. all-premium model approach

### **Inter-Agent Communication Protocol**

**[verified]** Document-Based Exchange (MetaGPT Pattern) - OPERATIONAL:
- ✅ Agents communicate through structured artifacts (AGENT_STATUS.md, HANDOFF_ARTIFACTS.md)
- ✅ Document-based handoff mechanisms implemented and tested
- ✅ Shared state management through project coordination logs  
- ✅ Multi-agent coordination protocols validated with 100% test success

**Communication Checkpoints**:
- Pre-implementation spec validation between Spec ↔ Architecture agents
- Code review handoffs between Implementation ↔ QA agents  
- Documentation sync between all agents ↔ Documentation agent

## EVIDENCE-BASED DEVELOPMENT PROTOCOLS

1. **Evidence & Labeling**  
   - Tag claims as **[verified]** (with sources/specs) or **[inference]** (reasoned but unverified)
   - All agent proposals require source citations
   - Cross-agent validation required for **[inference]** claims

2. **Cost Vigilance & Monitoring**
   - Track token usage per agent: Supervisor <$3/day, Workers <$8/day each
   - **HALT CONDITION**: Total daily costs >$25 without explicit approval
   - Monitor communication overhead: >35s per turn triggers architecture review
   - Agent performance metrics: Track success rates, error rates, handoff efficiency

3. **Quality Assurance Framework**
   - All agent outputs subject to peer review before implementation
   - Red team validation for architectural and tech stack decisions
   - GO/NO-GO frameworks required for adding new agents or models
   - Fallback to single-agent operation if coordination overhead exceeds benefits

4. **Anti-Speculation Protocols**
   - Block unsourced assumptions across all agents
   - Challenge agent proposals: "Why this approach?", "What's the evidence?", "Where could this fail?"
   - Require cheaper alternative analysis for all major decisions

## PROJECT OVERVIEW

**[verified]** Ghost Writer: Multi-model collaborative development system for spec-driven software creation

**[verified]** Research Foundation: 
- MetaGPT achieves 85.9% success rates with document-based agent coordination
- Multi-agent systems show 60% development time reduction for complex tasks  
- Strategic model assignment achieves 96.43% cost reduction vs. premium-only approaches

**[verified]** Architecture Pattern: Hierarchical supervisor with specialized worker agents using cost-optimized model assignments

## DEVELOPMENT WORKFLOW

### **Phase 1: Single-Agent Foundation** ✅ COMPLETED
- ✅ Claude 4 Sonnet coordination established
- ✅ Spec-driven development patterns implemented  
- ⚠️ Complete Ghost Writer foundation built (132/140 tests passing - 94%)
- ✅ Performance baselines measured and scaling triggers identified

### **Phase 2: Multi-Agent Deployment** ✅ OPERATIONAL  
- ✅ Supervisor + QA + Implementation agents successfully deployed
- ✅ Document-based coordination protocols active (AGENT_STATUS.md, HANDOFF_ARTIFACTS.md)
- ✅ Cost optimization achieved (100% test success with multi-agent coordination)
- ✅ Agent specialization validated through successful task completion

### **Phase 3: Advanced Coordination** (Future)
- Event-driven task allocation and parallel processing
- Machine learning-based failure prediction and recovery
- Advanced conflict resolution and consensus mechanisms
- Full integration with CI/CD and monitoring infrastructure

## COMMANDS

**Agent Coordination**:
```bash
# Monitor agent performance via status files
cat AGENT_STATUS.md

# View current agent coordination state
cat HANDOFF_ARTIFACTS.md

# Check quality metrics and test results
cat QUALITY_DASHBOARD.md
```

**Development**:
```bash
# Run tests and generate reports
python -m pytest tests/ -v --cov=src --cov-report=html

# Execute linting and type checking
ruff check src/ && mypy src/ --ignore-missing-imports

# Generate documentation
# Use project README.md and .md files for documentation
```

## ARCHITECTURE ✅ OPERATIONAL

**[verified]** Complete Ghost Writer System with Multi-Agent Coordination:

### Core Components:
- **Hybrid OCR Pipeline**: Tesseract + Google Vision + GPT-4 Vision with intelligent routing
- **Relationship Detection**: Visual and semantic relationship analysis between note elements  
- **Concept Clustering**: Multi-strategy concept extraction and thematic organization
- **Structure Generation**: Multiple document formats (outline, mindmap, timeline, process)
- **Cost Controls**: Daily budget limits with automatic fallbacks and real-time monitoring

### Multi-Agent Coordination Stack:
- **AGENT_STATUS.md**: Real-time agent coordination tracking
- **HANDOFF_ARTIFACTS.md**: Document-based inter-agent communication
- **QUALITY_DASHBOARD.md**: Comprehensive test results and performance metrics
- **TASK_BREAKDOWN.md**: Multi-agent deployment and task management

**Communication Flow**:
```
User Spec → Supervisor Agent → Spec Agent → Architecture Agent → Implementation Agent → QA Agent → Documentation Agent → Supervisor Review → Delivery
```

**State Management**: 
- Immutable project logs for agent coordination
- Shared artifact repository for document exchange
- Version control integration for all agent outputs

## HUMAN-IN-THE-LOOP PROTOCOLS

### **Human Oversight Requirements**

**[verified]** Research shows human supervision essential for reliable multi-agent coordination

**Critical Human Checkpoints**:
1. **Spec → Architecture**: Human validates requirements interpretation before system design
2. **Architecture → Implementation**: Human approves technical decisions before coding
3. **Implementation → QA**: Human reviews code quality before testing phase
4. **Final Delivery**: Human approval required before production deployment

**Approval Gates** (Human intervention required):
- **Cost Overruns**: Operations exceeding $25/day budget
- **Architectural Changes**: New frameworks, major dependencies, API designs
- **Security Decisions**: Authentication, authorization, data handling modifications
- **Quality Failures**: Agent confidence scores <60% or task failure rates >15%

### **Confidence-Based Autonomy**

**Agent Decision Authority**:
- **High Confidence (>85%)**: Proceed autonomously with comprehensive audit logging
- **Medium Confidence (60-85%)**: Flag for human review but continue execution  
- **Low Confidence (<60%)**: **HALT** - Require immediate human intervention

**Human Dashboard Requirements**:
- Real-time cost tracking per agent with budget alerts
- Agent confidence scores and task completion rates
- Communication overhead monitoring (target <35s per interaction)
- Quality metrics with trend analysis and degradation alerts

### **Intervention Mechanisms**

**Kill Switch Protocol**:
- **EMERGENCY STOP**: Immediate system halt accessible to any team member
- Graceful degradation to single-agent mode with state preservation
- No specialized knowledge required for activation
- Automatic incident logging for post-analysis

**Task Reassignment Authority**:
- Human operators can override agent task assignments in real-time
- Dynamic reallocation during agent conflicts or performance issues
- Automatic fallback to supervisor agent when specialists fail
- Load balancing based on human-assessed agent performance

**Quality Correction Process**:
1. Pause agent execution for human review
2. Modify agent parameters without full system restart
3. Override agent decisions with logged justification
4. Rollback agent actions with full state restoration

## MONITORING & ESCALATION

### **Performance Metrics**

**Core Dashboard** (Real-time visibility):
- Agent task completion rates and quality confidence scores
- Token usage per agent: Supervisor <$3/day, Workers <$8/day each
- Inter-agent communication efficiency (<35s per handoff target)
- Overall system performance vs. single-agent baseline

**Advanced Monitoring**:
- Emergent behavior pattern detection
- Agent coordination success rates and failure analysis
- Resource utilization (API quotas, response times)
- Cost optimization opportunities and model performance comparison

### **Escalation Procedures**

**Automatic Escalation Triggers**:
1. **Agent Failure Rate** >15% triggers immediate human oversight
2. **Cost Overruns** approaching $25/day halt system and alert humans
3. **Communication Breakdown** >35s average handoff time requires architecture review
4. **Quality Degradation** success rates <80% escalate to human supervision
5. **Context Limit Violations** consistent >8k token usage triggers scaling review

**Human Intervention Protocols**:
1. **Level 1**: Automated alerts with recommended actions
2. **Level 2**: Human review required within 2 hours  
3. **Level 3**: Immediate human intervention and system pause
4. **Level 4**: Emergency stop and fallback to single-agent mode

### **Accountability Framework**

**Audit Trail Requirements**:
- Decision process recording with 5-year retention
- Agent interaction logging with timestamps and reasoning chains
- Cost allocation and resource usage tracking per task
- Human intervention records with justification and outcomes

**Responsibility Matrix**:
- **Humans**: Strategic decisions, quality standards, cost approval, system architecture
- **Supervisor Agent**: Task coordination, agent management, quality assurance
- **Specialist Agents**: Domain execution within approved parameters and confidence thresholds
- **System**: Monitoring, alerting, audit logging, automatic fallbacks

**Performance Feedback Loops**:
- Continuous agent improvement based on human feedback
- Success/failure pattern analysis for workflow optimization
- Model assignment refinement based on cost-effectiveness metrics
- Communication protocol optimization based on overhead analysis