"""Project a run trace into a human review interface.

A TOOL, not production code.

THE ONE RULE THIS FILE OBEYS

It reads the trace and renders it. It does not open DesignState, does not parse a
fixture, and does not decide what any stage meant. If a fact is not in the trace
it does not appear in the UI - which is why `run_trace.py` records NOT_EXERCISED
nodes explicitly rather than omitting them. A stage missing from a review screen
reads as a stage that passed.

WHAT IT MUST NEVER IMPLY

    contract: ACCEPTED   schema, references and authority were satisfied
    human review         whether the engineering is any good

These are rendered as two separate badges on every node, and the second starts at
NOT_REVIEWED and is only ever set by the person reviewing. There is no automated
mechanical score anywhere in this file, and no model is asked to judge a design.

Self-contained: one HTML file, inline CSS and JS, no CDN and no framework. It has
to work over VS Code Remote SSH port forwarding, where an external fetch does not.
"""
from __future__ import annotations

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

VER3 = os.path.join(REPO, "ver3")
DEFAULT_OUT = os.path.join(VER3, "out", "review")

STATUS_CLASS = {
    "LIVE_DEEPSEEK": "live", "REPLAY": "replay", "DETERMINISTIC": "det",
  "EXECUTED": "det", "EXECUTED_NO_WRITE": "blocked",
  "DEVELOPMENT_FIXTURE": "absent",
    "NOT_EXERCISED": "none", "NOT_IMPLEMENTED": "absent",
    "BLOCKED_BY_UPSTREAM": "blocked",
}

CSS = """
:root{--bg:#0f1115;--panel:#171a21;--line:#252a34;--fg:#d8dde6;--dim:#8b93a3;
--ok:#3fa86b;--bad:#c0504d;--warn:#c8973f;--live:#4a7fd4;--replay:#6b5ea8;
--absent:#5a5f6b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.55 ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif}
header{padding:18px 22px;border-bottom:1px solid var(--line);background:var(--panel)}
h1{margin:0 0 4px;font-size:17px;font-weight:600}
.sub{color:var(--dim);font-size:12.5px}
.wrap{display:flex;gap:0;min-height:calc(100vh - 74px)}
nav{width:290px;border-right:1px solid var(--line);background:var(--panel);
padding:12px;overflow:auto}
main{flex:1;padding:22px;overflow:auto;max-width:1100px}
.node{display:block;width:100%;text-align:left;background:transparent;color:inherit;
border:1px solid var(--line);border-radius:7px;padding:9px 11px;margin-bottom:7px;
cursor:pointer;font:inherit}
.node:hover{border-color:#3a4150}
.node.sel{border-color:#5b7fbd;background:#1b2030}
.node .rid{font-weight:600;letter-spacing:.3px}
.node .ttl{color:var(--dim);font-size:12px;margin-top:2px}
.badges{margin-top:6px;display:flex;gap:5px;flex-wrap:wrap}
.b{font-size:10.5px;padding:1.5px 6px;border-radius:99px;border:1px solid}
.b.live{color:#9dc0ff;border-color:#2f4d80;background:#16203a}
.b.replay{color:#bfb3f0;border-color:#413a70;background:#1e1b33}
.b.det{color:#9fd8bb;border-color:#2b5c42;background:#152820}
.b.none{color:#9aa2b1;border-color:#3a3f4b;background:#1a1d24}
.b.absent{color:#a8adb8;border-color:#4a4f5b;background:#20242c}
.b.blocked{color:#e0b48a;border-color:#6b4a2a;background:#2a1f16}
.b.acc{color:#8fe0ae;border-color:#2b6b45;background:#13291d}
.b.rej{color:#f0a6a4;border-color:#7a3634;background:#2c1817}
.b.hr{color:#d9c07a;border-color:#6b5a2a;background:#26210f}
h2{font-size:15px;margin:26px 0 9px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h2:first-of-type{margin-top:0}
.grid{display:grid;grid-template-columns:170px 1fr;gap:5px 14px;font-size:13px}
.grid dt{color:var(--dim)}
.grid dd{margin:0;word-break:break-word}
/* pre-wrap, because the source request is prose: unwrapped it ran off the
   panel and the reviewer had to scroll sideways to read the request they are
   reviewing against. Long unbroken tokens (hashes, paths) still get to break. */
pre{background:#0b0d11;border:1px solid var(--line);border-radius:6px;padding:11px;
overflow:auto;max-height:420px;font-size:12px;line-height:1.5;
white-space:pre-wrap;overflow-wrap:anywhere}
details{border:1px solid var(--line);border-radius:6px;padding:9px 11px;margin:9px 0;
background:#12151b}
summary{cursor:pointer;color:var(--dim);font-size:12.5px}
.warnbox{border:1px solid #6b4a2a;background:#241a12;border-radius:6px;padding:11px 13px;
margin:12px 0;font-size:13px}
.okbox{border:1px solid #2b5c42;background:#132018;border-radius:6px;padding:11px 13px;
margin:12px 0;font-size:13px}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;background:#12151b}
.flow{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin:10px 0 4px}
.fnode{border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-size:12px;
background:#12151b;cursor:pointer}
.fnode.live{border-color:#2f4d80}.fnode.replay{border-color:#413a70}
.fnode.none{opacity:.55}.fnode.absent{opacity:.45;border-style:dashed}
.arrow{color:var(--dim)}
.shots{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:9px}
.shots figure{margin:0;border:1px solid var(--line);border-radius:6px;overflow:hidden;
background:#0b0d11}
.shots img{width:100%;display:block;cursor:pointer}
.shots figcaption{font-size:11px;color:var(--dim);padding:5px 7px;word-break:break-all}
select,textarea,button{font:inherit;background:#0e1116;color:var(--fg);
border:1px solid var(--line);border-radius:6px;padding:7px 9px}
textarea{width:100%;min-height:72px;resize:vertical}
button{cursor:pointer}
button.primary{background:#1e3a63;border-color:#2f4d80}
.dim{color:var(--dim)}
svg{background:#0b0d11;border:1px solid var(--line);border-radius:6px;max-width:100%}
"""

