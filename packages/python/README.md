# memcell

Official Python SDK for [MemCell](https://memcell.io)—persistent cognitive memory and reasoning substrate for AI coding agents.

## Installation

```bash
pip install memcell
# or
uv add memcell
# or
poetry add memcell
```

## Quickstart

### Asynchronous Client (`AsyncMemCell`)

```python
import asyncio
from memcell import AsyncMemCell

async def main():
    async with AsyncMemCell(api_key="mc_live_...") as memory:
        # Pre-flight recall before an agent acts
        recall = await memory.recall(
            namespace="acme/devops",
            query="how to deploy the canary pipeline"
        )
        print(recall.prompt_context)

        # In-flight scoped execution with automatic reinforcement
        devops = memory.scope("acme/devops", subject="pipeline:canary")
        result = await devops.wrap_execution(
            action="deploy_canary",
            external_ref="ci:run:1049",
            fn=lambda ctx: print("Deploying with context:", ctx.prompt_context)
        )

asyncio.run(main())
```

### Synchronous Client (`MemCell`)

```python
from memcell import MemCell

memory = MemCell(api_key="mc_live_...")

recall = memory.recall(
    namespace="acme/backend",
    query="database connection pool configuration"
)
for statement in recall.statements:
    print(f"[{statement.kind}] {statement.title} (confidence: {statement.confidence})")
```

### OAuth 2.0 Machine-to-Machine (M2M)

```python
from memcell import AsyncMemCell

memory = AsyncMemCell(
    client_id="client_xyz",
    client_secret="secret_xyz",
    scope="memory:read:acme/* memory:write:acme/backend"
)
# Automatically handles token exchange and proactively refreshes before expiration!
```

### Rate Limiting & Resilience

```python
from memcell import AsyncMemCell

memory = AsyncMemCell(
    api_key="mc_live_...",
    max_retries=3,
    on_rate_limit_warning=lambda warning, response: print(f"Warning: {warning}")
)
# Automatically performs jittered exponential backoff respecting server Retry-After!
```

## License

Apache-2.0 © [MemCell](https://memcell.io)
