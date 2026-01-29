# Welcome to AI Employee! 🤖

## How to Open This Vault in Obsidian

### Step 1: Install Obsidian
1. Download Obsidian from [obsidian.md](https://obsidian.md)
2. Install and launch Obsidian

### Step 2: Open This Vault
1. In Obsidian, click **"Open folder as vault"**
2. Navigate to: `G:\Hackathon_0\AI_Employee\AI_Employee_Vault`
3. Select the `AI_Employee_Vault` folder
4. Click **"Open"**

### Step 3: Trust the Vault
- When prompted, click **"Trust author and enable plugins"**
- This enables the core plugins for better navigation

---

## First Steps After Opening

### 1. Read the Dashboard
- Open [[Dashboard]] to see system status
- All hackathon features are marked as complete

### 2. Explore the Structure
- Look at the left sidebar to see all folders
- Key folders:
  - `Needs_Action/` - Where incoming tasks appear
  - `Approvals/` - Where your drafts go
  - `Done/` - Completed tasks

### 3. Start the Web Dashboard
```bash
cd AI_Employee_Vault/dashboard
npm install  # First time only
npm run dev
```
Then open: http://localhost:3000

---

## Quick Navigation

| File | Purpose |
|------|---------|
| [[Dashboard]] | System status and metrics |
| [[Company_Handbook]] | Your business rules |
| [[DOCUMENTATION]] | Complete technical guide |
| [[ARCHITECTURE]] | System architecture |

---

## Troubleshooting

### EACCES Permission Denied Error
This happens when Windows/Obsidian can't access files. Try these solutions:

**Solution 1: Run Permission Fixer**
1. Double-click `FIX_OBSIDIAN_PERMISSIONS.bat` in this folder
2. If needed, right-click → "Run as administrator"
3. Try opening the vault again

**Solution 2: Copy to Documents**
1. Copy the entire `AI_Employee_Vault` folder to `Documents`
2. Open from the new location in Obsidian

**Solution 3: Manual Permission Fix (Windows)**
1. Right-click on `AI_Employee_Vault` folder
2. Properties → Security → Edit
3. Add your user with "Full control"
4. Apply to all subfolders

### Obsidian Shows Empty or Error
1. Make sure you selected `AI_Employee_Vault` folder (not AI_Employee)
2. Check that `.obsidian` folder exists inside the vault
3. Try: Close Obsidian → Delete `.obsidian` folder → Reopen vault

### Files Don't Load
1. File → Settings → Editor → Check "Show frontmatter"
2. Restart Obsidian

### Links Not Working
- Internal links use `[[filename]]` format
- Make sure the file exists in the vault

---

## Need Help?

- Read [[DOCUMENTATION]] for complete guide
- Run tests: `python test_all_features.py`
- Check system: `python run.py --status`

---

*Welcome to your AI Employee! 🎉*
