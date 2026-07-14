"""
Daily interview-prep WhatsApp sender.

Flow:
1. Read topics.json — an ordered list of topics + a pointer to "next index"
2. Call Anthropic API to generate a short, interviewer-style explanation
3. Send it via Twilio's WhatsApp API
4. Advance the pointer and write topics.json back (committed by the GitHub Action)

Run via: python send_daily_concept.py
Requires env vars: ANTHROPIC_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
                    TWILIO_WHATSAPP_FROM, MY_WHATSAPP_TO
"""

import json
import os
import sys
from datetime import datetime

import anthropic
from twilio.rest import Client

TOPICS_FILE = "topics.json"


def load_topics():
    with open(TOPICS_FILE, "r") as f:
        return json.load(f)


def save_topics(data):
    with open(TOPICS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_next_topic(data):
    idx = data["next_index"] % len(data["topics"])
    topic = data["topics"][idx]
    data["next_index"] = idx + 1
    return topic


def generate_explanation(topic: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # This system prompt is identical on every single run (365 days/year).
    # Marking it with cache_control means Anthropic caches it server-side after
    # the first call, so every subsequent day only pays full price for the tiny
    # "Topic: X" user message — the long instructions are billed at the much
    # cheaper cache-read rate instead of full input-token price every time.
    system_prompt = [
        {
            "type": "text",
            "text": (
                "You write short daily interview-prep messages for a WhatsApp bot. "
                "The reader is a software engineer with 4+ years experience (PHP/Node/Python) "
                "prepping for Senior SDE / AI Engineer interviews. "
                "For the given topic: "
                "1) Explain the core concept in under 90 words, the way a senior interviewer "
                "would want it explained — precise, no fluff, focused on WHY not just WHAT. "
                "2) Add one line: 'Likely follow-up:' with a single probing question an "
                "interviewer might ask next on this topic. "
                "Keep total output under 120 words. No markdown headers, no bullet lists — "
                "this is a WhatsApp message, plain text only, short paragraphs."
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Topic: {topic}"}],
    )

    # Optional: log cache performance so you can see savings kick in after day 1
    usage = message.usage
    print(
        f"tokens — input: {usage.input_tokens}, "
        f"cache_created: {getattr(usage, 'cache_creation_input_tokens', 0)}, "
        f"cache_read: {getattr(usage, 'cache_read_input_tokens', 0)}, "
        f"output: {usage.output_tokens}"
    )

    return message.content[0].text.strip()


def send_whatsapp(body: str):
    client = Client(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    client.messages.create(
        from_=os.environ["TWILIO_WHATSAPP_FROM"],   # e.g. "whatsapp:+14155238886"
        to=os.environ["MY_WHATSAPP_TO"],             # e.g. "whatsapp:+91XXXXXXXXXX"
        body=body,
    )


def main():
    data = load_topics()
    topic = get_next_topic(data)

    print(f"[{datetime.now().isoformat()}] Generating explanation for: {topic}")
    explanation = generate_explanation(topic)

    message = f"Day's concept: {topic}\n\n{explanation}"

    print("Sending WhatsApp message...")
    send_whatsapp(message)

    save_topics(data)
    print("Done. topics.json updated.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
