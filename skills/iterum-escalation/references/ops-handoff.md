# Ops handoff — MVP design and known limits

Read this when setting up or changing the ops notification path. It is not needed to decide whether to halt — `SKILL.md` carries everything required for that.

## Transport

`send_ops_message()` posts to an ops Slack channel via an incoming webhook. Chosen for MVP because it needs no new tooling, no new inbox for ops to watch, and no build beyond the webhook itself. It is expected to be replaced once volume justifies a queue.

## Notification payload

Every notification carries:

| Field | Purpose |
|---|---|
| Issue reference | Ties the notification to the record |
| Property and unit | So ops knows the site without opening anything |
| Resident name | So whoever picks it up can address them properly |
| Category and `ops_action_required` | Decides whether this needs action now or awareness only |
| Trigger, verbatim | The resident's own words, not a paraphrase — ops needs to judge tone for themselves |
| Conversation state | One line on where things had got to, and what the agent had already asked |
| Link to the issue in Iterum IQ | Full history |
| Link to the WhatsApp thread | The point of the whole design — one click to take over |

Halt and flag-and-continue notifications must be visually distinct in the channel. Ops should be able to tell which is which without reading the body.

## Why ops joins the WhatsApp thread

The resident stays in one conversation for the whole issue. No channel switch, no repeating themselves, no "someone else will call you" that then requires them to be available for a phone call. From the resident's side the service simply continues, and the change of who is answering is invisible.

This is the part worth protecting if the transport is ever replaced. A queue system that emails the resident separately would be a worse outcome than the Slack webhook, however much better the tooling looked internally.

## Accepted limitations at current volume

Recorded so nobody mistakes them for solved, each with the condition that should trigger revisiting it.

**No acknowledgement loop.** A Slack message nobody opens looks identical to one that was handled. *Revisit when:* the channel is busy enough that messages scroll out of view before being read.

**No out-of-hours path.** A critical escalation at 11pm gives the resident the emergency number — which is the part that actually protects them — but nothing at Iterum picks it up until morning. *Revisit when:* volume or portfolio spread makes overnight cover justifiable, or when the first out-of-hours critical escalation happens, whichever comes first.

**No prioritisation.** Everything lands in one channel in arrival order. *Revisit when:* one team reading one channel stops being the reality.

**No structured review.** Nothing yet looks back at escalations to find the ones handled badly, or the false positives worth tuning out. `response_mode` and `escalation_category` are logged on every escalation specifically so that review is possible later without re-reading transcripts. *Revisit when:* there are enough escalations to see a pattern — this is also what will tell you whether the category 3 test is drawn in the right place.

## Constraint this places on the agent

The agent must not imply a response time to the resident, because none is guaranteed. "Someone from our team will contact you" remains the strongest honest phrasing available, and it should not be strengthened until an acknowledgement loop exists to back it up.
