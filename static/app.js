/* Iterum Issue Resolution Agent - demo UI.
   Renders the SSE event stream into three views: what the resident sees, what the agent
   is actually doing, and the human gates. */

const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
};
const esc = (s) => String(s ?? "");
const pretty = (v) => typeof v === "string" ? v : JSON.stringify(v, null, 2);

const LOOP_COLOUR = { triage: "blue", decision: "purple", booking: "amber", done: "green" };

let state = {};
let scenarios = [];
let running = false;

/* ------------------------------------------------------------------ scenarios */
async function loadScenarios() {
  scenarios = await (await fetch("/api/scenarios")).json();
  const sel = $("scenario");
  sel.innerHTML = "";
  scenarios.forEach((s) => {
    const o = el("option", null, s.title);
    o.value = s.id;
    sel.appendChild(o);
  });
  showScenarioCard(scenarios[0]);
}

function showScenarioCard(s) {
  if (!s) return;
  const c = $("scenarioCard");
  c.innerHTML = "";
  const card = el("div", "scenario-card");
  card.appendChild(el("h3", null, s.title));
  card.appendChild(el("p", null, s.summary));
  const exp = el("div", "expected");
  exp.appendChild(el("span", "label", "What should happen"));
  exp.appendChild(el("div", null, s.expected));
  card.appendChild(exp);
  c.appendChild(card);
}

$("scenario").addEventListener("change", (e) => {
  showScenarioCard(scenarios.find((s) => s.id === e.target.value));
});

/* ------------------------------------------------------------------ run control */
$("run").addEventListener("click", async () => {
  $("thread").innerHTML = "";
  $("trace").innerHTML = "";
  document.querySelector("#traceBody .empty")?.remove();
  running = true;
  await fetch("/api/run", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: $("scenario").value, auto_play: $("autoplay").checked }),
  });
});

$("stop").addEventListener("click", () => fetch("/api/stop", { method: "POST" }));

$("autoplay").addEventListener("change", (e) => {
  fetch("/api/autoplay", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ auto_play: e.target.checked }),
  }).catch(() => {});
});

/* ------------------------------------------------------------------ resident pane */
function bubble(dir, text, meta) {
  const b = el("div", `bubble ${dir}`, text);
  if (meta) b.appendChild(el("span", "meta", meta));
  $("thread").appendChild(b);
  scrollDown("residentBody");
}

function setAwaiting(on, auto) {
  document.querySelectorAll(".awaiting").forEach((n) => n.remove());
  if (on) {
    $("thread").appendChild(el("div", "awaiting",
      auto ? "waiting for the resident… (simulated)" : "waiting for you to reply as the resident…"));
    scrollDown("residentBody");
  }
  $("replyText").disabled = !on || auto;
  $("replySend").disabled = !on || auto;
  if (on && !auto) $("replyText").focus();
}

