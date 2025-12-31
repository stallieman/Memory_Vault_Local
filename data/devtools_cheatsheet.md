# Kibana Dev Tools Cheatsheet (Elasticsearch Essentials)

## Index Management

### Create Index with Shard Settings, Mappings, Alias
```json
PUT /my-index
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "timestamp": { "type": "date" },
      "user": { "type": "keyword" },
      "message": { "type": "text" }
    }
  },
  "aliases": {
    "my-index-alias": {}
  }
}
```

---

## Composable Index Templates

### Create Template (shards, ILM, mappings, alias)
```json
PUT _index_template/my-template
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "index.lifecycle.name": "logs-ilm-policy"
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "level": { "type": "keyword" },
        "message": { "type": "text" }
      }
    },
    "aliases": {
      "current-logs": {}
    }
  },
  "priority": 50,
  "version": 1
}
```

### List All Templates
```
GET _index_template
```

### Delete Template
```
DELETE _index_template/my-template
```

---

## ILM (Index Lifecycle Management)

### Create ILM Policy
```json
PUT _ilm/policy/logs-ilm-policy
{
  "policy": {
    "phases": {
      "hot": { "actions": { "rollover": { "max_size": "50gb", "max_age": "30d" } } },
      "delete": { "min_age": "90d", "actions": { "delete": {} } }
    }
  }
}
```

### List ILM Policies
```
GET _ilm/policy
```

---

## Ingest Pipelines

### Create Ingest Pipeline
```json
PUT _ingest/pipeline/logs-pipeline
{
  "description": "Parse log lines",
  "processors": [
    { "grok": { "field": "message", "patterns": ["%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:msg}"] } },
    { "rename": { "field": "msg", "target_field": "message" } },
    { "date": { "field": "timestamp", "formats": ["ISO8601"] } },
    { "remove": { "field": "unwanted_field" } }
  ]
}
```

### List All Pipelines
```
GET _ingest/pipeline
```

---

## Reindex

### Simple Reindex
```json
POST _reindex
{
  "source": { "index": "old-index" },
  "dest": { "index": "new-index" }
}
```

### Reindex with Query & Script
```json
POST _reindex
{
  "source": {
    "index": "source-index",
    "query": { "range": { "timestamp": { "gte": "now-30d/d" } } }
  },
  "dest": { "index": "dest-index" },
  "script": { "source": "ctx._source.status = 'archived'" }
}
```

---

## Watcher

### Create Watch (Example: Failed Logins)
```json
PUT _watcher/watch/failed_login_watch
{
  "trigger": { "schedule": { "interval": "5m" } },
  "input": {
    "search": {
      "request": {
        "indices": ["logs-*"],
        "body": { "query": { "match": { "event": "login_failed" } } }
      }
    }
  },
  "condition": { "compare": { "ctx.payload.hits.total.value": { "gt": 5 } } },
  "actions": {
    "log": { "logging": { "text": "More than 5 failed logins in last 5 minutes!" } }
  }
}
```

### List Watches
```
GET _watcher/watch
```

### Execute Watch Manually
```
POST _watcher/watch/failed_login_watch/_execute
```

---

## Mappings

### Update Mapping (Add Field)
```json
PUT /my-index/_mapping
{
  "properties": {
    "new_field": { "type": "keyword" }
  }
}
```

### Get Mapping
```
GET /my-index/_mapping
```

---

## Aliases

### Add Alias
```json
POST /_aliases
{
  "actions": [
    { "add": { "index": "my-index", "alias": "current-logs" } }
  ]
}
```

### Get Aliases
```
GET /_alias
```

---

## Index Settings

### Update Number of Replicas
```json
PUT /my-index/_settings
{
  "number_of_replicas": 2
}
```

---

## Common Cluster & Node Commands

### Cluster Health
```
GET /_cluster/health
```

### Node Info
```
GET /_nodes
```

---

## Search & Aggregation Example
```json
GET /logs-*/_search
{
  "size": 0,
  "aggs": {
    "top_users": {
      "terms": { "field": "user.keyword", "size": 3 }
    }
  }
}
```

---

## Delete Index
```
DELETE /old-index
```

---

# (continued) Kibana Dev Tools Cheatsheet (Elasticsearch Essentials)