JS = r"""
const T = TRACE, R = {};
const $ = s => document.querySelector(s);
const esc = s => String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const key = n => T.benchmark_id + '::' + n.responsibility_id;

function loadReview(){ try{ Object.assign(R, JSON.parse(localStorage.getItem('assy-review')||'{}')); }catch(e){} }
function saveReview(){ localStorage.setItem('assy-review', JSON.stringify(R)); }
function verdictOf(n){ return (R[key(n)]||{}).verdict || 'NOT_REVIEWED'; }

function badge(cls, text){ return `<span class="b ${cls}">${esc(text)}</span>`; }

function sidebar(){
  $('#nav').innerHTML = T.nodes.map((n,i)=>`
    <button class="node" data-i="${i}">
      <div class="rid">${esc(n.responsibility_id.toUpperCase())}</div>
      <div class="ttl">${esc(n.title)}</div>
      <div class="badges">
        ${badge(STATUS_CLASS[n.status]||'none', n.status)}
        ${n.contract?badge(n.contract==='ACCEPTED'?'acc':'rej','contract: '+n.contract):''}
        ${badge('hr','review: '+verdictOf(n))}
      </div>
    </button>`).join('');
  document.querySelectorAll('.node').forEach(b=>b.onclick=()=>show(+b.dataset.i));
}

function flow(){
  return `<div class="flow">` + T.nodes.map((n,i)=>
    `<span class="fnode ${STATUS_CLASS[n.status]||'none'}" data-i="${i}"
      title="${esc(n.status)}">${esc(n.responsibility_id.toUpperCase())}</span>`
  ).join('<span class="arrow">→</span>') + `</div>`;
}

// What each status on THIS page means, derived from the statuses actually
// present. The banner used to explain REPLAY unconditionally - so a page whose
// nodes were DEVELOPMENT_FIXTURE showed a badge with no explanation beside a
// paragraph about a status that was nowhere on screen. A reviewer cannot weigh
// evidence whose provenance the page never names.
// Keyed on the STATUS VALUES the trace actually carries, not on the names of
// the Python constants that hold them. A first version keyed on `REPLAYED` and
// `LIVE_MODEL`; the values are `REPLAY` and `LIVE_DEEPSEEK`, so those entries
// matched nothing and the two REPLAY nodes on the BM-001 page went unexplained
// while the legend looked complete. `test_review_trace` now derives the
// required keys from STATUS_CLASS so a renamed status fails rather than
// silently dropping out of the legend.
const PROVENANCE_MEANING = {
  LIVE_DEEPSEEK: 'served by a live provider call in this run.',
  REPLAY: 'a recorded response replayed through the real parser and contracts. ' +
            'That is not live-model evidence.',
  DEVELOPMENT_FIXTURE: 'authored by hand to exercise the seam. No provider was ' +
            'contacted and no recorded response was served, so it is neither ' +
            'live nor a replay, and it answers no benchmark.',
  DETERMINISTIC: 'produced by a deterministic service, with no model involved.',
  EXECUTED: 'produced by a deterministic service - a solver or a CAD kernel - ' +
            'with no model involved.',
  EXECUTED_NO_WRITE: 'ran, but wrote nothing to state.',
  NOT_EXERCISED: 'did not run in this run.',
  NOT_IMPLEMENTED: 'not built. The node is present so its absence cannot read ' +
            'as a stage that passed.',
  BLOCKED_BY_UPSTREAM: 'could not run because something it depends on did not.'
};

function provenanceLegend(){
  const present = [...new Set(T.nodes.map(n=>n.status))].filter(s=>PROVENANCE_MEANING[s]);
  if(!present.length) return '';
  return 'What the statuses on this page mean:<br>' + present.map(s=>
    `<code>${esc(s)}</code> — ${PROVENANCE_MEANING[s]}`).join('<br>');
}

function kv(o){
  return '<dl class="grid">' + Object.entries(o).map(([k,v])=>
    `<dt>${esc(k)}</dt><dd>${v==null||v===''?'<span class="dim">—</span>':esc(v)}</dd>`
  ).join('') + '</dl>';
}

function reviewPanel(n){
  const r = R[key(n)]||{};
  return `<h2>${++SEC} · Human mechanical review</h2>
  <div class="warnbox">The system status above is a <b>contract</b> judgment —
  schema, references and authority. It is <b>not</b> a statement that the
  engineering is sound. That judgment is yours.</div>
  <div style="display:flex;gap:9px;align-items:flex-start;flex-wrap:wrap">
    <select id="rv">${['NOT_REVIEWED','PASS','FAIL','NEEDS_REVIEW'].map(v=>
      `<option ${r.verdict===v?'selected':''}>${v}</option>`).join('')}</select>
    <select id="rc">${['','mechanical concept','geometry','kinematics','load path',
      'manufacturability','assembly','parameter choice','missing information','other']
      .map(v=>`<option ${r.category===v?'selected':''}>${v||'(category)'}</option>`).join('')}</select>
  </div>
  <textarea id="rt" placeholder="What did you observe?">${esc(r.comment||'')}</textarea>
  <div style="margin-top:8px;display:flex;gap:8px">
    <button class="primary" id="rs">Save review</button>
    <button id="rx">Export all reviews (JSON)</button>
  </div>
  <div id="rmsg" class="dim" style="margin-top:6px"></div>`;
}

// Sections number themselves in the order they are EMITTED. They used to carry
// hardcoded numbers written for the fullest node - so a deterministic node, which
// has no prompt or raw response, rendered 1,2,3,4 and then 11, and the gap read
// as seven sections that failed to load rather than seven that do not apply.
let SEC = 0;
function section(t, body){
  const numbered = /^\d+ \u00b7 /.test(t) ? t.replace(/^\d+ \u00b7 /, ++SEC + ' \u00b7 ') : t;
  return `<h2>${numbered}</h2>${body}`;
}

function show(i){
  SEC = 0;
  const n = T.nodes[i];
  document.querySelectorAll('.node').forEach((b,j)=>b.classList.toggle('sel', j===i));
  let h = `<h1 style="margin:0 0 3px;font-size:19px">${esc(n.responsibility_id.toUpperCase())}
    <span class="dim" style="font-size:14px;font-weight:400"> · ${esc(n.title)}</span></h1>
    <div class="badges" style="margin:8px 0 14px">
      ${badge(STATUS_CLASS[n.status]||'none', n.status)}
      ${n.contract?badge(n.contract==='ACCEPTED'?'acc':'rej','contract: '+n.contract):''}
      ${badge('hr','human review: '+verdictOf(n))}
    </div>`;

  if(n.kind==='DETERMINISTIC' && (n.status||'').startsWith('EXECUTED')){
    const e=n.execution||{};
    h += section('1 · Deterministic execution', kv({
        'responsibility': e.responsibility_id, 'outcome': e.outcome,
        'input digest': (e.input_digest||'').slice(0,32),
        'wrote to state': e.patch_applied, 'evidence': e.evidence_id,
        'evidence validity': e.validity_of_evidence,
        'model provenance': 'none - this stage contacts no provider'}));
    if(n.settled){
      h += section('2 · Settlement', `<table><tr><th>parameter</th><th>symbol</th>
        <th>unit</th><th>value</th><th>solved by</th><th>validity</th></tr>` +
        Object.entries(n.settled).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${esc(v.symbol)}</td>
        <td>${esc(v.unit)}</td><td>${v.value==null?'<span class="dim">unsettled</span>':esc(v.value)}</td>
        <td>${esc(v.solved_by||'—')}</td><td>${esc(v.validity)}</td></tr>`).join('')+`</table>`);
      if(n.constraint_settlement) h += `<details><summary>constraint settlement</summary>
        <pre>${esc(JSON.stringify(n.constraint_settlement,null,1))}</pre></details>`;
    }
    if(n.signatures){
      h += section('2 · Compiled geometry', n.signatures.map(g=>`
        <div class="${g.validity==='STANDING'?'okbox':'warnbox'}">
          <b>${esc(g.entity_id)}</b> — ${g.validity==='STANDING'
            ? 'CURRENT for the present design state'
            : 'STALE: its premises changed after it was compiled, so it is history rather than current geometry'}
          <br>signature <code>${esc((g.signature_sha256||'').slice(0,32))}</code></div>
        <table><tr><th>body</th><th>volume mm3</th><th>solids</th><th>single connected</th></tr>` +
        (g.compiled_bodies||[]).map(b=>`<tr><td>${esc(b.body_id)}</td><td>${esc(b.volume)}</td>
          <td>${esc(b.solid_count)}</td><td>${esc(b.single_connected_solid)}</td></tr>`).join('')+
        `</table>
        <table><tr><th>statement</th><th>realizes feature</th></tr>` +
        Object.entries(g.feature_map||{}).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${esc(v)}</td></tr>`).join('')+
        `</table>`).join(''));
    }
    h += section('3 · Every recorded run', `<pre>${esc(JSON.stringify(n.deterministic_runs,null,1))}</pre>`);
    $('#main').innerHTML = h + reviewPanel(n); wireReview(n); return;
  }
  if(n.kind==='MODEL' && n.realization_graph){
    h += section('1 · Realization graph — why each feature exists', `<table>
      <tr><th>realization</th><th>discharges obligation</th><th>via feature</th>
      <th>verification predicate</th><th>validity</th></tr>` +
      n.realization_graph.map(r=>`<tr><td>${esc(r.realization)}</td>
      <td>${(r.addresses_obligations||[]).map(esc).join(', ')}</td>
      <td>${(r.participating_features||[]).map(esc).join(', ')}</td>
      <td>${esc(r.verification_predicate)}</td><td>${esc(r.validity)}</td></tr>`).join('')+`</table>`);
    h += section('2 · Features', `<table><tr><th>feature</th><th>on body</th><th>kind</th><th>validity</th></tr>`+
      n.feature_graph.map(f=>`<tr><td>${esc(f.feature)}</td><td>${esc(f.body)}</td>
      <td>${esc(f.feature_kind)}</td><td>${esc(f.validity)}</td></tr>`).join('')+`</table>`);
    h += section('3 · Construction program (each body in its own frame)', `<table>
      <tr><th>statement</th><th>body</th><th>operation</th><th>operands</th><th>realizes</th><th>validity</th></tr>`+
      n.construction_program.map(c=>`<tr><td>${esc(c.statement)}</td><td>${esc(c.body)}</td>
      <td>${esc(c.operation)}</td><td>${(c.operands||[]).map(esc).join(', ')||'—'}</td>
      <td>${esc(c.feature||'—')}</td><td>${esc(c.validity)}</td></tr>`).join('')+`</table>`);
    if(n.state_diff) h += section('4 · State change', `<pre>${esc(JSON.stringify(n.state_diff,null,1))}</pre>`);
    if(n.parsed) h += `<details><summary>authored response</summary><pre>${esc(JSON.stringify(n.parsed,null,1))}</pre></details>`;
    $('#main').innerHTML = h + reviewPanel(n); wireReview(n); return;
  }
  if(n.status==='NOT_IMPLEMENTED'){
    h += `<div class="warnbox"><b>This part of the pipeline does not exist.</b><br>
      ${esc(n.reason||'')}${n.declared_families&&n.declared_families.length?
      `<br><br>Declared in the contracts and written by no code:
       <code>${n.declared_families.map(esc).join(', ')}</code>`:''}</div>`;
    $('#main').innerHTML = h + reviewPanel(n); wireReview(n); return;
  }
  if(n.status==='NOT_EXERCISED'||n.status==='BLOCKED_BY_UPSTREAM'){
    h += `<div class="warnbox"><b>Not exercised in this run.</b><br>${esc(n.reason||'')}</div>`;
    $('#main').innerHTML = h + reviewPanel(n); wireReview(n); return;
  }

  const cvw = n.consumer_view||{};
  h += section('1 · Input state (before)', `<pre>${esc(JSON.stringify(n.state_before,null,1))}</pre>`);
  h += section('2 · Consumer view — what this responsibility was allowed to see', kv({
      'view status': cvw.status,
      'semantic families': (cvw.families||[]).join(', '),
      'namespace occupancy': JSON.stringify(cvw.namespace_occupancy||{}),
      'entities carried': JSON.stringify(cvw.counts||{}),
    }) + (Object.keys(cvw.namespace_occupancy||{}).length
      ? `<div class="okbox">Occupancy is <b>identity only</b> — which ids are taken.
         The semantic content of those entities is deliberately not carried.</div>` : ''));

  if(n.prompt_text!=null){
    h += section('3 · Actual model prompt',
      `<div class="dim" style="margin-bottom:6px">${n.prompt_chars} chars · pairing
       <code>${esc(n.prompt_pairing)}</code></div>
       <details open><summary>prompt as sent</summary><pre>${esc(n.prompt_text)}</pre></details>`);
  }
  if(n.raw_response!=null){
    h += section('4 · Raw model response',
      `<div class="dim" style="margin-bottom:6px">sha256 <code>${esc((n.raw_response_sha256||'').slice(0,32))}</code></div>
       <details><summary>raw response</summary><pre>${esc(n.raw_response)}</pre></details>`);
  }
  h += section('5 · Parsed output', Object.keys(n.parsed_collections||{}).length
      ? `<table><tr><th>collection</th><th>items</th></tr>` +
        Object.entries(n.parsed_collections).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join('') +
        `</table><details><summary>parsed JSON</summary><pre>${esc(JSON.stringify(n.parsed,null,1))}</pre></details>`
      : '<div class="dim">nothing parsed</div>');

  const probs = n.contract_problems||[];
  h += section('6 · Contract judgment (deterministic)',
    (n.contract==='ACCEPTED'
      ? `<div class="okbox">Patch <b>accepted</b>: schema, references and authority satisfied.
         This is not a mechanical-correctness claim.</div>`
      : `<div class="warnbox">Patch <b>rejected</b> — ${probs.length} problem(s).</div>`) +
    (probs.length?`<pre>${esc(probs.join('\n'))}</pre>`:'') +
    ((n.declared_incompleteness||[]).length
      ? `<details><summary>declared incompleteness (${n.declared_incompleteness.length})</summary>
         <pre>${esc(n.declared_incompleteness.join('\n'))}</pre></details>`:''));

  h += section('7 · State change', (n.state_diff&&n.state_diff.added_total)
      ? `<table><tr><th>family</th><th>created</th></tr>` +
        Object.entries(n.state_diff.added).map(([f,ids])=>
          `<tr><td>${esc(f)}</td><td>${ids.map(esc).join(', ')}</td></tr>`).join('') + `</table>`
      : '<div class="dim">no entity entered state from this execution</div>');

  const mrr = (n.model_run_records||[])[0]||{};
  h += section('8 · Provenance', kv({
      'stage owner (write authority)': n.stage_owner_id,
      'responsibility (reasoning pass)': n.responsibility_id,
      'response source': n.response_source,
      'provider': n.provider_id,
      'requested model': mrr.model_id_requested,
      'served model': mrr.model_id_served,
      'execution status': n.execution_status,
      'refinement only': n.refinement_only,
    }) + (mrr.model_id_served && mrr.model_id_requested !== mrr.model_id_served
      ? `<div class="warnbox">Requested and served model differ. Recorded, not assumed equivalent.</div>`:''));

  $('#main').innerHTML = h + reviewPanel(n);
  wireReview(n);
}

function wireReview(n){
  const k = key(n);
  $('#rs').onclick = ()=>{
    R[k] = {verdict:$('#rv').value, category:$('#rc').value, comment:$('#rt').value,
            run_id:T.run_id, benchmark_id:T.benchmark_id,
            responsibility_id:n.responsibility_id, repo_commit:T.repo_commit};
    saveReview(); sidebar(); $('#rmsg').textContent='saved locally';
  };
  $('#rx').onclick = ()=>{
    const blob = new Blob([JSON.stringify({schema:'assy-human-review/1',
      benchmark_id:T.benchmark_id, repo_commit:T.repo_commit, reviews:R}, null, 1)],
      {type:'application/json'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob); a.download='human_review-'+T.benchmark_id+'.json';
    document.body.appendChild(a); a.click(); a.remove();
    $('#rmsg').textContent='exported — save it into ver3/out/review/';
  };
}

function overview(){
  SEC = 0;
  const counted = {};
  T.nodes.forEach(n=>counted[n.status]=(counted[n.status]||0)+1);
  let h = `<h1 style="margin:0 0 3px;font-size:19px">${esc(T.benchmark_id)} — pipeline</h1>
   <div class="dim" style="margin-bottom:12px">run <code>${esc(T.run_id)}</code> ·
   commit <code>${esc((T.repo_commit||'').slice(0,12))}</code>${
     T.source_sha256 ? ' · source sha <code>'+esc(T.source_sha256.slice(0,16))+'</code>' : ''
   }</div>`;
  h += flow();
  h += `<div class="warnbox"><b>Read this before reviewing.</b><br>
    A green <i>contract</i> badge means the response satisfied schema, references and
    authority. It is not a claim that the mechanism, proportions, load path, kinematics
    or manufacturability are sound — those are exactly what you are being asked to judge,
    and every node starts at <code>NOT_REVIEWED</code>.<br><br>
    ${provenanceLegend()}</div>`;
  h += section('Source request', `<pre>${esc(T.source_text)}</pre>`);
  h += section('Status summary', `<table><tr><th>status</th><th>nodes</th></tr>` +
    Object.entries(counted).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join('')+`</table>`);
  h += section('Final committed state', `<table><tr><th>family</th><th>entities</th></tr>` +
    Object.entries(T.final_state||{}).map(([f,ids])=>
      `<tr><td>${esc(f)}</td><td>${ids.length} <span class="dim">${ids.map(esc).join(', ')}</span></td></tr>`
    ).join('')+`</table>`);
  h += cadSection();
  $('#main').innerHTML = h;
  document.querySelectorAll('.fnode').forEach(e=>e.onclick=()=>show(+e.dataset.i));
}

function cadSection(){
  const rc = T.reference_cad||{};
  const refs = rc.references||[];
  let h = `<h2>CAD — reference geometry</h2>
  <div class="warnbox"><b>This CAD was not produced by the pipeline.</b><br>
   It is hand-authored reference geometry under
   <code>ver3/cad_validation/</code>, built by scripts that call cadquery directly.
   They import no part of <code>assy_v3</code> and read no DesignState, so no body or
   feature below resolves to a canonical design entity id
   (<code>traceable_to_design_entities: false</code>).<br><br>
   The production pipeline has <b>no</b> embodiment, solver, construction-program or
   CAD-build stage — see the <code>S05</code> and <code>CAD</code> nodes.</div>`;
  if(!refs.length) return h + '<div class="dim">no reference CAD for this benchmark</div>';
  refs.forEach(r=>{
    h += `<h2 style="font-size:13.5px;border:0;margin:16px 0 6px">${esc(r.reference_id)}</h2>`;
    h += `<div class="dim" style="margin-bottom:7px">${r.step_files.length} STEP ·
          ${r.screenshots.length} render(s)</div>`;
    if(r.step_files.length) h += `<details><summary>authoritative STEP artifacts (not viewable in browser)</summary>
      <pre>${r.step_files.map(esc).join('\n')}</pre></details>`;
    if(r.screenshots.length){
      h += `<div class="shots">` + r.screenshots.slice(0,60).map(p=>
        `<figure><img loading="lazy" src="${esc(rel(p))}" onclick="window.open(this.src)">
         <figcaption>${esc(p.split('/').pop())}</figcaption></figure>`).join('') + `</div>`;
      if(r.screenshots.length>60) h+=`<div class="dim">…${r.screenshots.length-60} more not shown</div>`;
    }
  });
  return h;
}
function rel(p){ return '../../../' + p.replace(/^ver3\//,'ver3/'); }

loadReview();
sidebar();
$('#home').onclick = overview;
overview();
"""


