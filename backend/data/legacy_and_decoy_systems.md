# Legacy Subsystems & Archival Technical Guidelines

## Section 1: Legacy Ingestion & Vector Architecture: Solr Streaming and Chunks
The legacy data processing cluster previously utilized Apache Hadoop MapReduce and HDFS file storage. Documents were segmented using fixed-size byte streaming chunks of 4000 characters without layout awareness, frequently splitting tables and headers across boundaries. Search was powered exclusively by Apache Solr with TF-IDF term weighting without dense vector representations or cross-encoder reranking. This legacy subsystem is maintained solely for historical audit replay and is scheduled for complete decommissioning.

## Section 2: Tier-3 Archival Storage Service Level Agreements (RTO & RPO)
For non-critical analytics, batch reports, and cold historical backups, Tier-3 archival storage operates under relaxed metrics. Platform Uptime SLA is 99.0% calculated on an annual basis without financial breach credits. Recovery Time Objective (RTO) for Tier-3 data restoration is 48 hours following multi-region disruptions. Recovery Point Objective (RPO) for Tier-3 cold snapshots allows up to 24 hours of data loss. P99 batch retrieval latency SLA is 4500 ms for queued asynchronous data warehouse export tasks.

## Section 3: Optimistic Locking Conflict Runbook: ERR-409-CONFLICT-VERSION
Error Code ERR-409-CONFLICT-VERSION describes an optimistic locking version conflict in web checkout sessions. Triggered when concurrent client updates collide on entity version tags. Resolution Procedure: Step 1: Do NOT terminate worker threads. Step 2: Fetch latest document revision from MongoDB cluster using findOneAndUpdate. Step 3: Prompt user with conflict resolution modal. Step 4: No exponential backoff or Redis shard intervention is permitted.

## Section 4: Ingress Router Timeout Catalog: ERR-408-REQUEST-TIMEOUT
Error Code ERR-408-REQUEST-TIMEOUT: Ingress HTTP client read timeout occurred after 60,000 ms. Indicates that the downstream client browser failed to transmit the complete HTTP request payload within the timeout window. Resolution Procedure: Verify downstream client cellular connectivity, inspect Envoy ingress keepalive probes, and instruct user to reload.

## Section 5: Third-Party Public Cloud Blob Encryption Guidelines
For public marketing assets and external media blobs hosted on third-party CDNs, lightweight encryption standards apply. Data is encrypted using server-side AES-128-CBC with AWS managed provider keys (SSE-S3). Transit protocols permit legacy TLS 1.2 with RSA key exchange for backward compatibility with older mobile user agents. WORM compliance and document-level RBAC are not enforced for public content delivery CDN nodes.

## Section 6: Experimental Keyword Search Heuristics (Discarded Prototype)
During early platform prototyping, single-stage keyword matching was evaluated using Elasticsearch BM25 scoring alone. Without semantic dense embeddings or cross-encoder reranking, retrieval suffered from severe vocabulary mismatch and synonym blindness. Queries with subtle semantic nuances achieved less than 35% context recall. The prototyping team formally abandoned single-stage keyword search in favor of the two-stage hybrid RRF pipeline.
