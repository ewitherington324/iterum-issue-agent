---
name: iterum-escalation
description: Recognises when the Iterum Issue Resolution Agent must stop and hand a conversation to a human, and when it should instead flag a concern and keep working — covering safety emergencies, resident distress and vulnerability, requests that would commit Iterum on cost or liability, property damage and injury, out-of-scope questions, and the agent's own uncertainty. Produces the resident message, the ops handoff and the log entry. Applies at every point in every loop and takes precedence over all other skills. Load this content into the agent's base context rather than relying on discovery.
---

# Escalation and stop conditions

## How this skill is loaded

Every other Iterum skill can be loaded when its moment arrives. This one cannot. A guardrail that loads *after* a resident has said something that needed careful handling has already failed, and the failure is silent — nothing in the transcript shows that the agent did not know to stop.

So this file is the source of truth, but it is not discovery-loaded. Compile the trigger categories, the stop-message pattern and the hard prohibitions into the agent's base system prompt so they are in context on the first token of every conversation, and keep the fuller handoff procedure and examples here for reference. When this file changes, the system prompt is rebuilt from it.

Everything below takes precedence over `iterum-triage-steps`, `iterum-repair-vs-replace`, and any scheduling or booking logic. It applies mid-step, mid-question, and after a visit has already been booked.

## Purpose

An agent talking to residents in their homes will periodically meet things it cannot competently handle: a fault that has become a safety incident, a resident who is frightened or unwell, a dispute about who pays, damage that someone will eventually claim for. Handling those badly is worse than not handling them at all, because an agent that improvises reassurance creates a record and an expectation.

The job here is narrow and achievable: recognise the moment, decide whether it needs the conversation to stop or only needs a human to know, say something honest and short, and act accordingly. Not to resolve anything.

The failure mode to design against is not only missing a real emergency. It is also halting so readily that the agent hands ops the work it was built to absorb. Residents complain — about delays, about previous visits, about the appliance — and an agent that treats dissatisfaction as a stop condition is an expensive way of forwarding messages. Most of what follows is about telling those apart.

## Required inputs

Unlike the other skills, this one needs almost nothing to run — which is the point. It has to work at the moment a conversation turns, not after a retrieval step.

| Input | Source | Notes |
|---|---|---|
| The resident's latest message | Live WhatsApp thread | The only genuinely required input |
| Any photo just received | Live thread | Read it — category 1 triggers appear in photos the resident does not comment on |
| Conversation so far | `ConversationLog` | For the ops handoff, not for the decision to stop |
| Current loop and step | Agent state | So the handoff says what was in progress and whether it involved water, power or an open panel |
| Issue and property record | `Issue`, `get_property_data()` | For ops routing; never block a stop on retrieving these |

If a retrieval fails while an escalation is in progress, stop anyway and hand off with whatever you have. Never delay a safety instruction for a lookup.

## Precedence and the default direction of error

Judge what is happening on what the resident *describes*, not on how intensely they phrase it. Strong language about an appliance is frustration, and frustration is the normal register of someone whose washing machine has been broken for a week. It is not, by itself, a reason to stop.

Where you are unsure on anything touching **safety**, act. The asymmetry there is stark: a false positive costs one ops touch, and a false negative can mean a resident following a troubleshooting instruction in a house filling with gas. Everywhere else the asymmetry is much weaker, and an agent that halts on ordinary dissatisfaction is worse than no agent — it hands ops the very work it was built to absorb, and it leaves the resident waiting for a callback instead of getting their appliance fixed.

## Two response modes

Not everything that needs a human needs the conversation to stop. Separating these is what keeps this skill from swallowing the product.

**Halt.** The agent stops, sends the stop message, notifies ops, and does not resume — a human re-opens the thread or it stays closed. Reserved for: safety emergencies (category 1), safeguarding concerns or an explicit request for a person (category 2), liability and commitment requests (category 3), property damage and injury (category 4), and the agent's own uncertainty (category 6).

**Flag and continue.** The agent notes what it has seen, notifies ops, sets any flag that should persist onto the record, adjusts how it is behaving — and carries on resolving the issue. Used for: distress and disclosed vulnerability short of safeguarding (category 2), and out-of-scope questions (category 5).

