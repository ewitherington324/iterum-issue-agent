# Worked examples — escalation

Three cases covering the distinctions that matter: an obvious halt, a flag-and-continue, and a complaint that is neither. Read alongside `../SKILL.md`.

**Example 1 — safety emergency mid-triage**

> **Agent:** Can you open the flap at the bottom front and tell me what you find behind it?
>
> **Resident:** hang on theres a weird burning smell coming from the back now and the lights flickered
>
> **Agent:** Thanks for telling me — stop what you're doing and leave it as it is. Don't touch the machine. If it's safe and dry to reach, switch it off at the wall socket. I'm passing this to our team now as urgent and someone will contact you.

Output: `escalation_category: "safety_emergency"`, `severity: "critical"`, `agent_state: "halted"`. Ops notified urgently with the burning smell, the flicker, and the fact that the resident was mid-way through opening the filter access. No troubleshooting resumes.

**Example 2 — distress, flag and continue**

> **Resident:** its been 3 weeks with no washing machine and im really struggling with it, ive got two under five and im not coping with any of this at the moment
>
> **Agent:** Three weeks with two small children is a lot — let's get this sorted rather than have you try anything else. I'm booking an engineer now and I'll come straight back with the earliest time I can get.

Output: `response_mode: "flag_and_continue"`, `escalation_category: "distress_vulnerability"`, `vulnerability_flag: true`, `ops_action_required: false`, `accommodations: ["No further troubleshooting steps", "Prioritise slot"]`, `agent_state: "active"`. Ops is notified for awareness with a link to the thread. No clinical detail recorded, no coping suggestions offered, nothing said about escalation.

This is the case worth getting right, and it is easy to get wrong in both directions. Halting would leave someone who has just said they are struggling waiting for a callback about a problem the agent could have solved in the next two messages. Ignoring it would mean asking them to go and pull a filter out. The answer is neither: acknowledge briefly, stop asking them to do things, go faster, and make sure a human can see it.

**Example 3 — a complaint that is not an escalation**

> **Resident:** honestly this is a joke, ive reported this twice already and nobody has done anything. absolutely useless
>
> **Agent:** That's a fair thing to be annoyed about, and I can see this has been raised before. I've got the details I need, so I'm going to get an engineer booked now rather than ask you to go through it again.

Output: no halt, no escalation category met. The prior reports are recorded on the issue so the pattern is visible to ops, and the repeat-report history feeds the repair-versus-replace assessment as evidence. The conversation continues.

Strong language, an accusation of poor service and a complaint history — and none of it meets the category 3 test, because the agent is not being asked to take a position on money, fault or tenancy. Stopping here would hand ops exactly the work this agent exists to absorb, and would leave the resident worse off than if they had never been contacted.
