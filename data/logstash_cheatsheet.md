# Logstash Cheatsheet

A quick reference for creating Logstash pipelines, the most-used filter commands, and managing Logstash via the API. Suitable for copy-pasting into your documentation or Obsidian.

---

## Basic Pipeline Structure

```conf
input {
  beats {
    port => 5044
  }
  # Or: file, http, jdbc, kafka, etc.
}

filter {
  # Filters go here
}

output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    index => "my-index-%{+YYYY.MM.dd}"
    user => "elastic"
    password => "changeme"
    ssl => true
    cacert => "/etc/logstash/certs/ca.crt"
  }
  # stdout { codec => rubydebug } # For debugging
}
```

---

## Most Common Filters

### 1. **grok**
Extracts structured fields from text using patterns.

```conf
filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
    # Custom: match => { "message" => "user=%{WORD:user} id=%{NUMBER:id}" }
  }
}
```

### 2. **date**
Parses date/time strings into the `@timestamp` field.

```conf
filter {
  date {
    match => ["timestamp", "yyyy-MM-dd HH:mm:ss,SSS"]
    timezone => "Europe/Amsterdam"
    target => "@timestamp"
  }
}
```

### 3. **mutate**
General transformations: rename, remove, convert, update, etc.

```conf
filter {
  mutate {
    rename   => { "oldField" => "newField" }
    remove_field => ["unneeded_field"]
    convert  => { "status_code" => "integer" }
    update   => { "log_level" => "INFO" }
    gsub     => [
      "message", "\d{4}-\d{2}-\d{2}", "" # Remove date patterns
    ]
  }
}
```

### 4. **json**
Parses JSON-formatted strings.

```conf
filter {
  json {
    source => "message"
    target => "parsed_json"
  }
}
```

### 5. **csv**
Parses CSV lines into fields.

```conf
filter {
  csv {
    separator => ","
    columns => ["id", "username", "email"]
  }
}
```

### 6. **geoip**
Adds geolocation info from an IP address.

```conf
filter {
  geoip {
    source => "client_ip"
    target => "geoip"
  }
}
```

### 7. **split**
Splits an array or string into multiple events or fields.

```conf
filter {
  split {
    field => "tags"
  }
}
```

### 8. **clone**
Duplicates events (useful for sending to multiple outputs).

```conf
filter {
  clone {
    clones => ["clone1", "clone2"]
  }
}
```

### 9. **aggregate**
Accumulates data across multiple events (advanced).

```conf
filter {
  aggregate {
    task_id => "%{some_id}"
    code => "
      map['count'] ||= 0
      map['count'] += 1
    "
    push_map_as_event_on_timeout => true
    timeout => 120
  }
}
```

---

## Useful Output Plugins

### **Elasticsearch**

```conf
output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    index => "logstash-%{+YYYY.MM.dd}"
  }
}
```

### **File**

```conf
output {
  file {
    path => "/var/log/logstash/output.log"
  }
}
```

### **Stdout for Debug**

```conf
output {
  stdout { codec => rubydebug }
}
```

---

## Managing Pipelines

- **Pipeline config directory:** `/etc/logstash/conf.d/`
- **Multiple pipelines:** `/etc/logstash/pipelines.yml`

```yaml
# pipelines.yml example
- pipeline.id: main
  path.config: "/etc/logstash/conf.d/*.conf"
- pipeline.id: secondary
  path.config: "/etc/logstash/conf.d/secondary.conf"
```

---

## Logstash REST API Calls

> Logstash must be started with the `--http.port` option (default: `9600`) for API access.

### Get Logstash Node Info

```bash
curl -X GET http://localhost:9600/
```

### Get Logstash Stats

```bash
curl -X GET http://localhost:9600/_node/stats
```

### Get Pipeline State

```bash
curl -X GET http://localhost:9600/_node/pipelines
```

### Get Pipeline State by ID

```bash
curl -X GET http://localhost:9600/_node/pipelines/<pipeline_id>
```

### Get Plugins Info

```bash
curl -X GET http://localhost:9600/_node/plugins
```

### Reload Pipeline (if enabled)

```bash
curl -X POST http://localhost:9600/_node/pipelines/<pipeline_id>/reload
```

### Check Hot Threads

```bash
curl -X GET http://localhost:9600/_node/hot_threads
```

---

## CLI Commands

```bash
# Test a pipeline config
logstash -f /etc/logstash/conf.d/my-pipeline.conf --config.test_and_exit

# Reload Logstash
sudo systemctl restart logstash

# View Logstash logs
journalctl -u logstash -f
```

---

## Tips

- Use `stdout { codec => rubydebug }` for debugging filter output.
- Comment out outputs during filter debugging to avoid spamming Elasticsearch.
- Use conditionals to process specific events:
```conf
filter {
  if "error" in [tags] {
    mutate { add_field => { "alert" => "true" } }
  }
}
```

---

## ℹ️ Wanneer gebruik je welke filter/CLI? (+ voorbeelden)
- **grok** → logregels parsen naar velden. Voorbeeld: `%{COMBINEDAPACHELOG}` voor webserverlogs.  
- **date** → timestamp normaliseren naar `@timestamp`; altijd doen voordat je naar ES schrijft.  
- **mutate convert** → types fixen voor aggregaties (bijv. `status_code` naar integer).  
- **json** → wanneer `message` al JSON is, parse het eerst.  
- **csv** → simpele CSV/TSV logformaten zonder custom code.  
- **geoip** → IP naar locatie voor dashboards (Kibana).  
- **split** → events dupliceren per item in array.  
- **clone** → zelfde event naar meerdere outputs (bijv. ES + file).  
- **aggregate** → sessie/transaction counter over meerdere events (geavanceerd).  
- `logstash -f ... --config.test_and_exit` → config check vóór deploy.  
- `journalctl -u logstash -f` → live Logstash service logs bij fouten.  

---

> **References:**  
> Logstash Filter Plugins: https://www.elastic.co/guide/en/logstash/current/filter-plugins.html  
> Logstash Monitoring API: https://www.elastic.co/guide/en/logstash/current/monitoring-logstash.html
