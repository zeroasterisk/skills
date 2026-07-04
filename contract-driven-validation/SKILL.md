---
name: contract-driven-validation
description: Define capabilities as falsifiable assertions with Surface/Needs/Behavior/Evidence. Prevents "it compiles therefore it works."
---

# Contract-Driven Validation

Every capability gets a falsifiable assertion. If you can't specify what evidence proves it works, you don't know what "done" means.

> Adapted from [Intelligent-Internet/zenith](https://github.com/Intelligent-Internet/zenith) engineering-mission-playbook VAL-* assertion system (Apache 2.0).

## VAL-* Assertions

Each capability is defined as a validation assertion with four fields:

```
VAL-001: <capability name>
  Surface:  <where to test it — API, browser, CLI, etc.>
  Needs:    <prerequisites — running server, test data, auth token, etc.>
  Behavior: <what should happen — specific, observable, falsifiable>
  Evidence: <what constitutes proof — request/response, screenshot, test output>
```

### Example: A2A Message Relay

```
VAL-001: Agent-to-agent message delivery
  Surface:  HTTP API (POST /a2a/{agent-slug})
  Needs:    Running relay, two registered agents with API keys
  Behavior: Message sent from agent A arrives in agent B's mailbox
  Evidence: POST returns 200 with task.status=submitted; 
            GET /mailbox/{agent-b} returns the message with correct payload

VAL-002: Mailbox authentication
  Surface:  HTTP API (GET /mailbox/{agent-id})
  Needs:    Running relay, registered agent with api_key_hash
  Behavior: Only the agent's own bearer token can read their mailbox
  Evidence: Correct token → 200 with messages;
            Wrong token → 401 with "invalid API key";
            No token → behavior depends on auth mode (optional: 200, required: 401)
```

## When to Write Assertions

- **Before implementation**: define what "done" looks like
- **During code review**: verify each assertion has evidence
- **Before marking complete**: run each assertion and record evidence

## Assertion Quality Checks

A good assertion is:

- **Falsifiable**: it can fail. "System works correctly" is not falsifiable. "GET /health returns 200 with body {ok: true}" is.
- **Observable**: you can see the evidence without reading source code.
- **Independent**: it can be verified by someone who didn't write the code.
- **Specific**: it names the surface, the inputs, and the expected output.

## Honest Failure

From the Zenith playbook: "Honest failure is allowed. Do not convert missing setup, weak oracle, broad contract, bad task topology, unavailable evidence, incomplete test coverage, repeated worker miss, or changed scope into a speculative pass."

If the assertion fails, report it as failed with the evidence of failure. A documented failure is more valuable than an undocumented "pass."

## Common Rationalizations

| Rationalization | Reality |
|----------------|---------|
| "The code clearly does X" | Code clarity is not behavioral evidence. Run the assertion. |
| "Tests prove it works" | Tests prove the test scenario works. The assertion checks the real surface. |
| "I'll add assertions later" | Assertions written after implementation confirm what you built, not what you should have built. Write them first. |
| "This is too simple for assertions" | Simple capabilities are the easiest to assert. No excuse. |
