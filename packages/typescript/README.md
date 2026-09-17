# @memcell/sdk

Official TypeScript and Node.js SDK for [MemCell](https://memcell.io)—persistent cognitive memory and reasoning substrate for AI coding agents.

## Installation

```bash
npm install @memcell/sdk
# or
pnpm add @memcell/sdk
# or
yarn add @memcell/sdk
```

## Quickstart

```typescript
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
// Outputs LLM-ready context containing active invariants and reflexes
```

### Agentic Loop Wrapper (`wrapExecution`)

```typescript
const devopsMemory = memory.scope("my-org/devops", {
  subject: "pipeline:deploy",
});

const result = await devopsMemory.wrapExecution(
  {
    action: "promote_canary",
    externalRef: "github:run:98213",
  },
  async (ctx) => {
    // ctx.promptContext includes recalled invariants and reflexes
    return await runPromotion(ctx.promptContext);
  },
);
// Automatically reports execution outcome ("worked" or "failed") and closes reinforcement loop!
```

### OAuth 2.0 Machine-to-Machine (M2M) Authentication

```typescript
const memory = new MemCell({
  auth: {
    clientId: process.env.MEMCELL_CLIENT_ID!,
    clientSecret: process.env.MEMCELL_CLIENT_SECRET!,
    scope: "memory:read:acme/* memory:write:acme/backend",
  },
});
// Automatically exchanges tokens and refreshes them proactively 60 seconds before expiry!
```

### Dual-Threshold Rate Limiting & Resilience

```typescript
const memory = new MemCell({
  auth: { apiKey: "mc_live_..." },
  maxRetries: 3,
  onRateLimitWarning: (warning, response) => {
    console.warn("Approaching rate limit capacity:", warning);
  },
});
```

## License

Apache-2.0 © [MemCell](https://memcell.io)