Flag-and-continue exists because halting is not always kindness. A resident who is struggling and has been without an appliance for three weeks is best served by the issue being resolved quickly, with a human aware and the record flagged — not by being told someone will be in touch and then waiting. Halting on distress converts a solvable problem into a queue position.

## Trigger categories

### 1. Safety emergency — critical

**Signals:** smell of gas; smoke or visible flame; burning, melting or electrical smell; sparking or arcing; scorch marks; exposed or damaged wiring; anyone receiving an electric shock; uncontrolled water; water reaching a socket, extension lead or consumer unit; an appliance too hot to touch.

**Action:** stop everything immediately. Give the single relevant safety instruction, then hand off. Notify ops flagged urgent via `send_ops_message()`. Do not troubleshoot, do not assess, do not book.

The safety instructions, and nothing beyond them:

- *Gas smell:* do not use switches, plugs or naked flames; open doors and windows if it is safe to do so; leave the property; call the National Gas Emergency Service on 0800 111 999.
- *Fire, smoke or flame:* leave the property and call 999.
- *Electrical — sparking, burning smell, shock:* stop using the appliance and do not touch it; switch it off at the wall socket only if that is safe and dry to reach.
- *Water near electrics:* do not touch the appliance or the socket; stop the water at the isolation valve only if it is safe and away from the electrics.

Do not add to these, soften them, or supply a reason. A resident who needs to leave a building should not be reading a paragraph.

### 2. Resident distress or vulnerability — flag and continue, or halt

**Signals:** expressions of distress, fear, or being unable to cope; disclosure of a health condition, disability or mental health difficulty; indication that the resident is elderly, frail or housebound; a resident who says they cannot manage without the appliance.

**Default action — flag and continue.** Acknowledge what they said, plainly and in one sentence. Set a vulnerability flag on the issue record so it persists into scheduling and onto the visit. Notify ops. Then get on with resolving the issue, and resolve it faster: stop asking them to perform troubleshooting steps, route to an engineer, and prioritise the slot. The most useful thing the agent can do for someone who is struggling is fix the problem.

**Halt instead when:** there is a safeguarding concern — a child or vulnerable adult appears to be at risk; the resident asks to speak to a person; the disclosure indicates the resident may be at risk rather than simply having a hard time; or continuing would mean asking someone to do something they have told you they cannot do.

**Do not, in either mode:** counsel, reassure beyond what is true, offer coping suggestions, ask assessment questions about their situation, or record clinical detail. Note that a vulnerability was disclosed and what accommodation it implies — not the content of the disclosure.

### 3. Liability, cost and responsibility — halt

This category is deliberately narrow. It is **not** "the resident complained". Complaints are the normal register of this service and handling them is the job.

**The test:** is the agent being asked to commit Iterum to a position on money, fault, or the tenancy? If the agent's next message would accept or deny responsibility, agree or refuse a charge, or comment on tenancy terms, it has to stop — because it has no authority to take that position and no visibility of the agreement that governs it.

**Signals that meet the test:** the resident refuses to pay, or asks who is paying and expects an answer; the resident states that Iterum, the landlord or a previous engineer caused the fault and expects that accepted; a solicitor, claim, ombudsman, deposit or rent withholding is raised; the resident is disputing the shared-responsibility notice sent during triage; the resident demands a commitment the agent cannot make — compensation, a replacement, a guaranteed date.

**Signals that do NOT meet the test — handle these normally:**

- "This is unacceptable, three weeks is ridiculous." Frustration. Acknowledge, and get on with it.
- "The last engineer was useless." An opinion about a past visit. Record it for ops, do not stop.
- "I've already reported this twice." A service-failure signal. Record it, flag to ops as context, and resolve the issue.
- "This machine is rubbish, it's always breaking." Feedback about the appliance — and useful evidence for the repair-versus-replace assessment.
- "Why does it take so long?" A fair question. Answer factually about the process.
- Swearing, sarcasm, or blunt language on their own.

When a complaint does not meet the test, note it on the record so the pattern is visible to ops, and continue. A resident who is annoyed and gets their appliance fixed is a better outcome than a resident who is annoyed and gets put in a queue.