def build(trace: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASSY design review — %s</title>
<style>%s</style></head>
<body>
<header>
  <h1>ASSY — human design review</h1>
  <div class="sub">System/contract status and human mechanical judgment are shown
  separately, and never merged. <button id="home" style="margin-left:10px">Overview</button></div>
</header>
<div class="wrap"><nav id="nav"></nav><main id="main"></main></div>
<script>const TRACE = %s;
const STATUS_CLASS = %s;
%s</script>
</body></html>
""" % (html.escape(trace["benchmark_id"]), CSS,
       json.dumps(trace), json.dumps(STATUS_CLASS), JS)
    path = os.path.join(out_dir, "index.html")
    with open(path, "w") as fh:
        fh.write(page)
    return path


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", default="BM-001")
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    trace_path = os.path.join(args.out, "trace-%s.json" % args.case)
    if not os.path.isfile(trace_path):
        print("no trace at %s - run ver3/tools/run_trace.py first" % trace_path)
        return 1
    with open(trace_path) as fh:
        trace = json.load(fh)
    path = build(trace, args.out)
    print("wrote %s" % os.path.relpath(path, REPO))
    print("serve with:  python -m http.server 8000   (from %s)" % REPO)
    print("then open :  http://localhost:8000/%s"
          % os.path.relpath(path, REPO).replace(os.sep, "/"))
    return 0


if __name__ == "__main__":                                       # pragma: no cover
    raise SystemExit(main())
