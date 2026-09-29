FROM python:3.12-slim

# Execution sandbox - minimal image with runtime compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ python3 nodejs npm openjdk-11-jre-headless \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /sandbox

# Create non-root user
RUN useradd -m -u 1000 sandbox && chown -R sandbox /sandbox
USER sandbox

CMD ["sleep", "infinity"]