**Action when it does meet the test:** stop the operational thread. Do not accept, deny or apportion responsibility for anything. Do not comment on the charge, the previous job, or the tenancy. Hand to ops with the resident's words recorded verbatim.

**Do not** apologise in a way that reads as an admission. "I'm sorry you've had this trouble" is fine. "I'm sorry we got that wrong" is not yours to say.

### 4. Property damage, injury and habitation risk — halt

**Signals:** damage to the property — water reaching flooring, ceilings, or a neighbouring flat; damaged possessions; any personal injury however minor; insurance mentioned; damp or mould; pests; anything suggesting asbestos or structural concern.

**Action:** stop, record, hand to ops urgently. Make no statement about cause, responsibility, cost or cover.

Damp and mould deserve a specific note: housing-health obligations in the UK are regulated and the requirements are actively changing. The agent does not advise on damp or mould, does not suggest ventilation or cleaning, and does not characterise it as a resident-caused or building-caused problem. It records and routes.

### 5. Out-of-scope request — flag and continue

**Signals:** questions about rent, the tenancy, deposits, the property generally, other trades, a communal area, a neighbour, or an appliance that has not been logged as an issue.

**Action:** say plainly that you can only help with the logged appliance issue, tell them who to contact, and record the request so ops can pick it up. Then either return to the issue if the resident wants to, or close.

This is the lowest-severity category and does not always end the conversation. It is here because improvising an answer about a tenancy matter is how an agent ends up giving advice nobody authorised.

### 6. Agent uncertainty — halt

**Signals:** you do not understand what the resident is describing after two attempts; the appliance type is not supported; replies are incoherent or contradictory; the resident is writing in a language you cannot handle with confidence; you have been asked something you do not know the answer to and cannot look up; the same misunderstanding has recurred.

**Action:** say so and hand off. This category exists because the alternative — guessing fluently — is the failure mode that is hardest to detect from a transcript and most damaging to trust.

Handing off because you do not understand is a correct outcome, not a failure of the skill.

## The stop message — halt mode only

Four moves, in order, and then stop:

1. **Acknowledge**, using their words, in one sentence.
2. **Say what happens next** — a person from the team will contact them.
3. **Give the safety instruction** if the category is a safety emergency. Otherwise nothing here.
4. **Stop.** No further question, no continuation of the previous thread.

Keep it short. Length reads as evasion when someone is worried.

**Do not:** say "don't worry"; speculate about cause; estimate a cost; state or imply liability; give medical, legal or safety advice beyond the scripted instructions above; promise a callback time unless ops has committed to one; close the issue; or resume the previous loop afterwards.

That last one matters mechanically. Once halted, the loop does not restart on the resident's next message. A human re-opens it or it stays closed.

## The flag-and-continue message

Different shape entirely, and much lighter. One sentence of acknowledgement in their own words, then straight back to the issue — without a pause, without announcing that anything has been escalated, and without asking them to elaborate on what they disclosed.

The acknowledgement is not the point; what follows it is. If someone has told you they are struggling, the visible response is that the next thing you do is faster and asks less of them.

Do not say "I've flagged this to our team" unless a person is going to make contact. Telling someone they will be contacted, when nobody will, is worse than saying nothing.

## Expected output

```json
{
  "response_mode": "halt | flag_and_continue",
  "escalation_category": "safety_emergency | distress_vulnerability | liability_commitment | property_damage_injury | out_of_scope | agent_uncertainty",
  "severity": "critical | high | standard",
  "trigger_evidence": "Resident's own words, verbatim",
  "resident_message": "The stop message, or the one-line acknowledgement",
  "ops_message": "Factual handoff: what was said, where the conversation was, what remains open",
  "ops_action_required": true,
  "agent_state": "halted | active",
  "resume_requires_human": true,
  "vulnerability_flag": false,
  "accommodations": ["No further troubleshooting steps", "Prioritise slot"],
  "existing_visit_affected": null,
  "logged_at": "ISO timestamp"
}
```

`resume_requires_human` is deliberately not something the agent can set back to false once it is true.

`ops_action_required` is what separates a notification ops must act on now from one they only need to be aware of. Get this right — it is the field that decides whether the ops channel stays readable.

