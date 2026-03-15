# Behavior profiles

## cpu_periodic

Simulates scheduled compute abuse or opportunistic mining-like bursts.

Pattern:
- idle period
- CPU busy-loop burst
- idle period

## memory_random

Simulates transient staging, leak-like growth, or irregular buffering.

Pattern:
- random sleep
- allocate memory block
- hold briefly
- release

## beacon_periodic

Simulates low-volume regular callbacks to a controlled service.

Pattern:
- fixed interval HTTP GET to the sink
- low bytes transferred
- stable cadence

## exfil_burst

Simulates short high-concurrency transfer bursts to a controlled sink.

Pattern:
- idle
- N concurrent HTTP GET requests for small blobs
- idle

This is safe because the sink is controlled and the payloads are synthetic.

## io_staging

Simulates temporary file staging and churn.

Pattern:
- create temp files
- append/rotate content
- delete after hold period

## mixed_intrusion

Simulates a multi-phase incident-like sequence using only benign operations:
- beaconing
- CPU burst
- memory staging
- temp file churn
- network burst

This profile is useful when validating whether a monitoring platform can correlate multiple weak signals into a stronger story.
