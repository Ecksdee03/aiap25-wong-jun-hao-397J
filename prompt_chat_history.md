# AIAP Technical Assessment — Prompt Chat History

**Candidate name (as in NRIC):**

**Email (as used in your application):**

**AI assistant(s) used:** _(e.g., Claude 4.6 Sonnet, ChatGPT GPT-5, GitHub Copilot, Cursor)_

---

## How to fill in this document

Your submission has **two parts**:

1. **Share links** — for every chat with the AI that has a share-link feature
   (Claude, ChatGPT, Gemini, etc.), paste the link in the section below.
2. **Transcripts** — produce each chat below, labelling messages as `[User]` or
   `[AI]`. Don't edit, summarise, or rewrite anything afterwards.

**Both parts are required where possible.** The share link is the audit trail
(timestamped on the platform's servers); the transcript is what the assessors
actually read. They will be cross-checked.

For tools without share links (IDE-based assistants like Cursor, GitHub Copilot
Chat, or Claude Code in agent mode), write *"not available"* under share links
for that chat and rely on the transcript.

### What counts as editing

- **Allowed:** removing personal identifiers (real names, emails, API keys);
  redacting any unrelated personal chats accidentally captured in the export;
  fixing copy-paste artefacts (stray HTML tags) into clean text.
- **Not allowed:** deleting messages, summarising responses, rewriting your
  messages afterwards, reordering turns, removing exchanges that look
  embarrassing or off-track.

If you make redactions, note them briefly at the top of the relevant session
(e.g., *"Redacted: two unrelated personal messages between turn 4 and turn 5."*).
That transparency is itself a positive signal.

---

## Part 1 — Share Links

List one share link per chat with the AI. Use a short descriptor so assessors
know what each chat was about.

- **Session 1** — [brief description] — [tool name]: [paste URL here]
- **Session 2** — [brief description] — [tool name]: [paste URL here]
- **Session 3** — [brief description] — [tool name]: [paste URL here]

_(Add more lines as needed. Mark "not available" for IDE-based tools.)_

---

## Part 2 — Transcripts

Produce each chat below using the format:

```
[User] your message here

[AI] assistant's response here

[User] your next message

[AI] next response
```

Use one blank line between turns. Don't edit, summarise, or rewrite anything afterwards.

---

### Session 1 — [brief description] — [tool name]

[User] _your first message goes here_

[AI] _assistant's response goes here_

[User] _your next message_

[AI] _next response_

_(continue for the full session)_

---

### Session 2 — [brief description] — [tool name]

[User] _..._

[AI] _..._

_(continue)_

---

### Session 3 — [brief description] — [tool name]

[User] _..._

[AI] _..._

_(continue)_

---

## Example (for reference — remove from your submission)

### Session 1 — Initial scoping chat — Claude 4.6 Sonnet

[User] I've been given a take-home assessment about MoveEasy, a last-mile delivery company. Their customer ratings dropped from 4.4 to 3.9 and they want me to "use AI to fix it". What questions should I be asking before scoping this?

[AI] Good instinct to pause on scoping. A few categories of questions worth surfacing before you start building: First, on the action — who would actually use the output of your model, and what would they do with it? A dispatcher flagging risky deliveries needs different output than a customer service team identifying complaint patterns. Second, on data availability — six months might not be enough...

[User] That's helpful but I want to challenge one of your assumptions. You're framing this as predictive — but the Head of Customer Service quote sounded more like she wanted *pattern identification*, not prediction. Should I be considering a non-predictive framing at all?

[AI] You're right to push back — I was over-indexing on the dispatcher use case. The pattern-identification framing is genuinely different in shape...

_(and so on for the rest of the session)_

---