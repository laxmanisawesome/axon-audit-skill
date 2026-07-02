# Scaling Math Reference

## Key Formulas

### Little's Law
```
L = λ × W
L = concurrent users in system
λ = arrival rate (requests/second)
W = average time per request (seconds)

Example:
λ = 100 req/s
W = 200ms = 0.2s
L = 100 × 0.2 = 20 concurrent connections
```

### QPS from DAU
```
QPS = (DAU × requests_per_user_per_day) / 86400

Example:
10K DAU × 50 requests/day = 500K req/day
500K / 86400 ≈ 5.8 QPS
```

### Database Connections
```
max_connections = concurrent_users × connection_per_user

At 1K users with pool of 10: need ~10 connections
At 10K users: need ~50 connections (pooling matters)
At 100K users: ~200 connections (need connection pooling + read replicas)
```

## Scaling Milestones

### 1K DAU
- Single DB足够. No caching needed.
- One web server. No CDN needed.
- Cost: ~$20-50/mo

### 10K DAU
- DB indexing becomes critical. N+1 queries become visible.
- CDN for static assets becomes useful.
- Rate limiting on auth becomes necessary.
- Cost: ~$100-300/mo

### 100K DAU
- Read replicas or caching layer (Redis) becomes necessary.
- Queue for background jobs becomes useful.
- Database connection pooling is required.
- Cost: ~$500-2000/mo

### 1M DAU
- Microservices or modular monolith. Caching everywhere.
- Read replicas, write masters. Sharding may be needed.
- Full monitoring, alerting, on-call rotation.
- Cost: ~$3K-15K/mo

## Cost Estimation
```
Monthly cost ≈ compute + storage + bandwidth + API calls + third-party services

Firebase/Firestore at 100K DAU:
- Firestore reads: ~10M/mo = $70
- Functions: ~5M invocations = $50
- Storage: ~50GB = $2.50
- Auth: free up to 50K
Total Firestore ≈ $125/mo
```
