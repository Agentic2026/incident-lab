# incident-lab

A safe, configurable container lab for simulating suspicious runtime patterns that security monitoring platforms can observe and triage.

The project is intentionally non-malicious. It does **not** contain exploit code, credential theft, persistence, or real exfiltration logic. Instead, it simulates observable behaviors such as:

- CPU burst patterns
- memory pressure and release
- periodic beacon-like HTTP traffic
- bursty high-concurrency network transfer to a controlled sink
- temporary filesystem staging and churn
- multi-phase mixed behavior that looks more incident-like than a single metric spike

This repository is independent of Manifold. You can run it standalone, or attach its containers to the same Docker network as your monitoring stack.

## Images

This repo publishes two Docker images from the same Python project:

- `ghcr.io/<owner>/incident-lab-simulator`
- `ghcr.io/<owner>/incident-lab-sink`

The simulator image runs configurable profiles. The sink image is a safe internal HTTP target that serves small payloads so you can generate repeatable network activity without touching third-party infrastructure.

## Quick start

### Local with uv

```bash
uv sync
uv run python -m incident_lab --help
uv run python -m incident_lab
```

### Docker Compose

```bash
docker compose up -d --build
```

This starts:
- one sink service
- several simulator services with distinct profiles

## Profiles

- `cpu_periodic`
- `memory_random`
- `beacon_periodic`
- `exfil_burst`
- `io_staging`
- `mixed_intrusion`

See [docs/BEHAVIORS.md](docs/BEHAVIORS.md) for details.

## Repository layout

- `src/incident_lab/` Python package
- `docker/` Dockerfiles for simulator and sink images
- `.github/workflows/` CI and image publishing workflows
- `docker-compose.yml` local demo stack
- `docs/` operational docs and behavior notes

## Safety model

This lab is for benign simulation only.

It intentionally avoids:
- exploit payloads
- credential use or exfiltration of real secrets
- persistence or privilege escalation
- scanning other networks
- malware-like code

The network burst profile targets a controlled sink by default. Override the target only in environments you own and control.
