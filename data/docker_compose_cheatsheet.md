# Docker Compose Cheatsheet

## Basic Commands
- `docker-compose up -d` Start all services in the background  
- `docker-compose down` Stop and remove containers, networks, volumes  
- `docker-compose ps` List running containers  
- `docker-compose logs -f` Follow logs from all services  
- `docker-compose exec <service> <command>` Run a command in a running service  
- `docker-compose build` Build / rebuild services  
- `docker-compose pull` Pull service images  
- `docker-compose stop` Stop services  
- `docker-compose start` Start stopped services  

---

## Minimal Example: `docker-compose.yml`
```yaml
version: '3.8'
services:
  app:
    image: python:3.11
    volumes:
      - .:/code
    working_dir: /code
    command: python main.py
    ports:
      - "8080:8080"
    environment:
      - ENV=dev
    depends_on:
      - db

  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  pgdata:
```

---

## Useful Service Options
- **`depends_on`** Set start-order of services  
- **`environment`** Set environment variables (`KEY=value` or YAML map)  
- **`volumes`** Mount host / named volumes (`./host:/container`)  
- **`networks`** Attach to custom networks  
- **`restart`** Restart policy (`always`, `on-failure`)  
- **`command`** Override default command (`["python", "my_script.py"]`)  
- **`entrypoint`** Override entrypoint (`["bash", "entrypoint.sh"]`)  
- **`ports`** Expose ports (`"host:container"`)  

---

## Networking
- Services communicate via service name (e.g., `db:5432`)  
- A default network is created per Compose project  

---

## Managing Volumes & Networks
- **List volumes:** `docker volume ls`  
- **Remove unused volumes:** `docker volume prune`  
- **List networks:** `docker network ls`  
- **Remove unused networks:** `docker network prune`  

---

## Scaling Services
- `docker-compose up --scale app=3 -d` Start three instances of `app`  

---

## Compose File Version
- Use the latest supported version (e.g., `'3.8'` or `'2.4'`)  

---

## Validate Compose File
- `docker-compose config` Validate and view the merged config  

---

## Updating Containers
- **Pull latest images:** `docker-compose pull`  
- **Recreate with latest images:** `docker-compose up -d --force-recreate`  

---

## ℹ️ Wanneer gebruik je welk Compose-commando? (+ voorbeelden)
- `docker-compose up -d` → start stack voor lokaal dev/test.  
  Voorbeeld: `docker-compose up -d api db redis`.
- `docker-compose down -v` → netjes stoppen én volumes weggooien na experiment.  
- `docker-compose logs -f api` → streaming logs van één service bij debuggen.  
- `docker-compose exec db psql -U user` → snelle shell in servicecontainer.  
- `docker-compose build --no-cache` → rebuild als Dockerfile is aangepast.  
- `docker-compose pull && docker-compose up -d` → images bijwerken in CI of productie-rollout.  
- `docker-compose config` → valideren wat Compose daadwerkelijk gaat draaien (samengevoegd resultaat).  
- `docker-compose up --scale worker=3` → horizontaal schalen van stateless services.  