## Snapshot & Restore

### Create Snapshot Repository (File System)
```json
PUT _snapshot/my_backup
{
  "type": "fs",
  "settings": {
    "location": "/mount/backups/es",
    "compress": true
  }
}
```

### Create Snapshot
```
PUT _snapshot/my_backup/snapshot_1?wait_for_completion=true
```

### Get Snapshot Status
```
GET _snapshot/my_backup/snapshot_1
```

### Restore Snapshot
```
POST _snapshot/my_backup/snapshot_1/_restore
```

---

## Rollup Jobs (Summarize Old Data)

### Create Rollup Job
```json
PUT _rollup/job/sales_rollup
{
  "index_pattern": "sales-*",
  "rollup_index": "rollup-sales",
  "cron": "0 0 0 * * ?",  
  "page_size": 1000,
  "groups": {
    "date_histogram": {
      "field": "timestamp",
      "interval": "1d",
      "delay": "7d",
      "time_zone": "Europe/Amsterdam"
    },
    "terms": {
      "fields": ["region", "product"]
    }
  },
  "metrics": [
    { "field": "amount", "metrics": ["sum", "max", "min", "avg"] }
  ]
}
```

### Get All Rollup Jobs
```
GET _rollup/job/_all
```

---

## Tasks & Maintenance

### List Running Tasks
```
GET _tasks
```

### Cancel Task
```
POST _tasks/task_id:ID/_cancel
```

### Force Merge Index (Optimize Segments)
```
POST /my-index/_forcemerge?max_num_segments=1
```

---

## Index Aliases Management (Zero-Downtime)

### Atomic Alias Switch
```json
POST /_aliases
{
  "actions": [
    { "remove": { "index": "my-index-v1", "alias": "live-index" } },
    { "add":    { "index": "my-index-v2", "alias": "live-index" } }
  ]
}
```

---

## Shrink Index

### Prepare Index for Shrink
```json
PUT /my-index/_settings
{
  "settings": {
    "index.blocks.write": true
  }
}
```

### Shrink Index
```
POST /my-index/_shrink/my-index-shrunk
```

---

## Field Capabilities
```
GET /my-index/_field_caps?fields=*
```

---

## Analyze Text
```json
POST /my-index/_analyze
{
  "field": "message",
  "text": "The quick brown fox jumps over the lazy dog."
}
```

---

## Bulk Operations
```json
POST /my-index/_bulk
{ "index": { "_id": "1" } }
{ "user": "alice", "timestamp": "2024-01-01T12:00:00", "message": "Hello!" }
{ "index": { "_id": "2" } }
{ "user": "bob", "timestamp": "2024-01-01T13:00:00", "message": "Hi!" }
```

---

## Update by Query
```json
POST /my-index/_update_by_query
{
  "script": {
    "source": "ctx._source.status = 'closed'",
    "lang": "painless"
  },
  "query": {
    "term": { "status": "open" }
  }
}
```

---

## Delete by Query
```json
POST /my-index/_delete_by_query
{
  "query": {
    "range": {
      "timestamp": { "lt": "now-365d/d" }
    }
  }
}
```

---

## Template Preview
```json
POST _index_template/_simulate
{
  "index_patterns": ["logs-2025-06-01"]
}
```

---

## Explain API
```json
GET /my-index/_explain/1
{
  "query": { "match": { "user": "alice" } }
}
```

---

## Search Templates

### Store Template
```json
POST _scripts/my_search_template
{
  "script": {
    "lang": "mustache",
    "source": {
      "query": {
        "match": {
          "user": "{{username}}"
        }
      }
    }
  }
}
```

### Use Template
```json
GET /my-index/_search/template
{
  "id": "my_search_template",
  "params": {
    "username": "alice"
  }
}
```

---

## Security

### Get User List
```
GET /_security/user
```

### Get Role List
```
GET /_security/role
```

---

## Miscellaneous
```
GET /my-index/_stats
GET /my-index/_settings
POST /my-index/_refresh
```

---

## Quick Reference: HTTP VERBS

- **GET** = Retrieve info
- **PUT** = Create/replace
- **POST** = Modify / actions
- **DELETE** = Remove