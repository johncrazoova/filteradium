# Gateway Architecture

## Overview

Gateway is a **provider-agnostic** request routing layer that isolates all external communication from the application logic. TSETMC is one of potentially many providers.

## Folder Structure

```
desktop/gateway/
├── gateway.js          # Core router + event emitter
├── actions.js          # Action Registry (all endpoints)
├── providers.js        # Provider abstraction + TsetmcProvider
├── config.js           # GatewayResponse + types
├── health.js           # HealthChecker utility
├── ipc.js              # IPC bridge (single endpoint)
├── index.js            # Module exports + factory
└── middlewares/
    ├── logger.js       # Request logging
    ├── retry.js        # Exponential backoff retry
    ├── cache.js        # TTL-based response cache
    └── rateLimiter.js  # Requests per second limit
```

## Providers

| Provider | Status | Description |
|----------|--------|-------------|
| TsetmcProvider | ✅ Implemented | TSETMC CDN API |
| CodalProvider | 🔲 Planned | Codal disclosures |
| RahavardProvider | 🔲 Planned | Rahavard data |
| CustomProvider | 🔲 Planned | User-defined |

### Adding a New Provider

1. Create a class extending `BaseProvider`
2. Implement `request()`, `healthCheck()`, `parse()`
3. Register: `gateway.registerProvider('name', new MyProvider())`
4. Update actions to use the new provider

## Middleware Pipeline

```
Request → Logger → RateLimiter → Cache → Retry → Provider → Logger
```

| Middleware | Purpose | Configurable |
|------------|---------|--------------|
| Logger | Logs start/end of each request | Yes |
| RateLimiter | Limits requests per second | Yes |
| Cache | Stores responses by TTL | Per-action |
| Retry | Retries with backoff on failure | Yes |

### Adding a New Middleware

```javascript
class MyMiddleware {
  async handle(context, next) {
    // Before
    const result = await next();
    // After
    return result;
  }
}
gateway.use(new MyMiddleware());
```

## IPC

Single IPC endpoint: `gateway:request`

```javascript
// Renderer
const result = await window.api.request('price-history', { insCode: '12345' });
// result = { ok, data, error, request: { provider, url, retries, duration } }
```

## Events

| Event | Payload |
|-------|---------|
| `request:start` | `{ action, provider }` |
| `request:success` | `{ action, provider, duration, cached }` |
| `request:error` | `{ action, provider, duration, error }` |
| `request:retry` | `{ action, attempt, delay, error }` |
| `request:cached` | `{ action }` |

## Migration Strategy

1. **Phase 1** (current): Gateway exists alongside `apiFetch()`
2. **Phase 2**: Register IPC handler, expose `request()` in preload
3. **Phase 3**: Replace `apiFetch()` calls in renderer with `window.api.request()`
4. **Phase 4**: Remove `apiFetch()` and `API_URLS`

## Extension Strategy

- **New Provider**: Add class → Register → Update actions
- **New Action**: Add to `ACTION_MAP` in `actions.js`
- **New Middleware**: Create class → `gateway.use()`
- **New Feature**: Add middleware (e.g., metrics, circuit breaker)

## Constraints

- Gateway must never contain endpoint strings (use `actions.js`)
- Gateway must never contain provider-specific logic
- Every request must return `GatewayResponse`
- UI must never change during refactoring
- Old code must remain until migration is complete
