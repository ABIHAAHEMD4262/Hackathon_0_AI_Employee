#!/bin/bash

#====================================================================
# AI Employee Setup Script
# This script sets up everything you need to run your AI Employee
#====================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  AI Employee Setup Script                     ║"
echo "║                     Version 1.0.0                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running from project root
if [ ! -f "CLAUDE.md" ]; then
    print_error "Please run this script from the AI_Employee project root directory"
    exit 1
fi

echo ""
echo "Step 1: Checking Prerequisites"
echo "─────────────────────────────────────"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 is required but not installed"
    print_info "Install Python 3.10+ from https://python.org"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    print_status "pip3 found"
else
    print_warning "pip3 not found, trying pip..."
    if ! command -v pip &> /dev/null; then
        print_error "pip is required but not installed"
        exit 1
    fi
fi

# Check Claude Code
if command -v claude &> /dev/null; then
    print_status "Claude Code CLI found"
else
    print_warning "Claude Code CLI not found"
    print_info "Install with: npm install -g @anthropic-ai/claude-code"
    print_info "Or download from: https://claude.ai/download"
fi

# Check Node.js (for MCP servers)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_warning "Node.js not found (optional, needed for MCP servers)"
    print_info "Install from: https://nodejs.org"
fi

# Check Git
if command -v git &> /dev/null; then
    print_status "Git found"
else
    print_warning "Git not found (optional)"
fi

echo ""
echo "Step 2: Creating Virtual Environment"
echo "─────────────────────────────────────"

if [ -d "venv" ]; then
    print_info "Virtual environment already exists"
else
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

echo ""
echo "Step 3: Installing Python Dependencies"
echo "─────────────────────────────────────"

pip install --upgrade pip > /dev/null
pip install -r requirements.txt
print_status "Python dependencies installed"

echo ""
echo "Step 4: Setting Up Directory Structure"
echo "─────────────────────────────────────"

# Create all necessary directories
directories=(
    "nerve_center/inbox"
    "nerve_center/processed"
    "nerve_center/logs"
    "nerve_center/skills"
    "nerve_center/templates"
    "nerve_center/drafts"
    "nerve_center/finances/invoices"
    "nerve_center/briefings"
    "config/credentials"
    "tests"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
done
print_status "Directory structure created"

echo ""
echo "Step 5: Creating Configuration Files"
echo "─────────────────────────────────────"

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# AI Employee Environment Variables
# Copy this file to .env and fill in your values

# Claude API (if not using Claude Code CLI)
ANTHROPIC_API_KEY=your_api_key_here

# Gmail API (optional)
GMAIL_CREDENTIALS_PATH=config/credentials/gmail_credentials.json

# Calendar API (optional)
CALENDAR_CREDENTIALS_PATH=config/credentials/calendar_credentials.json

# Notification settings
NOTIFICATION_EMAIL=your-email@example.com
NOTIFICATION_WEBHOOK_URL=

# System settings
LOG_LEVEL=INFO
MAX_API_CALLS_PER_HOUR=100
EOF
    print_status "Created .env.example"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Environment
.env
venv/
__pycache__/
*.pyc

# Credentials - NEVER commit these
config/credentials/
*.json
!package.json
!config/mcp_config.example.json

# Logs
nerve_center/logs/*
!nerve_center/logs/.gitkeep

# Personal data
nerve_center/inbox/*
!nerve_center/inbox/.gitkeep
nerve_center/processed/*
!nerve_center/processed/.gitkeep
nerve_center/drafts/*
nerve_center/finances/*
nerve_center/briefings/*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
    print_status "Created .gitignore"
fi

# Create MCP config example
if [ ! -f "config/mcp_config.example.json" ]; then
    cat > config/mcp_config.example.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-filesystem", "./nerve_center"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-server-memory"]
    }
  }
}
EOF
    print_status "Created MCP config example"
fi

# Create placeholder files to preserve git structure
touch nerve_center/logs/.gitkeep
touch nerve_center/inbox/.gitkeep
touch nerve_center/processed/.gitkeep
touch config/credentials/.gitkeep

echo ""
echo "Step 6: Verifying Installation"
echo "─────────────────────────────────────"

# Try to import the main module
if python3 -c "import asyncio; print('asyncio OK')" 2>/dev/null; then
    print_status "Python asyncio available"
else
    print_error "Python asyncio not available"
fi

# Check if orchestrator can be loaded
if python3 -c "import sys; sys.path.insert(0, 'src'); exec(open('src/orchestrator.py').read().split('if __name__')[0])" 2>/dev/null; then
    print_status "Orchestrator module loads correctly"
else
    print_warning "Orchestrator has import warnings (may be missing optional dependencies)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}Setup Complete!${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Next Steps:"
echo "─────────────────────────────────────"
echo "1. Copy .env.example to .env and fill in your values:"
echo "   cp .env.example .env"
echo ""
echo "2. Customize your Company Handbook:"
echo "   Edit nerve_center/Company_Handbook.md"
echo ""
echo "3. Set your Business Goals:"
echo "   Edit nerve_center/Business_Goals.md"
echo ""
echo "4. (Optional) Set up Gmail API credentials:"
echo "   - Go to Google Cloud Console"
echo "   - Enable Gmail API"
echo "   - Download credentials to config/credentials/gmail_credentials.json"
echo ""
echo "5. Start the AI Employee:"
echo "   source venv/bin/activate"
echo "   python src/orchestrator.py"
echo ""
echo "6. Test with a sample file:"
echo "   echo 'Test task' > nerve_center/inbox/test.txt"
echo ""
echo -e "${BLUE}Documentation:${NC} See docs/QUICKSTART.md"
echo -e "${BLUE}Issues:${NC} https://github.com/your-repo/ai-employee/issues"
echo ""