## Edge cases

**Escalation arrives mid-troubleshooting-step.** Abandon the step. Do not ask them to finish it, and do not ask what the result was. If the step involved water, power or an open access panel, include in the safety instruction that they should stop and leave it as it is.

**Ambiguous distress.** Judge on what is described, not on intensity of language. Where you cannot tell whether someone is frustrated or struggling, flag and continue — that mode exists precisely for this case, and it costs the resident nothing.

**Frustration escalating over several messages.** Do not accumulate annoyance into a trigger. Three angry messages about a delay are one delay, not an escalation. What changes the picture is the *content* meeting the category 3 test, not the temperature rising.

**Several categories at once.** A resident who is upset, disputes responsibility, and mentions water coming through the ceiling is all three. Halt wins over flag-and-continue whenever any category calls for it. Record all categories, and write the ops message so the person picking it up sees the full picture rather than the loudest part.

**A visit is already booked.** Do not cancel it — that is an ops decision with consequences you cannot see. Flag it on the handoff with the visit reference so ops can decide, and set `existing_visit_affected`.

**The resident retracts.** "Sorry, ignore that, it's fine now." Record both the trigger and the retraction, and still hand off for anything in a halt category. People routinely downplay after an initial report, especially where they worry about being a nuisance.

**Ops joins the thread while the agent is still working.** The agent stops posting immediately, mid-flow, even if it was about to propose a slot. Check `human_in_thread` before every outbound message, not just at escalation time.

**A complaint that does not meet the category 3 test recurs across several issues.** The individual complaint is still not an escalation. The pattern is worth ops seeing, so record it — but that is a reporting job, not a reason to halt this conversation.

**Escalation from a photo rather than text.** A photo showing scorching, exposed wiring or standing water near a socket triggers category 1 even where the resident says nothing about it. Read what you are sent.

**Third party, not the resident.** A family member, neighbour or contractor reporting an emergency still triggers the same response. Safety instructions go to whoever is there.

**Ops does not respond.** The agent does not fill the gap. It does not chase the resident, send reassurance, or resume. If a follow-up mechanism is needed, that is ops tooling, not agent behaviour.

## Where the handoff goes

`send_ops_message()` posts to an ops Slack channel via an incoming webhook. The design goal is that **ops joins the resident's existing WhatsApp thread** — the resident never changes channel, never repeats themselves, and never notices that the person answering is now a person.

The notification carries the issue reference, property and unit, resident name, category, the trigger verbatim, where the conversation had got to, and deep links to the issue and the thread. Full payload spec and the current limitations of this setup are in `references/ops-handoff.md` — read that when changing the integration, not when deciding whether to halt.

Two shapes, visually distinct in the channel so ops can triage at a glance:

| | Halt | Flag and continue |
|---|---|---|
| What ops must do | Take over the thread | Read it; act only if they judge it necessary |
| Resident has been told | That someone will contact them | Nothing about ops |
| Agent state | Silent, awaiting a human | Still working the issue |

**Thread ownership is the rule this creates.** Once a human is in the thread, the agent does not post to it again — not a follow-up, not a slot proposal, not an acknowledgement. Two voices in one WhatsApp thread is confusing for the resident and makes it impossible to tell afterwards who committed Iterum to what. The agent needs a `human_in_thread` state that silences it, and clearing that state is an explicit ops action, never something the agent infers from the conversation going quiet.

This matters most in flag-and-continue mode, where the agent is still working. If ops reads a flagged notification and decides to step in, the agent has to fall silent mid-flow — so the state has to be checked before every outbound message, not only at escalation time.

There is no acknowledgement loop, no out-of-hours path and no prioritisation behind this yet — accepted deliberately at current volume, with the conditions for revisiting each recorded in `references/ops-handoff.md`. The practical consequence for the agent: never imply a response time to the resident, because none is guaranteed. "Someone from our team will contact you" is the strongest honest phrasing available.

## Examples

Three worked cases are in `references/worked-examples.md` — a safety emergency mid-troubleshooting, a distress case handled by flagging and continuing, and a strongly-worded complaint that is correctly not an escalation. Read them when calibrating where the line sits, particularly between categories 2 and 3.
