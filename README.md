# MemCell Client SDKs

The official multi-language client libraries for [MemCell](https://memcell.io)—the persistent cognitive memory and reasoning substrate for autonomous AI coding agents.

This repository is organized as a multi-package monorepo housing client libraries for:

- **TypeScript / JavaScript**: [`@memcell/sdk`](./packages/typescript) (Node $\ge 18$, Bun, Deno, Edge runtimes)
- **Python**: [`memcell`](./packages/python) (Python $\ge 3.10$, sync and async with `httpx`)

---

## Installation

### TypeScript / Node.js

```bash
# npm
npm install @memcell/sdk

# pnpm
pnpm add @memcell/sdk

# yarn
yarn add @memcell/sdk
```

### Python

```bash
# pip
pip install memcell

# uv
uv add memcell

# poetry
poetry add memcell
```

---

## Quickstart

### TypeScript

```ts
import { MemCell } from "@memcell/sdk";

const memory = new MemCell({
  auth: { apiKey: process.env.MEMCELL_API_KEY! },
});

// Recall invariants and reflexes before an agent acts
const recall = await memory.recall({
  namespace: "my-org/my-project",
  query: "production deployment procedure",
});

console.log(recall.promptContext);
// Outputs XML/Markdown prompt context containing active invariants and reflexes
```

### Python

```python
from memcell import AsyncMemCell

async with AsyncMemCell(api_key="mc_live_...") as memory:
    # Recall invariants and reflexes before an agent acts
    recall = await memory.recall(
        namespace="my-org/my-project",
        query="production deployment procedure"
    )
    print(recall.prompt_context)
```

---

## Monorepo Architecture

```
sdk/
├── packages/
│   ├── typescript/        # Modern TypeScript SDK (@memcell/sdk)
│   └── python/            # Modern Python SDK (memcell)
├── .github/workflows/     # Unified CI and multi-package release-please workflows
└── release-please-config.json
```

---

## Development & Contribution

### Prerequisites

- Node.js $\ge 20$ & pnpm $\ge 9$
- Python $\ge 3.10$ & pytest / uv

### Local Setup

```bash
# Install Node dependencies
pnpm install

# Run TypeScript tests & typecheck
pnpm test:ts
pnpm typecheck

# Run Python tests
pnpm test:py
# or directly:
cd packages/python && pytest
```

---

## License

Apache-2.0 © [MemCell](https://memcell.io)