async function sendReply() {
  const text = $("replyText").value.trim();
  if (!text) return;
  $("replyText").value = "";
  await fetch("/api/resident/reply", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}
$("replySend").addEventListener("click", sendReply);
$("replyText").addEventListener("keydown", (e) => { if (e.key === "Enter") sendReply(); });

/* ------------------------------------------------------------------ trace pane */
function scrollDown(id) { const n = $(id); n.scrollTop = n.scrollHeight; }

function traceCard(cls, pillCls, pillText, name, bodyNodes, openByDefault) {
  const card = el("div", `evt ${cls}` + (openByDefault ? " open" : ""));
  const head = el("div", "evt-head");
  head.appendChild(el("span", `pill ${pillCls}`, pillText));
  head.appendChild(el("span", "name", name));
  const chev = el("span", "chev", "›");
  head.appendChild(chev);
  head.addEventListener("click", () => card.classList.toggle("open"));
  card.appendChild(head);
  const body = el("div", "evt-body");
  (bodyNodes || []).forEach((n) => body.appendChild(n));
  card.appendChild(body);
  $("trace").appendChild(card);
  scrollDown("traceBody");
  return card;
}

function pre(obj) { return el("pre", null, pretty(obj)); }

function plain(cls, text) {
  $("trace").appendChild(el("div", cls, text));
  scrollDown("traceBody");
}

/* ------------------------------------------------ skill output (Module 2) ---------
   The three skills feed the two reasoning calls in agent/reasoning.py, but until now
   nothing they distinctively produce reached the UI - it arrived as an undifferentiated
   JSON dump in the trace, alongside every other tool result. These renderers pull out
   the parts that ARE the skills' contribution, so the before/after is visible rather
   than asserted:

     - decision skill  -> contra_indicators, evidence_missing, limits_applied, determinative
     - triage skill    -> fault_slug and whether its reference section matched

   Both fall back quietly: on the rules-based path there are no contra_indicators and
   no skill name, and the card says so, which is the A/B in one glance. */
let skillOut = { assessment: null, triage: null };

const CODE_PILL = { A: "amber", B: "green", C: "amber", D: "blue" };

function parseResult(raw) {
  try { return typeof raw === "string" ? JSON.parse(raw) : raw; } catch { return null; }
}

function listBlock(labelText, items, extraCls, ordered) {
  const wrap = el("div", "skill-block");
  wrap.appendChild(el("div", "label", labelText));
  const list = el(ordered ? "ol" : "ul", "skill-list" + (extraCls ? " " + extraCls : ""));
  (items || []).forEach((t) => list.appendChild(el("li", null, String(t))));
  wrap.appendChild(list);
  return wrap;
}

function textBlock(labelText, body, extraCls) {
  const wrap = el("div", "skill-block" + (extraCls ? " " + extraCls : ""));
  wrap.appendChild(el("div", "label", labelText));
  wrap.appendChild(el("div", "note", body));
  return wrap;
}

function assessmentCard(a) {
  const card = el("div", "card skill");

  const h = el("h4");
  h.appendChild(el("span", `pill ${CODE_PILL[a.code] || "grey"}`, `Code ${a.code}`));
  h.appendChild(el("span", null, a.code_meaning || "recommendation"));
  card.appendChild(h);

  const meta = el("div", "skill-meta");
  const conf = Number(a.confidence);
  const thr = Number(a.confidence_threshold);
  meta.appendChild(el("span", `pill ${a.meets_threshold ? "green" : "amber"}`,
    `confidence ${isFinite(conf) ? conf.toFixed(2) : "?"}`));
  if (isFinite(thr)) {
    meta.appendChild(el("span", "note", a.meets_threshold
      ? `meets the ${thr.toFixed(2)} threshold`
      : `BELOW the ${thr.toFixed(2)} threshold`));
  }
  card.appendChild(meta);

  // The marker that has to read at a glance: this code did not come from weighing.
  if (a.determinative) {
    const d = el("div", "determ");
    d.appendChild(el("span", "pill solid-purple", "DETERMINATIVE"));
    d.appendChild(el("span", null,
      "Fixed-outcome fault \u2014 the fault class sets the code on its own. " +
      "The six factors, the 7-year line and the 70% ratio do not apply."));
    card.appendChild(d);
  }

  if (a.rationale) card.appendChild(textBlock("Rationale", a.rationale));
  if (a.evidence_used && a.evidence_used.length)
    card.appendChild(listBlock("Evidence used", a.evidence_used));

  // The headline addition. Empty is now a validation error on a weighed call, so an
  // absent list here means the rules-based path, not a silent miss.
  if (a.contra_indicators && a.contra_indicators.length) {
    card.appendChild(listBlock("Contra-indicators \u2014 what argues against this code",
      a.contra_indicators, "contra"));
  }
  if (a.evidence_missing && a.evidence_missing.length)
    card.appendChild(listBlock("Evidence missing", a.evidence_missing, "gaps"));
  if (a.limits_applied && a.limits_applied.length)
    card.appendChild(listBlock("Confidence limits applied",
      a.limits_applied.map((l) => `${Number(l.limit).toFixed(2)} \u2014 ${l.reason}`), "gaps"));
  if (a.confidence_capped)
    card.appendChild(textBlock("Confidence capped",
      `Reported ${Number(a.confidence_capped.reported).toFixed(2)}, held at ` +
      `${Number(a.confidence_capped.capped_to).toFixed(2)} by its own reported limit.`, "gaps"));

  const src = el("div", "skill-src");
  src.appendChild(el("span", "pill grey", a.skill || "rules-based heuristic"));
  if (a.assessment_id) src.appendChild(el("span", "pill grey", a.assessment_id));
  src.appendChild(el("span", null, a.source === "subagent"
    ? "reasoning call" : "fallback path \u2014 no skill in context"));
  if (a.confidence_basis) src.appendChild(el("span", "basis", a.confidence_basis));
  card.appendChild(src);

  return card;
}

function triageNodes(t) {
  const nodes = [];

  const row = el("div", "skill-meta");
  row.appendChild(el("span", "pill purple", t.fault_slug || "no fault_slug"));
  row.appendChild(el("span", `pill ${t.reference_matched ? "green" : "red"}`,
    t.reference_matched ? "reference matched" : "NO reference"));
  nodes.push(row);

  nodes.push(el("div", "note", t.reference_matched
    ? "Steps drawn from the documented fault pattern for this slug under " +
      "skills/iterum-triage-steps/references/ \u2014 not improvised."
    : "No reference section for this appliance type. The skill instructs the model not " +
      "to improvise beyond universally safe checks and to route to an engineer."));

  if (t.steps && t.steps.length)
    nodes.push(listBlock("Resident-safe steps", t.steps, null, true));
  if (t.diagnostic_question)
    nodes.push(textBlock("Diagnostic question", t.diagnostic_question));
  if (t.safety_note)
    nodes.push(textBlock("Safety", t.safety_note, "safety"));

  const src = el("div", "skill-src");
  src.appendChild(el("span", "pill grey", t.skill || "rules-based lookup"));
  src.appendChild(el("span", null, t.source === "llm_reasoning_call"
    ? "reasoning call" : "fallback path"));
  nodes.push(src);

  return nodes;
}

/* ------------------------------------------------------------------ gates pane */
let gatesHtml = { gate: null, ops: [], visits: [], closed: null, guardrails: [] };

function renderGates() {
  const p = $("tab-gates");
  p.innerHTML = "";

  // open gate
  if (state.pending_gate) {
    const g = state.pending_gate;
    const ctx = g.context || {};
    const card = el("div", "card gate-open");
    const h = el("h4");
    h.appendChild(el("span", "pill amber", g.kind === "engineer" ? "Engineer" : "Property manager"));
    h.appendChild(el("span", null, g.kind === "engineer"
      ? "Confirm or override the recommendation" : "Approve the replacement cost"));
    card.appendChild(h);

    const dl = el("dl");
    const add = (k, v) => { dl.appendChild(el("dt", null, k)); dl.appendChild(el("dd", null, v)); };
    if (g.kind === "engineer") {
      add("Engineer", `${ctx.engineer?.name} — ${ctx.engineer?.partner}`);
      add("Channel", ctx.channel);
      add("Recommendation", ctx.recommendation);
      if (ctx.rationale) add("Rationale", ctx.rationale);
    } else {
      add("To", ctx.to);
      add("Subject", ctx.subject);
      add("Cost", `£${Number(ctx.estimated_cost).toFixed(0)}`);
      add("Threshold", `£${Number(ctx.threshold).toFixed(0)}` +
        (ctx.over_threshold ? " — OVER, approval required" : " — under"));
    }
    card.appendChild(dl);
    if (g.kind === "pm" && ctx.body) card.appendChild(pre(ctx.body));

    const note = el("input");
    note.placeholder = g.kind === "engineer" ? "Note / your assessment…" : "Note…";
    const row = el("div", "actions");
    const yes = el("button", "ok", g.kind === "engineer" ? "Confirm" : "Approve");
    const no = el("button", "no", g.kind === "engineer" ? "Override" : "Reject");
    const send = (decision) => fetch(`/api/gate/${g.kind}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, note: note.value }),
    });
    yes.addEventListener("click", () => send(g.kind === "engineer" ? "confirm" : "approve"));
    no.addEventListener("click", () => send(g.kind === "engineer" ? "override" : "reject"));
    row.appendChild(yes); row.appendChild(no);
    card.appendChild(note); card.appendChild(row);
    p.appendChild(card);
  }

  // The assessment that the gates are deciding on. Placed directly under an open gate
  // so the engineer is looking at the contra-indicators while confirming or overriding.
  if (skillOut.assessment) p.appendChild(assessmentCard(skillOut.assessment));

  // resolved decisions
  const decided = [];
  if (state.engineer_decision) decided.push(["Engineer", state.engineer_decision]);
  if (state.pm_decision) decided.push(["Property manager", state.pm_decision]);
  decided.forEach(([who, d]) => {
    const card = el("div", "card");
    const h = el("h4");
    const good = d.decision === "confirm" || d.decision === "approve";
    h.appendChild(el("span", `pill ${good ? "green" : "red"}`, d.decision));
    h.appendChild(el("span", null, who));
    card.appendChild(h);
    if (d.note) card.appendChild(el("div", "note", d.note));
    p.appendChild(card);
  });

  // ops feed
  if (gatesHtml.ops.length) {
    const card = el("div", "card");
    card.appendChild(el("h4", null, "Ops queue"));
    gatesHtml.ops.forEach((o) => {
      const row = el("div", "note");
      row.appendChild(el("span", "pill blue", o.category));
      row.appendChild(el("span", null, " " + o.request));
      card.appendChild(row);
    });
    p.appendChild(card);
  }

  // visits
  if (gatesHtml.visits.length) {
    const card = el("div", "card");
    card.appendChild(el("h4", null, "Visits"));
    gatesHtml.visits.forEach((v) => {
      const row = el("div", "note");
      row.appendChild(el("span", `pill ${v.status === "confirmed" ? "green" : "grey"}`, v.status));
      row.appendChild(el("span", null, ` ${v.type} — ${v.slot_date} (${v.id})`));
      card.appendChild(row);
    });
    p.appendChild(card);
  }

  if (gatesHtml.guardrails.length) {
    const card = el("div", "card");
    card.appendChild(el("h4", null, "Guardrails fired"));
    gatesHtml.guardrails.forEach((g) => {
      const row = el("div", "note");
      row.appendChild(el("span", "pill red", g.rule));
      row.appendChild(el("span", null, " " + g.detail));
      card.appendChild(row);
    });
    p.appendChild(card);
  }

  if (gatesHtml.closed) {
    const card = el("div", "card");
    const h = el("h4");
    h.appendChild(el("span", "pill green", "closed"));
    h.appendChild(el("span", null, gatesHtml.closed.resolution));
    card.appendChild(h);
    card.appendChild(el("div", "note", gatesHtml.closed.summary));
    p.appendChild(card);
  }

  if (!p.children.length) {
    p.appendChild(el("div", "empty",
      "Nothing waiting on a human. On the repair path this stays empty for the whole run — that is the point."));
  }
}

/* ------------------------------------------------------------------ tabs */
document.querySelectorAll(".tabs button").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("on"));
    document.querySelectorAll(".tab-panel").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    $("tab-" + b.dataset.tab).classList.add("on");
    if (b.dataset.tab === "record") loadRecord();
    if (b.dataset.tab === "log") loadLog();
  });
});

async function loadRecord() {
  const p = $("tab-record");
  try {
    const r = await (await fetch("/api/record")).json();
    p.innerHTML = "";
    const mk = (title, obj) => {
      const c = el("div", "card");
      c.appendChild(el("h4", null, title));
      c.appendChild(pre(obj));
      p.appendChild(c);
    };
    mk("Issue (visits nested inside)", r.issue);
    mk("Appliance", r.appliance);
    mk("Property & engineer", { property: r.property, engineer: r.engineer, pm: r.property_manager });
    if (r.approvals.length) mk("Approvals", r.approvals);
    if (r.email_outbox.length) mk("Email outbox", r.email_outbox);
    if (r.ops_queue.length) mk("Ops queue", r.ops_queue);
  } catch {
    p.innerHTML = '<div class="empty">Run a scenario first.</div>';
  }
}

async function loadLog() {
  const p = $("tab-log");
  const rows = await (await fetch("/api/log")).json();
  p.innerHTML = "";
  if (!rows.length) { p.innerHTML = '<div class="empty">Nothing logged yet.</div>'; return; }
  const card = el("div", "card");
  card.appendChild(el("h4", null, `decision_log.jsonl — ${rows.length} entries`));
  rows.slice().reverse().forEach((r) => {
    const row = el("div", "log-row");
    row.appendChild(el("b", null, r.event));
    row.appendChild(el("span", null, " " + (r.tool || r.rule || r.scenario || "")));
    if (r.reason) row.appendChild(el("div", null, r.reason));
    card.appendChild(row);
  });
  p.appendChild(card);
}

/* ------------------------------------------------------------------ knobs */
const KNOB_SPECS = [
  { key: "pm_cost_threshold_gbp", label: "PM approval threshold", min: 0, max: 1200, step: 25,
    fmt: (v) => "£" + Number(v).toFixed(0),
    hint: "PRD open question — needs a real number. Drop it below the replacement cost and the PM gate appears." },
  { key: "confidence_threshold", label: "Confidence threshold", min: 0.3, max: 1, step: 0.05,
    fmt: (v) => Number(v).toFixed(2),
    hint: "PRD assumes 0.75, but what underlies the percentage is undecided." },
  { key: "max_slot_rejections", label: "Slot rejections before ops", min: 1, max: 6, step: 1,
    fmt: (v) => String(v), hint: "PRD 5.1. Enforced in the scheduling tool, not just asked for." },
];

const SWITCHES = [
  { key: "use_llm_for_triage_steps", label: "Triage steps: LLM path",
    hint: "Off = fault-pattern lookup keyed on the real label slugs." },
  { key: "use_llm_for_decision_analysis", label: "Repair vs replace: LLM path",
    hint: "Off = age/cost heuristic. Run the same scenario both ways." },
];

async function renderKnobs() {
  const k = await (await fetch("/api/knobs")).json();
  const p = $("tab-knobs");
  p.innerHTML = "";
  const intro = el("div", "card");
  intro.appendChild(el("h4", null, "Open questions, as dials"));
  intro.appendChild(el("div", "note",
    "These are the PRD's undecided values. They are exposed rather than buried so you can see what is still an assumption."));
  p.appendChild(intro);

  const card = el("div", "card");
  KNOB_SPECS.forEach((spec) => {
    const wrap = el("div", "knob");
    const lab = el("label");
    lab.appendChild(el("span", null, spec.label));
    const val = el("b", null, spec.fmt(k[spec.key]));
    lab.appendChild(val);
    wrap.appendChild(lab);
    const input = el("input");
    input.type = "range"; input.min = spec.min; input.max = spec.max;
    input.step = spec.step; input.value = k[spec.key];
    input.addEventListener("input", () => { val.textContent = spec.fmt(input.value); });
    input.addEventListener("change", () => {
      fetch("/api/knobs", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [spec.key]: Number(input.value) }) });
    });
    wrap.appendChild(input);
    wrap.appendChild(el("div", "hint", spec.hint));
    card.appendChild(wrap);
  });
  p.appendChild(card);

  const abCard = el("div", "card");
  abCard.appendChild(el("h4", null, "LLM path vs rules-based fallback"));
  abCard.appendChild(el("div", "note", "PRD 4.1. Flip these and re-run the same scenario."));
  SWITCHES.forEach((spec) => {
    const wrap = el("div", "knob switch");
    const lab = el("label");
    const cb = el("input"); cb.type = "checkbox"; cb.checked = !!k[spec.key];
    cb.addEventListener("change", () => {
      fetch("/api/knobs", { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ [spec.key]: cb.checked }) });
    });
    lab.appendChild(cb);
    lab.appendChild(el("span", null, " " + spec.label));
    wrap.appendChild(lab);
    wrap.appendChild(el("div", "hint", spec.hint));
    abCard.appendChild(wrap);
  });
  p.appendChild(abCard);
}

/* ------------------------------------------------------------------ event stream */
function applyState(s) {
  if (!s) return;
  state = s;
  $("loopPill").textContent = s.loop_label || "Idle";
  $("loopPill").className = "pill " + (LOOP_COLOUR[s.loop] || "grey");
  $("iterPill").textContent = s.loop === "done" ? "—" : `iteration ${s.loop_iteration}`;
  $("costPill").textContent = "$" + Number(s.cost_usd || 0).toFixed(4);
  setAwaiting(s.awaiting_resident, s.auto_play);
  renderGates();
}

function handle(e) {
  switch (e.kind) {
    case "reset":
      $("thread").innerHTML = ""; $("trace").innerHTML = "";
      gatesHtml = { gate: null, ops: [], visits: [], closed: null, guardrails: [] };
      skillOut = { assessment: null, triage: null };
      state = {}; renderGates();
      break;

    case "scenario_started": {
      showScenarioCard(e.scenario);
      const iss = e.issue;
      $("residentName").textContent = iss.id;
      traceCard("evt exit open", "purple", "scenario", e.scenario.title,
        [el("div", "note", e.scenario.summary), pre(iss)], false);
      applyState(e.state);
      break;
    }

    case "loop_enter":
      { const b = el("div", "loop-band");
        b.appendChild(el("span", `pill ${LOOP_COLOUR[e.loop] || "grey"}`, e.loop));
        b.appendChild(el("span", null, e.label));
        $("trace").appendChild(b); scrollDown("traceBody"); applyState(e.state); }
      break;

    case "loop_exit": {
      const nodes = [pre(e)];
      const label = e.outcome || e.code || "exit";
      traceCard("exit", "purple", "loop exit", `${e.loop} → ${label}`, nodes, true);
      break;
    }

    case "tool_call":
      // The repair-vs-replace subagent's own lookups arrive on the same stream, tagged.
      traceCard("tool", e.iterum_tool ? (e.agent === "subagent" ? "blue" : "green") : "red",
        e.iterum_tool ? (e.agent === "subagent" ? "subagent tool" : "tool")
                      : "NOT AN ITERUM TOOL", e.tool,
        [pre(e.input)], false);
      // Keep the header counter live rather than only updating it at phase boundaries.
      if (typeof e.iteration === "number") {
        $("iterPill").textContent = `iteration ${e.iteration}`;
        if (e.loop) {
          state.loop = e.loop;
          $("loopPill").className = "pill " + (LOOP_COLOUR[e.loop] || "grey");
        }
      }
      break;

    case "tool_result": {
      const parsed = parseResult(e.result);
      if (e.tool === "assess_repair_vs_replace" && parsed && parsed.code) {
        skillOut.assessment = parsed;
        renderGates();
      }
      if (e.tool === "get_triage_steps" && parsed && (parsed.steps || parsed.fault_slug)) {
        skillOut.triage = parsed;
        traceCard("skill", "purple", "triage skill", e.tool, triageNodes(parsed), true);
      }
      // The raw payload still gets its own collapsed card - the readable view is an
      // addition, not a replacement, so nothing is hidden from the trace.
      traceCard("tool", "grey", "result", e.tool, [pre(e.result)], false);
      break;
    }

    case "reasoning_path":
      traceCard("tool", e.path === "llm" ? "blue" : "amber",
        e.path === "llm" ? "LLM call" : "fallback", e.tool,
        [el("div", "note", e.detail || (e.path === "llm"
          ? "Reasoning call to the model." : "Rules-based fallback path."))], false);
      break;

    case "guardrail":
      gatesHtml.guardrails.push({ rule: e.rule, detail: e.detail });
      traceCard("guard", "red", "guardrail", e.rule,
        [el("div", "note", e.detail)], true);
      renderGates();
      break;

    case "gate_check":
      traceCard(e.outcome === "deny" ? "guard" : "gateok",
        e.outcome === "deny" ? "red" : "green",
        e.outcome === "deny" ? "gate blocked" : "gate passed",
        `${e.tool} (${e.path})`, [el("div", "note", e.detail)], true);
      break;

    case "gate_opened":
      traceCard("gate", "amber", "awaiting human",
        e.gate === "engineer" ? "engineer confirmation" : "PM approval",
        [pre(e.context)], true);
      applyState({ ...state, pending_gate: { kind: e.gate, context: e.context } });
      break;

    case "gate_closed":
      traceCard("gateok", "green", "human decided", `${e.gate}: ${e.decision}`,
        [el("div", "note", e.note || "no note")], true);
      break;

    case "slot_proposed":
      traceCard("tool", "amber", `slot ${e.attempt}`, e.slot,
        [el("div", "note", `${e.rejections_so_far} rejected so far`)], false);
      break;

    case "resident_message":
      if (e.direction === "out") {
        bubble("out", e.text, "agent");
      } else {
        bubble("in", e.text, e.simulated ? "resident (simulated)" : "resident (you)");
        setAwaiting(false, state.auto_play);   // the reply landed; stop prompting
      }
      break;

    case "awaiting_resident":
      setAwaiting(true, e.auto_play);
      break;

    case "resident_timeout":
      plain("note", "Resident did not reply within the window.");
      break;

    case "agent_text":
      plain("agent-say", e.text);
      break;

    case "agent_thinking":
      plain("thinking", e.text);
      break;

    case "ops_message":
      gatesHtml.ops.push({ category: e.category, request: e.request });
      renderGates();
      break;

    case "visit":
      gatesHtml.visits = gatesHtml.visits.filter((v) => v.id !== e.visit.id).concat([e.visit]);
      renderGates();
      break;

    case "job_closed":
      gatesHtml.closed = { resolution: e.resolution, summary: e.summary };
      renderGates();
      break;

    case "phase_result":
      applyState(e.state);
      break;

    case "state":
    case "run_complete":
      if (e.summary) {
        traceCard("exit", "green", "run complete", "summary", [pre(e.summary)], true);
        if (e.summary.non_iterum_tool_calls?.length) {
          traceCard("guard", "red", "tool surface", "built-in tools were reached",
            [pre(e.summary.non_iterum_tool_calls)], true);
        }
      }
      applyState(e.state);
      running = false;
      break;

    case "run_incomplete":
      traceCard("err", "red", "incomplete", e.loop, [el("div", "note", e.detail)], true);
      break;

    case "error":
      traceCard("err", "red", "error", e.where, [el("div", "note", e.detail)], true);
      break;

    case "knobs":
      renderKnobs();
      break;
  }
}

function connect() {
  const src = new EventSource("/api/events");
  src.onmessage = (m) => { try { handle(JSON.parse(m.data)); } catch (err) { console.error(err, m.data); } };
  src.onerror = () => { /* EventSource retries on its own */ };
}

loadScenarios().then(renderKnobs).then(renderGates).then(connect);
