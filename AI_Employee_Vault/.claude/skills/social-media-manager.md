# Social Media Manager Skill

## Description
Manages social media presence across LinkedIn, Twitter, Facebook, and Instagram.

## Triggers
- Scheduled post time reached
- User requests social media post
- Weekly summary generation

## Capabilities
1. **Draft Posts**: Create engaging social media content
2. **Schedule Posts**: Queue posts for optimal timing
3. **Analytics**: Generate engagement summaries
4. **Cross-Platform**: Support multiple platforms

## Supported Platforms
- LinkedIn (professional content)
- Twitter/X (short updates)
- Facebook (general posts)
- Instagram (visual content)

## Commands

### Draft a LinkedIn post
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python mcp_servers/social_media_server.py --platform linkedin --action draft
```

### Generate weekly summary
```bash
python mcp_servers/social_media_server.py --action summary
```

## File Locations
- Draft posts: `Approvals/`
- Scheduled posts: `Tasks/social_queue.md`
- Analytics: `Business/social_analytics.md`

## Post Templates

### LinkedIn (Professional)
- Industry insights
- Project updates
- Career milestones
- Thought leadership

### Twitter (Concise)
- Quick updates
- Thread topics
- Engagement posts
- News commentary

## Rules
1. All posts require human approval before publishing
2. LinkedIn: Professional tone, 1-3 posts per week
3. Twitter: Casual but professional, up to 3 posts per day
4. Include relevant hashtags
5. Optimal posting times: 9 AM, 12 PM, 5 PM
