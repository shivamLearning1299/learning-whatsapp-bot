# Daily interview-prep WhatsApp bot

Sends yourself one interview-prep concept a day over WhatsApp, generated fresh
by Claude, covering networking/OS/AI topics — runs automatically via GitHub
Actions, no server to manage.

## How it works

1. GitHub Actions triggers `send_daily_concept.py` on a daily cron schedule.
2. The script reads `topics.json`, picks the next topic in rotation.
3. Calls the Anthropic API to generate a short, interviewer-style explanation
   (with prompt caching on the system prompt to reduce cost on repeated runs).
4. Sends the message via Twilio's WhatsApp API.
5. Advances the rotation pointer in `topics.json` and commits it back to the repo.

## One-time setup

### 1. Twilio WhatsApp sandbox (free)

1. Create a free Twilio account at twilio.com.
2. Go to Console → Messaging → Try it out → Send a WhatsApp message.
3. Follow the prompt to join the sandbox — you'll send a "join <code>" message
   from your own WhatsApp to Twilio's sandbox number (+14155238886). This links
   your number to the sandbox for testing.
4. Note your **Account SID** and **Auth Token** from the Twilio console dashboard.

Note: the sandbox requires you to re-join every 72 hours of inactivity, and
messages only work between your verified number and the sandbox — fine for
personal use, but if you want a permanent production number later, Twilio
requires WhatsApp Business API approval (a longer process, not needed here).

### 2. Anthropic API key

Get one from console.anthropic.com if you don't already have one for other projects.

### 3. Repo secrets

In your GitHub repo: Settings → Secrets and variables → Actions → New repository secret.
Add all five:
- `ANTHROPIC_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM` → `whatsapp:+14155238886` (sandbox number)
- `MY_WHATSAPP_TO` → `whatsapp:+91XXXXXXXXXX` (your number, E.164 format)

### 4. Push this repo to GitHub

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

### 5. Test it manually before waiting for the cron

Go to the repo's Actions tab → "Daily interview-prep WhatsApp message" →
Run workflow (this uses the `workflow_dispatch` trigger). Check your WhatsApp
within a minute or two.

## Local testing (optional)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in real values
export $(cat .env | xargs)   # loads env vars into your shell
python send_daily_concept.py
```

## Customizing the send time

Edit the `cron` line in `.github/workflows/daily-concept.yml`. Cron runs in
UTC — for IST, subtract 5:30 from your target time. E.g. for 8:00 AM IST,
use `30 2 * * *`.

## Adding/editing topics

Just edit `topics.json` — add new strings to the `topics` array. The rotation
pointer (`next_index`) wraps around automatically once it reaches the end, so
the list repeats for reinforcement.

## Notes on cost

- Anthropic: each run is a tiny call (~400 output tokens max) — cost is
  negligible even at 365 runs/year.
- Twilio sandbox: free for testing/personal use.
- GitHub Actions: well within the free tier for a once-daily job.
