---
target:
  - prism/agents/decisions.py
  - prism/agents/social_agent.py
  - prism/agents/profiles.py
  - prism/llm/client.py
  - prism/config/settings.py
---

# Foundation Agent Spec Tests

These tests validate that the foundation agent framework provides the core infrastructure for PRISM: structured agent decisions, LLM client abstraction, and configuration-driven behavior.

## Data Model Structure

### Choice Enum Completeness

Agents must have a complete set of social media actions available. Without all four action types, the simulation cannot model realistic social media behavior (lurking, engagement, conversation, amplification).

```
Given the prism/agents/decisions.py file
When examining the Choice enum
Then it has exactly four values: IGNORE, LIKE, REPLY, RESHARE
And each value is a string enum member
```

### AgentDecision Structure

Decisions must capture both the action and reasoning. Without structured output, we cannot analyze why agents behave as they do, which is core to the research value of PRISM.

```
Given the prism/agents/decisions.py file
When examining the AgentDecision class
Then it is a dataclass with fields: choice, reason, content, post_id
And choice is typed as Choice
And reason is typed as str
And content is typed as str | None
And post_id is typed as str
```

### AgentDecision Validation

Content must match choice type to maintain data integrity. A LIKE with content or a REPLY without content would corrupt simulation state.

```
Given the prism/agents/decisions.py file
When examining the AgentDecision class
Then it has validation logic that enforces:
  - content is None when choice is IGNORE or LIKE
  - content is not None when choice is REPLY or RESHARE
```

### AgentProfile Structure

Agents need identity and interests to make personalized decisions. Without profiles, all agents would behave identically, defeating the purpose of agent-based modeling.

```
Given the prism/agents/profiles.py file
When examining the AgentProfile class
Then it is a dataclass with fields: id, name, interests, personality
And interests is typed as list[str]
And the class can be instantiated with required fields
```

## LLM Client

### OllamaChatClient Interface

The system needs a standard way to communicate with Ollama. Without a proper client interface, we cannot make LLM calls or swap providers.

```
Given the prism/llm/client.py file
When examining the OllamaChatClient class
Then it has an __init__ method accepting endpoint and model parameters
And it has an async chat method accepting messages parameter
And the chat method returns a string
```

### OllamaChatClient HTTP Integration

The client must properly communicate with Ollama's REST API. Incorrect API usage would cause all agent decisions to fail.

```
Given the prism/llm/client.py file
When examining the OllamaChatClient.chat implementation
Then it makes HTTP POST requests to the /api/chat endpoint
And it sends messages in Ollama's expected format
And it extracts the response content from the API response
```

## Configuration

### LLMConfig Structure

Configuration must be validated to prevent runtime errors. Invalid config (wrong URL, unknown model) should fail fast, not during simulation.

```
Given the prism/config/settings.py file
When examining the LLMConfig class
Then it has fields: endpoint, model, reasoning_effort, timeout
And endpoint has a default value
And model has a default value
```

### Config Loading

Users must be able to configure the system via YAML without code changes. Without config loading, every change requires code modification.

```
Given the prism/config/settings.py file
When examining the module
Then there is a load_config function
And it accepts a file path parameter
And it returns a configuration object
```

## Agent Implementation

### SocialAgent Structure

The SocialAgent is the core abstraction connecting LLM to simulation. Without it, we cannot create agents that make decisions.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has an __init__ method accepting profile and client parameters
And it stores the profile as an instance attribute
And it stores the client as an instance attribute
```

### SocialAgent Decision Method

Agents must be able to evaluate feeds and decide. Without the decide method, agents cannot participate in simulation.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has an async decide method
And the decide method accepts a feed parameter (list of posts)
And the decide method returns an AgentDecision
```

### Prompt Building

Prompts must incorporate agent profile for personalized decisions. Generic prompts would produce generic, unrealistic behavior.

```
Given the prism/agents/prompts.py file
When examining the module
Then there is a build_system_prompt function that accepts an AgentProfile
And there is a build_user_prompt function that accepts a list of posts
And both functions return strings
```

## Integration

### Module Exports

Users must be able to import core classes easily. Poor exports make the library hard to use.

```
Given the prism/agents/__init__.py file
When examining the module exports
Then SocialAgent is exported
And AgentDecision is exported
And Choice is exported
And AgentProfile is exported
```

### LLM Module Exports

```
Given the prism/llm/__init__.py file
When examining the module exports
Then OllamaChatClient is exported
```

### Config Module Exports

```
Given the prism/config/__init__.py file
When examining the module exports
Then load_config is exported
And LLMConfig is exported
```
