"""
Daily interview-prep WhatsApp sender.

Flow:
1. Read topics.json — an ordered list of topics + a pointer to "next index"
2. Call Groq API to generate a short, interviewer-style explanation
3. Send it via Twilio's WhatsApp API
4. Advance the pointer and write topics.json back (committed by the GitHub Action)

Run via: python send_daily_concept.py
Requires env vars: GROQ_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
                    TWILIO_WHATSAPP_FROM, MY_WHATSAPP_TO
"""

import json
import os
import sys
from datetime import datetime

from groq import Groq
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
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    system_prompt = (
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
    )

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
    )

    usage = completion.usage
    print(
        f"tokens — prompt: {usage.prompt_tokens}, "
        f"completion: {usage.completion_tokens}, "
        f"total: {usage.total_tokens}"
    )

    return completion.choices[0].message.content.strip()


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
