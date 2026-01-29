# AI Employee Cloud Deployment
# Platinum Tier - Runs 24/7 on cloud VM

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy AI Employee code
COPY watchers/ ./watchers/
COPY mcp_servers/ ./mcp_servers/
COPY scripts/ ./scripts/
COPY Skills/ ./Skills/

# Create vault structure
RUN mkdir -p vault/Inbox \
    vault/Needs_Action/Emails \
    vault/Needs_Action/LinkedIn \
    vault/In_Progress \
    vault/Pending_Approval \
    vault/Approved \
    vault/Done \
    vault/Rejected \
    vault/Failed \
    vault/Quarantine \
    vault/Plans \
    vault/Clients \
    vault/Business/CEO_Briefings \
    vault/Marketing/LinkedIn_Queue \
    vault/Marketing/Social_Queue \
    vault/Logs/Audit \
    vault/Logs/Daily \
    vault/Logs/Errors \
    vault/Logs/System

# Copy static vault files
COPY Dashboard.md vault/
COPY Company_Handbook.md vault/
COPY ARCHITECTURE.md vault/

# Environment variables (override at runtime)
ENV VAULT_PATH=/app/vault
ENV CHECK_INTERVAL=60
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the orchestrator
CMD ["python", "watchers/orchestrator.py", "/app/vault"]
