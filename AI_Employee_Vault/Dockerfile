# AI Employee - Docker Configuration
# Platinum Tier: Cloud Deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for dashboard
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create vault directories
RUN mkdir -p Inbox Needs_Action Approvals Approved Rejected Done Logs Tasks Plans Business .queue

# Install dashboard dependencies
WORKDIR /app/dashboard
RUN npm install --production

# Build dashboard
RUN npm run build

# Back to app root
WORKDIR /app

# Expose ports
EXPOSE 3001 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV VAULT_PATH=/app
ENV NODE_ENV=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/api/health || exit 1

# Start script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
