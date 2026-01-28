---
target:
  - prism/agents/decision.py
  - prism/agents/social_agent.py
  - prism/agents/prompts.py
  - prism/llm/config.py
  - prism/llm/client.py
  - configs/default.yaml
---

# Foundation Agent Framework + Ollama Spec Tests

Validates that PRISM's core agent infrastructure provides config-driven LLM integration, structured agent decisions, and a social agent abstraction.

## Agent Decision Model

### AgentDecision is a validated Pydantic model

Downstream features (simulation loop, metrics, experiments) depend on agent decisions being structured, typed objects — not raw strings or dicts. If the decision model is missing or unvalidated, the entire simulation pipeline breaks.

```
Given the prism/agents/decision.py file
When examining the AgentDecision class
Then it inherits from pydantic.BaseModel
And it has a "choice" field typed as Literal["LIKE", "REPLY", "RESHARE", "SCROLL"]
And it has a "reason" field typed as str
And it has a "content" field typed as str | None with default None
```

### AgentDecision validates content requirement for REPLY and RESHARE

If an agent says "REPLY" but provides no content, the simulation would produce empty replies that corrupt cascade analysis. Validation catches this at the model level rather than downstream.

```
Given the prism/agents/decision.py file
When examining the AgentDecision class
Then it has a validator that checks content is non-empty when choice is "REPLY" or "RESHARE"
And the validator uses pydantic's field_validator or model_validator mechanism
```

## Configuration

### LLMConfig provides validated configuration

Researchers need to swap models and tune parameters via config files, not code changes. Invalid config (e.g., negative temperature) must be caught at startup, not during a multi-hour simulation run.

```
Given the prism/llm/config.py file
When examining the LLMConfig class
Then it inherits from pydantic.BaseModel
And it has a "host" field with default "http://localhost:11434"
And it has a "model_id" field with default "mistral"
And it has a "temperature" field with a constraint between 0.0 and 2.0
And it has a "max_tokens" field with a constraint greater than 0
And it has a "seed" field typed as int | None
```

### Config loads from YAML file

Experiments require reproducible configurations stored as files. If config loading breaks, no simulation can start.

```
Given the prism/llm/config.py file
When examining the load_config function
Then it accepts a path parameter for the YAML file
And it returns a PrismConfig (or similar root config) object
And the returned object contains an llm field of type LLMConfig
```

### Default YAML config exists

A missing default config would block any new user or CI run from starting the system.

```
Given the configs/default.yaml file
When examining its contents
Then it contains an "llm" section
And the llm section specifies "host", "model_id", and "temperature" keys
```

## LLM Client

### Client factory creates OllamaChatClient from config

The client factory decouples agent code from Ollama-specific construction. Without it, changing the LLM provider would require modifying agent code.

```
Given the prism/llm/client.py file
When examining the create_llm_client function
Then it accepts an LLMConfig parameter
And it returns an OllamaChatClient (or compatible client object)
And it passes host and model_id from the config to the client constructor
```

## Prompt Templates

### System prompt includes agent profile

Agents must behave according to their personality and interests. Without profile injection, all 500 agents would behave identically, defeating the purpose of the simulation.

```
Given the prism/agents/prompts.py file
When examining the system prompt template function
Then it accepts agent profile parameters (interests, personality, or similar)
And it returns a string containing the agent's personality/interest information
And the returned string includes instructions about valid decision choices (LIKE, REPLY, RESHARE, SCROLL)
```

### Feed prompt formats posts for agent consumption

The agent needs to see posts in a structured format to make decisions. Malformed feed input produces meaningless decisions.

```
Given the prism/agents/prompts.py file
When examining the feed/user prompt template function
Then it accepts feed text or post data as input
And it returns a formatted string suitable for LLM consumption
```

## Social Agent

### SocialAgent wraps ChatAgent with social behavior

The SocialAgent is the primary abstraction other features interact with. If it doesn't properly wrap ChatAgent, the entire agent layer is unusable.

```
Given the prism/agents/social_agent.py file
When examining the SocialAgent class
Then it has an async decide method that accepts feed text (str) as input
And it returns an AgentDecision instance
And it stores or references a ChatAgent (or equivalent agent) internally
```

### SocialAgent handles structured output with fallback

Not all Ollama models support native structured output. Without a fallback, switching to a model without structured output support would break all agent decisions silently.

```
Given the prism/agents/social_agent.py file
When examining the decide method implementation
Then it attempts to use the agent's structured response (response.value or similar)
And it has a fallback path that parses the text response as JSON
And it has a last-resort fallback that returns a default SCROLL decision
```
