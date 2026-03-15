# Docker and image publishing

This repository publishes two images to GitHub Container Registry by default:

- `ghcr.io/agentic2026/incident-lab-simulator`
- `ghcr.io/agentic2026/incident-lab-sink`

Both images are built from the same codebase.

## Local build

```bash
docker build -f docker/simulator.Dockerfile -t incident-lab-simulator:dev .
docker build -f docker/sink.Dockerfile -t incident-lab-sink:dev .
```

## Compose

```bash
docker compose up -d --build
```

## Registry behavior

The GitHub Actions workflow:
- builds on pull requests to validate Dockerfiles
- publishes multi-arch images on pushes to `main`, tags, or manual dispatch
- uses GHCR and the repository `GITHUB_TOKEN`
