# AI Moderation — Phase 6

## Goal
Before a report changes a locality's Aura, confirm the photo actually shows the selected category
(e.g. someone marked "littering" — does the photo actually show litter?).

## Approach: Claude's vision capability

Claude can look at an image and answer a yes/no question about it. We ask it to respond in JSON so
the backend can parse it directly — no regex needed.

### Example backend call (Python, `anthropic` package)

```python
import anthropic
import base64

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from your .env

def moderate_report(image_bytes: bytes, category: str, is_positive: bool) -> dict:
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    behavior = "positive" if is_positive else "negative"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"A user reported this photo as an example of {behavior} civic "
                            f"behavior in the category '{category}'. "
                            "Look at the image and judge whether it plausibly shows that. "
                            "Respond ONLY with JSON, no other text, in this exact shape: "
                            '{"matches": true or false, "confidence": 0.0 to 1.0, "reason": "short reason"}'
                        ),
                    },
                ],
            }
        ],
    )

    # message.content[0].text will be the JSON string — parse it with json.loads()
    return message.content[0].text
```

### What the backend does with the result
- `matches: true` and `confidence` above your threshold (start with `0.6`) → approve, apply Aura change.
- `matches: false` or low confidence → reject, don't change Aura, tell the user why
  (use `reason` to build a friendly Gen-Z rejection message — see `docs/microcopy.md`).

### Also check for
- **Inappropriate content**: add a second, simpler check ("does this image contain anything
  inappropriate, violent, or unrelated to civic reporting?") before even doing the category match.
- **Blank/corrupt uploads**: reject before calling the AI at all (cheaper, faster).

---

## Duplicate detection — Phase 7 (non-AI, runs before AI moderation)

Simple version (good enough for v1):

```sql
SELECT id FROM reports
WHERE locality_id = ?
  AND category = ?
  AND is_positive = ?
  AND status != 'rejected'
  AND created_at >= datetime('now', '-24 hours');
```

If this returns any row → mark the new report `status = 'duplicate'`, don't call the AI, don't
change Aura. Return the "already flagged, bro" message.

**Stretch goal (later):** add image-similarity hashing (e.g. `imagehash` Python library) so two
different-looking photos of the *same* pile of litter, taken minutes apart by different people,
are still caught as duplicates even if timestamps differ slightly.
