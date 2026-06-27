# Privacy and Data Principles

## 1. Public repo must stay sanitized

Do not commit private deployment notes, raw sensitive disaster data, `.env` files, API keys, SSH material, Kaggle credentials, Tailscale-only details, private model artifacts, or local IDE state.

## 2. Uploaded data should not persist by default

The Live Gemma preview should decode, sanitize, and delete uploads after each request. It should return bounded JSON and avoid raw stack traces or raw model output.

## 3. Logs are operational, not evidence dumps

Generated logs should avoid private field notes, uploaded images, secrets, and model credentials. Benchmark logs belong under ignored `logs/` unless intentionally sanitized and promoted.

## 4. Public docs describe patterns, not private infrastructure

Public deployment docs should describe safe localhost/reverse-proxy/container patterns. Private repos may document actual hostnames and operator runbooks.

## 5. Model/data caches are not repo content

Large model weights, data shards, extracted images, generated results, and local caches should remain outside git unless explicitly sanitized and intentionally published.
