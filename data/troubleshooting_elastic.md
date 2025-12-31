```md
# 🛠️ Elasticsearch 8.x Dev Tools Troubleshooting Cheatsheet

## ✅ 1. Cluster Health
Check overall health (green/yellow/red)
```json
GET _cluster/health
```

---

## 📦 2. Cluster State
View cluster metadata and shard routing
```json
GET _cluster/state
```

---

## 🕒 3. Pending Tasks
List pending cluster tasks
```json
GET _cluster/pending_tasks
```

---

## 🧠 4. Node Stats
Detailed CPU, memory, disk, and thread stats
```json
GET _nodes/stats
```

---

## 📊 5. Index Stats
Stats per index or for all
```json
GET /<index_name>/_stats
# or all indices:
GET /_stats
```

---

## 🧩 6. Shard Allocation
Check current shard distribution and status
```json
GET _cat/shards?v
```

---

## ❓ 7. Explain Shard Allocation
Why a shard is unassigned
```json
GET _cluster/allocation/explain
```

---

## 🔍 8. Hot Threads (Search Performance)
Find slow search threads
```json
GET _nodes/hot_threads?threads=3&type=search
```

---

## ♻️ 9. Index Recovery Status
Track ongoing shard recovery
```json
GET /_recovery
```

---

## 📁 10. Logs or Watcher Indices
Query internal logs (e.g., Logstash or monitoring)
```json
GET /.logstash-*/_search
```

---

# 🔧 Shard Troubleshooting Commands

## 11. Check Index Settings (Replica Count)
```json
GET /<index_name>/_settings
```

## 12. Change Number of Replicas
```json
PUT /<index_name>/_settings
{
  "index": {
    "number_of_replicas": 1
  }
}
```

---

## 13. Manually Allocate Stale Primary Shard
⚠️ Accepts potential data loss!
```json
POST _cluster/reroute
{
  "commands": [
    {
      "allocate_stale_primary": {
        "index": "<index_name>",
        "shard": 0,
        "node": "<node_name>",
        "accept_data_loss": true
      }
    }
  ]
}
```

---

## 14. Retry Failed Shard Allocations
```json
POST _cluster/reroute?retry_failed
```

---

## 15. Force Merge Index (Fix Corruption)
```json
POST /<index_name>/_forcemerge?max_num_segments=1
```

---

## 16. Check Index Status (Open/Closed)
```json
GET _cat/indices?v
```

## 17. Reopen Closed Index
```json
POST /<index_name>/_open
```

---

## 18. Adjust Disk Watermarks to Allow Allocation
```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.disk.watermark.low": "10gb",
    "cluster.routing.allocation.disk.watermark.high": "5gb",
    "cluster.routing.allocation.disk.watermark.flood_stage": "1gb"
  }
}
```

---

## 19. Delete Corrupted Index (Last Resort)
```json
DELETE /<index_name>
```

---

## 20. Logs: Check Elasticsearch Node Logs (Linux shell)
```bash
journalctl -u elasticsearch --no-pager | tail -n 50
# OR if not using systemd:
tail -f /var/log/elasticsearch/elasticsearch.log
```

---

## ℹ️ Wanneer gebruik je welke call?
- `GET _cluster/health` → eerste check bij issues (groen/geel/rood + pending tasks).  
- `GET _cluster/state` → routing/metadata; nuttig bij shard misallocaties.  
- `GET _cluster/allocation/explain` → waarom shard niet toegewezen.  
- `GET _cat/shards?v` → snel overzicht shard status/per node.  
- `GET _nodes/stats` → CPU/mem/FS per node.  
- `GET _nodes/hot_threads?type=search` → trage queries of heavy GC vinden.  
- `GET _recovery` → voortgang van shard recovery na restart.  
- `PUT _cluster/settings` (watermarks) → opschalen/ruimte forceren bij disk pressure.  
- `POST _cluster/reroute?retry_failed` → opnieuw proberen na fix.  
- `POST _cluster/reroute` met `allocate_stale_primary` → laatste redmiddel, accepteert mogelijk dataverlies.  
- `DELETE /<index>` → alleen als index echt corrupt/overbodig is.  

```
