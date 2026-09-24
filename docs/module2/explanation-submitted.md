# Module 2 — what the skills changed

> **As submitted.** Transcribed from the PDF handed in for Module 2. Kept verbatim as the record of
> what was claimed. One correction for later modules: the "can't drift apart" claim in the last
> section is not yet literally true — `agent/fallbacks.py` keeps its own copy of the fault
> patterns (see `CLAUDE.md`, known open items). Evidence for the other claims is in
> `verification.md` in this folder; the prompts the skills replaced are in `baseline-prompts.md`.

---

**Recap:** Iterum manages white goods (appliances) for large rental buildings. When something
breaks, a property manager logs it, and our agent messages the resident on WhatsApp to work out
what's wrong — resolving it with them if possible, booking an engineer if not.

The prototype already did all of that before this module. What changed is *how it knows what to
say*.

## 3 Skills

The test I used: if a step gives the same answer every time from the same inputs, it's code. If it
needs judgement inside a policy, it's a skill.

That ruled several other steps of the system out: e.g. checking a warranty, finding the next free
appointment, looking up whether a part is in stock — these are lookups and arithmetic. The three
skills I chose are the three points where the agent has to think rather than just retrieve:

1. What to ask a resident to try before sending anyone (troubleshooting skill)
2. Whether a broken appliance should be repaired or replaced (repair vs. replace skill)
3. When to stop and hand the conversation to a human (escalation skill)

Each is repeated on every single issue, follows a consistent process, and goes wrong in expensive
ways if done inconsistently. That's the case for making them skills.

## What each one does differently now

**Troubleshooting guidance.** Before, the agent was told what residents must never be asked to do
— no electrical work, nothing behind a fixed panel — and then invented the actual steps from its
own general knowledge of appliances. The safety rules were solid; the appliance knowledge was
improvised fresh every time, with nothing to check it against.

Now it works from a written fault guide for each appliance type, organised against Iterum's own
catalogue of 55 fault categories taken from our real service history. When a "dishwasher not
draining" issue arrives, the agent is handed the documented pattern for that exact fault (e.g.
check the filter first, it's the most common cause; if the sink isn't draining either it's a
plumbing problem, not an appliance one) rather than reconstructing it from scratch.

The guidance now exists as a document. An Iterum engineer can read it, mark it up and correct it.
Previously the advice only existed in the instant it was generated.

**Repair versus replace.** Before, a short instruction with our cost and age rules, which returned
a recommendation and a list of reasons for it.

Now it follows a written method: six factors weighed in order, a short list of faults where the
answer is fixed regardless of anything else (a cracked hob is always a replacement, at any age),
and — the change that matters most — a requirement to state the strongest argument *against* its
own recommendation.

That last one exists because every replacement recommendation is checked by an engineer before
anything is ordered. A log that records only the conclusion tells you an engineer overruled the
agent. A log that also records the counter-argument tells you whether the agent had already
spotted the reason it was overruled. Only the second is something we can learn from as this data
accumulates.

In testing it produced substantive counter-arguments every time, not filler. On one replacement
case it argued against itself on the grounds that the cost was only marginally over our threshold
and might fall back under it once the fault was confirmed on site. Twice it flagged a data
inconsistency in our own records that nobody had asked it to look for.

**Escalation.** Before, a single instruction: if you hit something you can't handle, stop.

The skill now has two responses rather than one. It stops for safety and for anything touching
money, fault or the tenancy. For a resident who's struggling, it acknowledges, stops asking them to
do things, routes straight to an engineer and prioritises the appointment — with a human notified,
but the problem still getting solved. It also carries an explicit list of things that are *not*
escalations, because a rule that only says what to catch will over-catch.

## What this improved

The agent's behaviour stopped being buried inside code and became a set of documents the people
who understand appliances can actually review. The same documents now feed both the AI path and
the simple rules-based backup, so the two can't drift apart. And because the troubleshooting guide
is organised against our real fault catalogue, it gets more useful as our service data grows
rather than staying static.
