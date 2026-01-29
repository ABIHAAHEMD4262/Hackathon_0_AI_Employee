# Cloud Deployment Guide - Platinum Tier

Deploy your AI Employee to run 24/7 on a cloud VM.

---

## Quick Start

### 1. Choose a Cloud Provider

| Provider | Free Tier | Recommended |
|----------|-----------|-------------|
| **Oracle Cloud** | 2 VMs free forever | ✅ Best for free |
| AWS EC2 | 750 hrs/month (1 year) | Good |
| Google Cloud | $300 credit | Good |
| DigitalOcean | $200 credit | Simple |
| Railway | $5/month free | Easiest |

---

## Option 1: Oracle Cloud (FREE Forever)

### Step 1: Create Account
1. Go to: https://www.oracle.com/cloud/free/
2. Sign up for free tier
3. Choose your home region

### Step 2: Create VM
1. Go to Compute → Instances → Create Instance
2. Choose:
   - Shape: VM.Standard.E2.1.Micro (Always Free)
   - Image: Ubuntu 22.04
   - Memory: 1GB (free tier)
3. Download SSH key
4. Create instance

### Step 3: Connect & Setup
```bash
# Connect to your VM
ssh -i <your-key.pem> ubuntu@<your-vm-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Logout and login again for docker permissions
exit
```

### Step 4: Deploy AI Employee
```bash
# Connect again
ssh -i <your-key.pem> ubuntu@<your-vm-ip>

# Clone your vault (or upload)
git clone https://github.com/YOUR_USERNAME/ai-employee-vault.git
cd ai-employee-vault/cloud

# Create .env file
cat > .env << EOF
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
EOF

# Start AI Employee
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

---

## Option 2: Railway (Easiest)

### Step 1: Setup
1. Go to: https://railway.app/
2. Sign up with GitHub
3. Click "New Project"

### Step 2: Deploy
1. Select "Deploy from GitHub repo"
2. Choose your AI Employee repository
3. Railway auto-detects Dockerfile

### Step 3: Configure
1. Go to Variables tab
2. Add:
   - `EMAIL_USER`
   - `EMAIL_PASS`
   - `VAULT_PATH=/app/vault`

### Step 4: Done!
Railway handles everything automatically.

---

## Option 3: Manual Docker Deployment

### On Any Linux Server

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com | sh

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/ai-employee-vault.git
cd ai-employee-vault

# 3. Create .env
cp .env.example .env
nano .env  # Edit with your credentials

# 4. Build and run
cd cloud
docker-compose up -d --build

# 5. View logs
docker-compose logs -f orchestrator
```

---

## Vault Syncing

### Option A: Git Sync (Recommended)
Sync your cloud vault with local using Git.

```bash
# On cloud VM
cd /path/to/vault
git init
git remote add origin https://github.com/YOU/ai-employee-vault.git
git pull origin main

# Setup auto-sync (cron)
crontab -e
# Add: */5 * * * * cd /path/to/vault && git pull && git add -A && git commit -m "sync" && git push
```

### Option B: Syncthing
Real-time sync between cloud and local.

```bash
# Install on cloud VM
curl -s https://syncthing.net/release-key.txt | sudo apt-key add -
echo "deb https://apt.syncthing.net/ syncthing release" | sudo tee /etc/apt/sources.list.d/syncthing.list
sudo apt update && sudo apt install syncthing

# Start syncthing
syncthing
# Access web UI at http://your-vm-ip:8384
```

---

## Security Checklist

- [ ] Never commit .env files to Git
- [ ] Use app passwords, not main passwords
- [ ] Keep SSH keys secure
- [ ] Enable firewall (only allow SSH, HTTP/HTTPS)
- [ ] Regular security updates

### Firewall Setup (Oracle Cloud)
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (if using web dashboard)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## Monitoring

### Check Service Health
```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f orchestrator
```

### Setup Alerts (Optional)
Use Healthchecks.io for free monitoring:

1. Go to: https://healthchecks.io/
2. Create a check
3. Add to your cron:
```bash
# Ping healthchecks every 5 minutes
*/5 * * * * curl -fsS --retry 3 https://hc-ping.com/YOUR-UUID-HERE
```

---

## Cost Estimates

| Provider | Monthly Cost |
|----------|-------------|
| Oracle Cloud Free | $0 |
| Railway Starter | $5 |
| AWS t2.micro | ~$8 |
| DigitalOcean Basic | $6 |

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs orchestrator

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Gmail auth issues
1. Enable 2FA on Gmail
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use App Password in EMAIL_PASS

### Out of disk space
```bash
# Clean up Docker
docker system prune -a

# Check disk usage
df -h
```

---

## What Runs on Cloud vs Local

### Cloud Agent (24/7)
- ✅ Email monitoring (read only)
- ✅ LinkedIn monitoring
- ✅ Draft creation
- ✅ Task queuing
- ❌ Sending emails (needs approval)
- ❌ Posting to social (needs approval)

### Local Agent (When you're online)
- ✅ Approving/rejecting drafts
- ✅ Sending approved emails
- ✅ Posting approved content
- ✅ Sensitive operations
- ✅ Banking/payments

This separation ensures:
1. Cloud can work 24/7 on safe tasks
2. Sensitive actions only happen when you approve
3. Your credentials for sending stay local

---

*Platinum Tier Cloud Deployment Guide*
*AI Employee Hackathon*
