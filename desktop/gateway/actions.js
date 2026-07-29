/**
 * Action Registry — all endpoint definitions live here.
 *
 * The Gateway must never contain endpoint strings.
 * Each action maps to a provider, path template, cache policy, and timeout.
 *
 * Path templates use {paramName} syntax.
 * The Provider resolves templates from params.
 */

const ACTION_MAP = {
  // ─── Market ──────────────────────────────────────
  'market-state': {
    provider: 'tsetmc',
    path: '/api/MarketData/GetMarketState',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },   // 1 min
    timeout: 10000,
  },

  'instrument-market-state': {
    provider: 'tsetmc',
    path: '/api/MarketData/GetInstrumentMarketState/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },
    timeout: 10000,
  },

  // ─── Price ───────────────────────────────────────
  'market-watch': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetMarketWatch/{marketId}/{type}',
    method: 'GET',
    cache: { enabled: true, ttl: 30000 },   // 30 sec
    timeout: 15000,
  },

  'market-overview': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetMarketOverview',
    method: 'GET',
    cache: { enabled: true, ttl: 30000 },
    timeout: 10000,
  },

  'closing-price': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetClosingPriceInfo/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 30000 },
    timeout: 10000,
  },

  'closing-price-all': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetClosingPriceAll',
    method: 'GET',
    cache: { enabled: true, ttl: 30000 },
    timeout: 15000,
  },

  'price-history': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetClosingPriceHistory/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 3600000 },  // 1 hour
    timeout: 15000,
  },

  'price-change': {
    provider: 'tsetmc',
    path: '/api/ClosingPrice/GetPriceChange/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 30000 },
    timeout: 10000,
  },

  // ─── Order Book ──────────────────────────────────
  'best-limits': {
    provider: 'tsetmc',
    path: '/api/BestLimits/GetBestLimits/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 5000 },   // 5 sec
    timeout: 10000,
  },

  'best-limits-detail': {
    provider: 'tsetmc',
    path: '/api/BestLimits/GetBestLimitsDetail/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 5000 },
    timeout: 10000,
  },

  // ─── Client Type ─────────────────────────────────
  'client-type': {
    provider: 'tsetmc',
    path: '/api/ClientType/GetClientType/{insCode}/{dayOrTotal}',
    method: 'GET',
    cache: { enabled: false },
    timeout: 10000,
  },

  'client-type-history': {
    provider: 'tsetmc',
    path: '/api/ClientType/GetClientTypeHistory/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 3600000 },
    timeout: 10000,
  },

  // ─── Shareholders ────────────────────────────────
  'shareholders': {
    provider: 'tsetmc',
    path: '/api/Shareholder/GetInstrumentShareholders/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 3600000 },
    timeout: 10000,
  },

  'shareholder-history': {
    provider: 'tsetmc',
    path: '/api/Shareholder/GetInstrumentShareholderHistory/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 3600000 },
    timeout: 10000,
  },

  // ─── Index ───────────────────────────────────────
  'index-b1': {
    provider: 'tsetmc',
    path: '/api/Index/GetIndexB1',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },
    timeout: 10000,
  },

  'index-b2': {
    provider: 'tsetmc',
    path: '/api/Index/GetIndexB2',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },
    timeout: 10000,
  },

  // ─── Sector ──────────────────────────────────────
  'sectors': {
    provider: 'tsetmc',
    path: '/api/StaticData/GetStaticData',
    method: 'GET',
    cache: { enabled: true, ttl: 86400000 },  // 24 hours
    timeout: 10000,
  },

  'sector-instruments': {
    provider: 'tsetmc',
    path: '/api/StaticData/GetStaticData/{sectorId}',
    method: 'GET',
    cache: { enabled: true, ttl: 86400000 },
    timeout: 10000,
  },

  // ─── Instrument ──────────────────────────────────
  'instrument-info': {
    provider: 'tsetmc',
    path: '/api/Instrument/GetInstrumentInfo/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 86400000 },
    timeout: 10000,
  },

  'instrument-search': {
    provider: 'tsetmc',
    path: '/api/Instrument/GetInstrumentSearch/{search}',
    method: 'GET',
    cache: { enabled: false },
    timeout: 10000,
  },

  // ─── Message ─────────────────────────────────────
  'messages': {
    provider: 'tsetmc',
    path: '/api/Message/GetMessage',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },
    timeout: 10000,
  },

  'instrument-messages': {
    provider: 'tsetmc',
    path: '/api/Message/GetInstrumentMessage/{insCode}',
    method: 'GET',
    cache: { enabled: true, ttl: 60000 },
    timeout: 10000,
  },
};

module.exports = { ACTION_MAP };
