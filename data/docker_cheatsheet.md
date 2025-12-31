# 🐳 Docker Essentials Cheatsheet

```bash
# 📌 Containers

# List running containers
docker ps

# List all containers (running + stopped)
docker ps -a

# Start a container
docker start <container_name>

# Stop a container
docker stop <container_name>

# Restart a container
docker restart <container_name>

# Remove a container
docker rm <container_name>

# Force remove a running container
docker rm -f <container_name>

# View logs (follow mode)
docker logs -f <container_name>

# Execute a command inside a running container (login)
docker exec -it <container_name> /bin/bash
# or
docker exec -it <container_name> /bin/sh
```

```bash
# 📌 Images

# List images
docker images

# Build image from Dockerfile
docker build -t <image_name>:<tag> .

# Remove an image
docker rmi <image_name>:<tag>

# Pull an image from Docker Hub
docker pull <image_name>:<tag>

# Push an image to registry
docker push <image_name>:<tag>
```

```bash
# 📌 Run Containers

# Run a container in background with port mapping
docker run -d --name <container_name> -p <host_port>:<container_port> <image_name>:<tag>

# Run with volume mounting
docker run -d \
  --name <container_name> \
  -v <host_path>:<container_path> \
  <image_name>:<tag>

# Run interactively with terminal
docker run -it <image_name>:<tag> /bin/bash

# Run with environment variables
docker run -d \
  --name <container_name> \
  -e KEY=value \
  <image_name>:<tag>
```

```bash
# 📌 Container & System Maintenance

# Show resource usage (top for Docker) – gebruik bij performance check
docker stats

# Show detailed info about a container – debugging env/ports/volumes
docker inspect <container_name>

# Prune unused containers, images, volumes, networks (careful!) – opruimen schijfruimte
docker system prune

# Remove dangling images only – opruimen build-afval
docker image prune
```

---

## ℹ️ Wanneer gebruik je welk commando? (+ voorbeelden)
- `docker ps -a` → snel zien wat er draait of faalde.  
  Voorbeeld: `docker ps -a --filter "status=exited"`.
- `docker logs -f <naam>` → live meekijken met app, bij crash-loop of foutmelding.  
  Voorbeeld: `docker logs -f my-api`.
- `docker exec -it <naam> /bin/bash` → container binnen voor inspectie of handmatige fixes.  
  Voorbeeld: `docker exec -it db psql -U postgres`.
- `docker run -d -p 8080:80 nginx` → quick test van image met port mapping.  
  Voorbeeld: `docker run -d --name web -p 8080:80 nginx:alpine`.
- `docker run -v $(pwd):/app node:20-alpine npm test` → eenmalige run met volume mount (build/test).  
- `docker start|stop <naam>` → herstart bestaande container zonder nieuwe image.  
- `docker rm -f <naam>` → force cleanup bij vastgelopen container.  
- `docker build -t myapp:dev .` → eigen image bouwen voor push of lokaal testen.  
- `docker system prune` → disk cleanup na veel builds/pulls (controleer eerst!).  
~~~markdown

Als je wilt, kan ik ook nog:
- een deel toevoegen over Docker networks,
- een voorbeeld met Docker Compose,
- of harde ezelbruggetjes erbij zodat het sneller blijft hangen.

Wat heb je zelf het meest nodig?
