/* ==========================================================================
   mdkg v0.1 explorer
   Offline single-page application over the generated JSON datasets.
   Depends only on the locally vendored Cytoscape.js. No CDN, no external API.
   ========================================================================== */
'use strict';

/* --------------------------------------------------------------------------
   1. State and data loading
   -------------------------------------------------------------------------- */

const DATASETS = [
  'overview', 'ontology_graph', 'function_behavior_graph', 'machine_elements_graph',
  'claims_graph', 'evidence_graph', 'alignments_graph', 'substitutions_graph',
  'rules', 'coverage', 'search_index'
];

const STATE = {
  data: {},
  view: 'overview',
  showKo: false,
  sourceFilter: 'all',
  graphs: {},            // live GraphView instances by view id
  selection: {}          // per-view selected record id
};

const NOT_STATED = 'Not stated by the source';

/* --------------------------------------------------------------------------
   2. Small helpers
   -------------------------------------------------------------------------- */

function esc(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** Render a value, or an explicit "not stated" marker — never a blank. */
function orMissing(value, marker) {
  if (value === null || value === undefined || value === '' ||
      (Array.isArray(value) && value.length === 0)) {
    return `<span class="missing">${esc(marker || NOT_STATED)}</span>`;
  }
  return esc(value);
}

function num(n) { return (n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US'); }

function titleCase(slug) {
  return String(slug).replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function download(filename, text, mime) {
  const blob = new Blob([text], { type: mime || 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

let toastTimer = null;
function toast(message) {
  const node = document.getElementById('toast');
  node.textContent = message;
  node.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.hidden = true; }, 2600);
}

/** Label honouring the Korean-labels toggle. */
function labelOf(record) {
  const base = record.label || record.id || '';
  if (STATE.showKo && record.ko) return `${base} · ${record.ko}`;
  return base;
}

/* --------------------------------------------------------------------------
   3. Epistemic badges — status is always visible, never colour-only
   -------------------------------------------------------------------------- */

const PROVENANCE_BADGE = {
  SourceDerivedValue:       ['badge-source', 'Source-derived'],
  NormalizedInterpretation: ['badge-normalized', 'Normalized interpretation'],
  EngineeringInference:     ['badge-inference', 'Engineering inference'],
  UserDefinedWeight:        ['badge-neutral', 'User-defined weight'],
  ComputedResult:           ['badge-neutral', 'Computed result']
};

const REVIEW_BADGE = {
  NeedsReview:            ['badge-review', 'NeedsReview'],
  HumanVerified:          ['badge-verified', 'HumanVerified'],
  Rejected:               ['badge-rejected', 'Rejected'],
  Normalized:             ['badge-normalized', 'Normalized'],
  AutomaticallyExtracted: ['badge-neutral', 'Automatically extracted']
};

const INTEGRITY_BADGE = {
  'reliable':           ['badge-integrity-reliable', 'Text reliable'],
  'partial-glyph-loss': ['badge-integrity-partial', 'Partial glyph loss'],
  'glyph-mismapped':    ['badge-integrity-mismapped', 'Glyph-mismapped — do not quote'],
  'unverified':         ['badge-neutral', 'Integrity unverified']
};

const AUTHORITY_BADGE = {
  'mdcore:RequiresExternalStandard':     'External standard required',
  'mdcore:RequiresManufacturerData':     'Manufacturer data required',
  'mdcore:RequiresCompanySpecification': 'Company specification required',
  'mdcore:RequiresExperimentalProtocol': 'Experimental protocol required',
  'mdcore:RequiresEngineeringReview':    'Engineering review required'
};

function badge(cls, text) { return `<span class="badge ${cls}">${esc(text)}</span>`; }

function provenanceBadge(kind) {
  const spec = PROVENANCE_BADGE[kind] || ['badge-neutral', kind || 'Unspecified provenance'];
  return badge(spec[0], spec[1]);
}
function reviewBadge(state) {
  const spec = REVIEW_BADGE[state] || ['badge-neutral', state || 'Unknown review state'];
  return badge(spec[0], spec[1]);
}
function integrityBadge(status) {
  const spec = INTEGRITY_BADGE[status] || ['badge-neutral', status || 'unknown'];
  return badge(spec[0], spec[1]);
}
function authorityBadges(list) {
  return (list || []).map(a => badge('badge-authority', AUTHORITY_BADGE[a] || a)).join('');
}

/* --------------------------------------------------------------------------
   4. Detail panel
   -------------------------------------------------------------------------- */

function showDetail(title, html) {
  document.getElementById('detail-title').textContent = title;
  document.getElementById('detail-body').innerHTML = html;
  document.getElementById('detail-panel').hidden = false;
  document.getElementById('detail-body').scrollTop = 0;
  wireCrossLinks(document.getElementById('detail-body'));
}
function hideDetail() { document.getElementById('detail-panel').hidden = true; }

function section(heading, body) {
  if (!body) return '';
  return `<div class="dsec"><h4>${esc(heading)}</h4>${body}</div>`;
}

function fields(pairs) {
  const rows = pairs
    .filter(p => p && p[1] !== undefined)
    .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v === null || v === '' ? orMissing(null) : v}</dd>`)
    .join('');
  return rows ? `<dl class="dfield">${rows}</dl>` : '';
}

function list(items, renderer) {
  if (!items || !items.length) return '';
  return `<ul class="dlist">${items.map(renderer || (i => `<li>${esc(i)}</li>`)).join('')}</ul>`;
}

/** Cross-links: [data-goto="view:id"] jumps to another view and selects a record. */
function wireCrossLinks(root) {
  root.querySelectorAll('[data-goto]').forEach(node => {
    node.addEventListener('click', ev => {
      ev.preventDefault();
      const [view, ...rest] = node.getAttribute('data-goto').split(':');
      navigate(view, rest.join(':'));
    });
  });
}
function linkTo(view, id, text) {
  return `<a href="#" data-goto="${esc(view)}:${esc(id)}">${esc(text || id)}</a>`;
}

/* --------------------------------------------------------------------------
   5. Graph view
   -------------------------------------------------------------------------- */

/** Category → shape + glyph. Shape carries meaning so colour never has to. */
const CAT_SHAPE = {
  structure: 'round-rectangle', function: 'diamond', behavior: 'hexagon',
  effect: 'octagon', condition: 'rectangle', requirement: 'tag',
  failure: 'triangle', verification: 'vee', decision: 'pentagon',
  substitution: 'barrel', rule: 'rhomboid', evidence: 'ellipse',
  claim: 'round-rectangle', alternative: 'pentagon', element: 'rectangle',
  family: 'round-rectangle', vocabulary: 'concave-hexagon',
  source: 'round-rectangle', other: 'ellipse'
};
const CAT_GLYPH = {
  structure: '▭', function: '◆', behavior: '⬡', effect: '⬢', condition: '▬',
  requirement: '⚑', failure: '▲', verification: '⌄', decision: '⬟',
  substitution: '⬓', rule: '▰', evidence: '●', claim: '▭', alternative: '⬟',
  element: '▬', family: '▭', vocabulary: '◇', source: '▭', other: '○'
};
function catColor(cat) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue('--c-' + cat).trim() || '#7b8797';
}

const EDGE_STYLE = {
  taxonomy:    { line: 'solid',  color: '#5c6b7d', width: 1.6, arrow: 'triangle' },
  property:    { line: 'dashed', color: '#8b93a1', width: 1.2, arrow: 'vee' },
  fbs:         { line: 'solid',  color: '#2f7d72', width: 2.0, arrow: 'triangle' },
  effect:      { line: 'dotted', color: '#1c6b8c', width: 1.6, arrow: 'vee' },
  condition:   { line: 'dotted', color: '#8a6d3b', width: 1.6, arrow: 'vee' },
  failure:     { line: 'solid',  color: '#a83232', width: 1.6, arrow: 'triangle' },
  verification:{ line: 'solid',  color: '#3f7d4c', width: 1.6, arrow: 'triangle' },
  evidence:    { line: 'solid',  color: '#56616e', width: 1.4, arrow: 'triangle' },
  aboutness:   { line: 'dashed', color: '#2d5f88', width: 1.2, arrow: 'vee' },
  structure:   { line: 'solid',  color: '#66707c', width: 1.4, arrow: 'triangle' },
  realisation: { line: 'dashed', color: '#9c5b2b', width: 1.5, arrow: 'vee' },
  alignment:   { line: 'solid',  color: '#6a5a8c', width: 2.0, arrow: 'triangle' },
  substitution:{ line: 'solid',  color: '#8c4a6b', width: 2.4, arrow: 'triangle' }
};

/** Above this many nodes the view starts narrowed and warns the user. */
const LARGE_GRAPH_THRESHOLD = 180;

class GraphView {
  constructor(mountId, dataset, options) {
    this.mountId = mountId;
    this.dataset = dataset;
    this.opts = Object.assign({ layout: 'cose', nodeLimit: 400 }, options || {});
    this.activeCats = new Set(dataset.meta.categories);
    this.activeKinds = new Set(dataset.meta.edge_kinds);
    this.activeNodeTypes = new Set(this._nodeTypes());
    this.hideIsolated = dataset.meta.isolated_node_count > 0;
    this.groupByModule = false;
    this.focusId = null;
    this.depth = 1;
    this.nodeLimit = this.opts.nodeLimit;
    this.overrideLimit = false;
    this.cy = null;
  }

  _nodeTypes() {
    const types = new Set();
    this.dataset.nodes.forEach(n => { if (n.data.nodeType) types.add(n.data.nodeType); });
    return Array.from(types).sort();
  }

  /* ----- markup ----- */
  toolbarHtml() {
    const meta = this.dataset.meta;
    const catChips = meta.categories.map(c =>
      `<button class="chip" role="switch" aria-pressed="true" data-cat="${esc(c)}">
         <span class="chip-glyph" aria-hidden="true">${CAT_GLYPH[c] || '○'}</span>${esc(titleCase(c))}
       </button>`).join('');
    const kindChips = meta.edge_kinds.map(k =>
      `<button class="chip" role="switch" aria-pressed="true" data-kind="${esc(k)}">${esc(titleCase(k))}</button>`).join('');
    const typeChips = this._nodeTypes().map(t =>
      `<button class="chip" role="switch" aria-pressed="true" data-ntype="${esc(t)}">${esc(titleCase(t))}</button>`).join('');

    return `
    <details class="filters" open>
      <summary>Graph filters &amp; controls</summary>
      <div class="filters-body">
        <div class="fgroup"><label class="flabel">Node category</label><div class="chips">${catChips}</div></div>
        ${typeChips ? `<div class="fgroup"><label class="flabel">Node type</label><div class="chips">${typeChips}</div></div>` : ''}
        <div class="fgroup"><label class="flabel">Relation kind</label><div class="chips">${kindChips}</div></div>
        <div class="fgroup">
          <label class="flabel">Display</label>
          <div class="btn-row">
            <label class="ctrl"><input type="checkbox" class="g-hide-isolated" ${this.hideIsolated ? 'checked' : ''}> Hide isolated</label>
            <label class="ctrl"><input type="checkbox" class="g-group-module"> Group by module</label>
          </div>
        </div>
        <div class="fgroup">
          <label class="flabel">Layout</label>
          <div class="btn-row">
            <select class="g-layout">
              <option value="cose">Force (cose)</option>
              <option value="breadthfirst">Hierarchy</option>
              <option value="concentric">Concentric</option>
              <option value="circle">Circle</option>
              <option value="grid">Grid</option>
            </select>
            <label class="ctrl">Max nodes
              <input type="number" class="g-limit" min="20" max="2000" step="20" value="${this.nodeLimit}">
            </label>
          </div>
        </div>
        <div class="fgroup">
          <label class="flabel">Focus</label>
          <div class="btn-row">
            <label class="ctrl">Depth
              <select class="g-depth"><option value="1">1</option><option value="2">2</option><option value="3">3</option></select>
            </label>
            <button class="btn g-expand" disabled>Expand neighbours</button>
            <button class="btn g-clear-focus" disabled>Clear focus</button>
          </div>
        </div>
        <div class="fgroup">
          <label class="flabel">Actions</label>
          <div class="btn-row">
            <button class="btn g-fit">Fit</button>
            <button class="btn g-reset">Reset layout</button>
            <button class="btn g-full">Full screen</button>
            <button class="btn g-png">Export PNG</button>
            <button class="btn g-json">Export JSON</button>
          </div>
        </div>
      </div>
    </details>
    <div class="g-warning-slot"></div>
    <div class="graph-canvas" id="${esc(this.mountId)}"><div class="graph-empty" hidden></div></div>
    <div class="legend">${this.legendHtml()}</div>
    ${meta.notes && meta.notes.length ? `<div class="graph-note">${meta.notes.map(n => '· ' + esc(n)).join('<br>')}</div>` : ''}
    <div class="graph-note g-stats"></div>
    <div class="graph-note g-zoom-hint"></div>`;
  }

  legendHtml() {
    const cats = (this.dataset.meta.legend || []).map(item =>
      `<span class="legend-item">
         <span class="legend-swatch" style="background:${esc(catColor(item.cat))}"></span>
         <span class="legend-glyph" aria-hidden="true">${esc(item.glyph || '')}</span>
         ${esc(item.label)}
       </span>`).join('');
    const kinds = (this.dataset.meta.edge_kinds || []).map(k => {
      const s = EDGE_STYLE[k] || EDGE_STYLE.taxonomy;
      return `<span class="legend-item">
        <svg width="26" height="10" aria-hidden="true"><line x1="1" y1="5" x2="25" y2="5"
          stroke="${esc(s.color)}" stroke-width="${s.width}"
          stroke-dasharray="${s.line === 'dashed' ? '5,3' : s.line === 'dotted' ? '2,3' : '0'}"/></svg>
        ${esc(titleCase(k))}</span>`;
    }).join('');
    return cats + '<span class="legend-sep"></span>' + kinds;
  }

  /* ----- data selection ----- */
  visibleElements() {
    const nodes = this.dataset.nodes.filter(n => {
      const d = n.data;
      if (!this.activeCats.has(d.cat)) return false;
      if (d.nodeType && !this.activeNodeTypes.has(d.nodeType)) return false;
      if (STATE.sourceFilter !== 'all' && d.docId && d.docId !== STATE.sourceFilter) return false;
      return true;
    });
    let ids = new Set(nodes.map(n => n.data.id));

    let edges = this.dataset.edges.filter(e =>
      this.activeKinds.has(e.data.kind) && ids.has(e.data.source) && ids.has(e.data.target));

    // Focus mode: keep only the focused node's N-hop neighbourhood.
    if (this.focusId && ids.has(this.focusId)) {
      const keep = new Set([this.focusId]);
      let frontier = [this.focusId];
      for (let d = 0; d < this.depth; d++) {
        const next = [];
        edges.forEach(e => {
          if (keep.has(e.data.source) && !keep.has(e.data.target)) { keep.add(e.data.target); next.push(e.data.target); }
          if (keep.has(e.data.target) && !keep.has(e.data.source)) { keep.add(e.data.source); next.push(e.data.source); }
        });
        frontier = next;
        if (!frontier.length) break;
      }
      ids = keep;
      edges = edges.filter(e => ids.has(e.data.source) && ids.has(e.data.target));
    }

    let visibleNodes = nodes.filter(n => ids.has(n.data.id));

    if (this.hideIsolated) {
      const connected = new Set();
      edges.forEach(e => { connected.add(e.data.source); connected.add(e.data.target); });
      visibleNodes = visibleNodes.filter(n => connected.has(n.data.id));
      ids = new Set(visibleNodes.map(n => n.data.id));
      edges = edges.filter(e => ids.has(e.data.source) && ids.has(e.data.target));
    }

    // Node-count guard: keep the most connected nodes rather than an arbitrary slice.
    let truncated = 0;
    if (!this.overrideLimit && visibleNodes.length > this.nodeLimit) {
      const degree = {};
      edges.forEach(e => {
        degree[e.data.source] = (degree[e.data.source] || 0) + 1;
        degree[e.data.target] = (degree[e.data.target] || 0) + 1;
      });
      const ranked = visibleNodes.slice().sort((a, b) =>
        (degree[b.data.id] || 0) - (degree[a.data.id] || 0) ||
        a.data.id.localeCompare(b.data.id));
      truncated = visibleNodes.length - this.nodeLimit;
      visibleNodes = ranked.slice(0, this.nodeLimit);
      ids = new Set(visibleNodes.map(n => n.data.id));
      edges = edges.filter(e => ids.has(e.data.source) && ids.has(e.data.target));
    }

    // Optional compound grouping by defining module / namespace.
    const extra = [];
    if (this.groupByModule) {
      const parents = new Set();
      visibleNodes.forEach(n => {
        const key = n.data.module || (String(n.data.id).split(':')[0] + ' (namespace)');
        n.data.parent = 'grp:' + key;
        parents.add(key);
      });
      parents.forEach(key => extra.push({
        data: { id: 'grp:' + key, label: key, cat: 'other', isGroup: true }
      }));
    } else {
      visibleNodes.forEach(n => { delete n.data.parent; });
    }

    return { nodes: extra.concat(visibleNodes), edges, truncated };
  }

  stylesheet() {
    const styles = [
      {
        selector: 'node',
        style: {
          'label': ele => labelOf(ele.data()),
          'font-size': 9, 'font-family': 'system-ui, sans-serif',
          'color': '#16202c', 'text-valign': 'bottom', 'text-halign': 'center',
          'text-margin-y': 3, 'text-wrap': 'wrap', 'text-max-width': 110,
          'text-background-color': '#ffffff', 'text-background-opacity': .8,
          'text-background-padding': 1,
          'width': 20, 'height': 20,
          'border-width': 1.5, 'border-color': '#16202c',
          'background-color': ele => catColor(ele.data('cat') || 'other'),
          'shape': ele => CAT_SHAPE[ele.data('cat')] || 'ellipse'
        }
      },
      { selector: 'node[?isGroup]', style: {
          'background-opacity': .06, 'background-color': '#1f4f82', 'border-style': 'dashed',
          'border-color': '#5c6b7d', 'border-width': 1, 'shape': 'round-rectangle',
          'text-valign': 'top', 'font-size': 10, 'color': '#41505f', 'padding': 12 } },
      // Individuals get a double border so class vs individual is legible without colour.
      { selector: 'node[nodeType="individual"]', style: { 'border-width': 3, 'border-style': 'double' } },
      { selector: 'node[?bridge]', style: { 'border-style': 'dashed', 'opacity': .75 } },
      { selector: 'node:selected', style: {
          'border-width': 4, 'border-color': '#c26a00', 'width': 28, 'height': 28,
          'font-size': 11, 'z-index': 99 } },
      { selector: 'node.faded', style: { 'opacity': .18 } },
      { selector: 'edge', style: {
          'curve-style': 'bezier', 'target-arrow-shape': 'triangle',
          'arrow-scale': .8, 'width': 1.4, 'line-color': '#5c6b7d',
          'target-arrow-color': '#5c6b7d', 'font-size': 8, 'color': '#41505f',
          'text-background-color': '#ffffff', 'text-background-opacity': .85,
          'text-background-padding': 1, 'opacity': .85 } },
      { selector: 'edge:selected', style: {
          'width': 3.4, 'line-color': '#c26a00', 'target-arrow-color': '#c26a00',
          'label': ele => ele.data('label'), 'z-index': 99, 'opacity': 1 } },
      { selector: 'edge.faded', style: { 'opacity': .08 } }
    ];
    Object.keys(EDGE_STYLE).forEach(kind => {
      const s = EDGE_STYLE[kind];
      styles.push({
        selector: `edge[kind="${kind}"]`,
        style: {
          'line-color': s.color, 'target-arrow-color': s.color,
          'target-arrow-shape': s.arrow, 'width': s.width, 'line-style': s.line
        }
      });
    });
    return styles;
  }

  layoutConfig(name) {
    const base = { name: name, animate: false, fit: true, padding: 28 };
    if (name === 'cose') {
      return Object.assign(base, {
        nodeRepulsion: 7000, idealEdgeLength: 62, nodeOverlap: 12,
        gravity: 0.9, numIter: 1100, randomize: false, componentSpacing: 32
      });
    }
    if (name === 'breadthfirst') return Object.assign(base, { directed: true, spacingFactor: 1.1, grid: true });
    if (name === 'concentric') {
      return Object.assign(base, {
        concentric: n => n.degree(), levelWidth: () => 3, minNodeSpacing: 22
      });
    }
    return base;
  }

  mount() {
    const container = document.getElementById(this.mountId);
    if (!container) return;
    const { nodes, edges, truncated } = this.visibleElements();

    const warnSlot = container.parentElement.querySelector('.g-warning-slot');
    if (warnSlot) {
      warnSlot.innerHTML = truncated > 0
        ? `<div class="graph-warning">
             <strong>Graph narrowed.</strong> ${num(truncated)} node(s) beyond the
             ${num(this.nodeLimit)}-node limit are hidden; the most connected nodes are shown.
             Narrow the filters, focus on a node, or
             <button class="btn g-override" type="button">render all anyway</button>.
           </div>` : '';
      const overrideBtn = warnSlot.querySelector('.g-override');
      if (overrideBtn) overrideBtn.addEventListener('click', () => {
        this.overrideLimit = true; this.mount();
      });
    }

    const emptyNode = container.querySelector('.graph-empty');
    if (this.cy) { this.cy.destroy(); this.cy = null; }
    container.innerHTML = '';
    if (emptyNode) container.appendChild(emptyNode);

    if (!nodes.length) {
      if (emptyNode) {
        emptyNode.hidden = false;
        emptyNode.textContent = 'No nodes match the current filters. Re-enable a category or clear the focus.';
      }
      this.updateStats(0, 0, truncated);
      return;
    }
    if (emptyNode) emptyNode.hidden = true;

    this.cy = cytoscape({
      container: container,
      elements: { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) },
      style: this.stylesheet(),
      layout: this.layoutConfig(this.opts.layout),
      wheelSensitivity: 0.3,
      maxZoom: 4, minZoom: 0.08
    });

    this.cy.on('tap', 'node', ev => {
      const d = ev.target.data();
      if (d.isGroup) return;
      this.focusId = d.id;
      this._enableFocusButtons(true);
      this.highlight(d.id);
      if (this.opts.onNodeSelect) this.opts.onNodeSelect(d, this);
      else showDetail(d.label || d.id, this.defaultNodeDetail(d));
    });
    this.cy.on('tap', 'edge', ev => {
      const d = ev.target.data();
      showDetail(d.label || 'Relation', this.defaultEdgeDetail(d));
    });
    this.cy.on('tap', ev => { if (ev.target === this.cy) { this.clearHighlight(); } });
    // Labels are suppressed below a zoom threshold: at fit-zoom a dense graph is
    // unreadable with every label painted, and the clutter hides the structure.
    this.cy.on('zoom', () => this.applyLabelVisibility());
    this.applyLabelVisibility();

    this.updateStats(nodes.filter(n => !n.data.isGroup).length, edges.length, truncated);
  }

  applyLabelVisibility() {
    if (!this.cy) return;
    const visible = this.cy.zoom() >= 0.55 || this.cy.nodes().length <= 40;
    if (visible === this._labelsVisible) return;
    this._labelsVisible = visible;
    this.cy.batch(() => {
      this.cy.nodes().style('text-opacity', visible ? 1 : 0);
    });
    const hint = document.getElementById(this.mountId);
    const stats = hint && hint.parentElement && hint.parentElement.querySelector('.g-zoom-hint');
    if (stats) stats.textContent = visible ? '' : 'Labels hidden at this zoom — zoom in to read them.';
  }

  highlight(id) {
    if (!this.cy) return;
    const node = this.cy.getElementById(id);
    if (!node || node.empty()) return;
    const keep = node.closedNeighborhood();
    this.cy.elements().addClass('faded');
    keep.removeClass('faded');
    node.select();
  }
  clearHighlight() { if (this.cy) this.cy.elements().removeClass('faded'); }

  defaultNodeDetail(d) {
    const rel = [];
    (d.outgoing || []).forEach(r => rel.push(`<li><code>${esc(r.label)}</code> → ${esc(r.target)}</li>`));
    (d.incoming || []).forEach(r => rel.push(`<li>${esc(r.source)} → <code>${esc(r.label)}</code></li>`));
    return [
      fields([
        ['Compact id', `<code>${esc(d.id)}</code>`],
        ['URI', d.uri ? `<code class="small">${esc(d.uri)}</code>` : null],
        ['Label (en)', esc(d.label)],
        ['Label (ko)', d.ko ? esc(d.ko) : `<span class="missing">no Korean label</span>`],
        ['Type', esc(d.nodeType || 'class')],
        ['Category', esc(titleCase(d.cat || 'other'))],
        ['Source module', d.module ? `<code class="small">${esc(d.module)}</code>` : null],
        ['Superclasses', (d.superclasses || []).length ? (d.superclasses || []).map(s => `<code>${esc(s)}</code>`).join(', ') : null]
      ]),
      d.bridge ? `<div class="callout callout-info">Bridge node: declared outside this module, shown so its subclasses are not stranded.</div>` : '',
      section('Definition', d.definition ? `<p>${esc(d.definition)}</p>` : `<p class="missing">No skos:definition recorded.</p>`),
      section('Scope note', d.scopeNote ? `<p>${esc(d.scopeNote)}</p>` : ''),
      section('Comment', d.comment ? `<p>${esc(d.comment)}</p>` : ''),
      section('Declared relations', rel.length ? `<ul class="dlist">${rel.join('')}</ul>` : ''),
      badge('badge-ontology', 'Ontology engineering — not source-derived')
    ].join('');
  }

  defaultEdgeDetail(d) {
    return [
      fields([
        ['Relation', `<code>${esc(d.label)}</code>`],
        ['Kind', esc(titleCase(d.kind))],
        ['From', `<code>${esc(d.source)}</code>`],
        ['To', `<code>${esc(d.target)}</code>`],
        ['Property', d.prop ? `<code>${esc(d.prop)}</code>` : null],
        ['URI', d.propUri ? `<code class="small">${esc(d.propUri)}</code>` : null],
        ['Characteristics', (d.characteristics || []).length ? esc((d.characteristics || []).join(', ')) : null]
      ]),
      section('Definition', d.definition ? `<p>${esc(d.definition)}</p>` : ''),
      section('Scope note', d.scopeNote ? `<p>${esc(d.scopeNote)}</p>` : '')
    ].join('');
  }

  updateStats(nodeCount, edgeCount, truncated) {
    const el = document.querySelector(`#${CSS.escape(this.mountId)}`).parentElement.querySelector('.g-stats');
    if (!el) return;
    const meta = this.dataset.meta;
    el.innerHTML = `Showing <strong>${num(nodeCount)}</strong> of ${num(meta.node_count)} nodes and
      <strong>${num(edgeCount)}</strong> of ${num(meta.edge_count)} relations.
      ${meta.isolated_node_count ? `${num(meta.isolated_node_count)} node(s) in this dataset have no relation in the source RDF${this.hideIsolated ? ' (currently hidden)' : ''}.` : ''}
      ${truncated ? `${num(truncated)} hidden by the node limit.` : ''}`;
  }

  wire(root) {
    const q = sel => root.querySelector(sel);
    root.querySelectorAll('[data-cat]').forEach(btn => btn.addEventListener('click', () => {
      const cat = btn.getAttribute('data-cat');
      const on = btn.getAttribute('aria-pressed') === 'true';
      btn.setAttribute('aria-pressed', String(!on));
      if (on) this.activeCats.delete(cat); else this.activeCats.add(cat);
      this.mount();
    }));
    root.querySelectorAll('[data-kind]').forEach(btn => btn.addEventListener('click', () => {
      const kind = btn.getAttribute('data-kind');
      const on = btn.getAttribute('aria-pressed') === 'true';
      btn.setAttribute('aria-pressed', String(!on));
      if (on) this.activeKinds.delete(kind); else this.activeKinds.add(kind);
      this.mount();
    }));
    root.querySelectorAll('[data-ntype]').forEach(btn => btn.addEventListener('click', () => {
      const t = btn.getAttribute('data-ntype');
      const on = btn.getAttribute('aria-pressed') === 'true';
      btn.setAttribute('aria-pressed', String(!on));
      if (on) this.activeNodeTypes.delete(t); else this.activeNodeTypes.add(t);
      this.mount();
    }));
    const hide = q('.g-hide-isolated');
    if (hide) hide.addEventListener('change', () => { this.hideIsolated = hide.checked; this.mount(); });
    const grp = q('.g-group-module');
    if (grp) grp.addEventListener('change', () => { this.groupByModule = grp.checked; this.mount(); });
    const layout = q('.g-layout');
    if (layout) {
      layout.value = this.opts.layout;
      layout.addEventListener('change', () => { this.opts.layout = layout.value; this.mount(); });
    }
    const limit = q('.g-limit');
    if (limit) limit.addEventListener('change', () => {
      this.nodeLimit = Math.max(20, parseInt(limit.value, 10) || 400);
      this.overrideLimit = false; this.mount();
    });
    const depth = q('.g-depth');
    if (depth) depth.addEventListener('change', () => { this.depth = parseInt(depth.value, 10) || 1; this.mount(); });
    const expand = q('.g-expand');
    if (expand) expand.addEventListener('click', () => {
      this.depth = Math.min(3, this.depth + 1);
      if (depth) depth.value = String(this.depth);
      this.mount();
    });
    const clear = q('.g-clear-focus');
    if (clear) clear.addEventListener('click', () => {
      this.focusId = null; this.depth = 1;
      if (depth) depth.value = '1';
      this._enableFocusButtons(false); this.mount();
    });
    const fit = q('.g-fit');
    if (fit) fit.addEventListener('click', () => { if (this.cy) this.cy.fit(undefined, 30); });
    const reset = q('.g-reset');
    if (reset) reset.addEventListener('click', () => {
      this.focusId = null; this.overrideLimit = false; this.clearHighlight();
      this._enableFocusButtons(false); this.mount();
    });
    const full = q('.g-full');
    if (full) full.addEventListener('click', () => {
      const canvas = document.getElementById(this.mountId);
      canvas.classList.toggle('fullscreen');
      full.textContent = canvas.classList.contains('fullscreen') ? 'Exit full screen' : 'Full screen';
      if (this.cy) { this.cy.resize(); this.cy.fit(undefined, 30); }
    });
    const png = q('.g-png');
    if (png) png.addEventListener('click', () => {
      if (!this.cy) return;
      const uri = this.cy.png({ full: true, scale: 2, bg: '#ffffff' });
      const a = document.createElement('a');
      a.href = uri; a.download = `${this.dataset.meta.id}.png`;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      toast('PNG exported');
    });
    const json = q('.g-json');
    if (json) json.addEventListener('click', () => {
      const { nodes, edges } = this.visibleElements();
      download(`${this.dataset.meta.id}-view.json`, JSON.stringify({
        meta: Object.assign({}, this.dataset.meta, {
          exported_view: true,
          node_count: nodes.length, edge_count: edges.length
        }),
        nodes, edges
      }, null, 2));
      toast('Visible graph exported as JSON');
    });
  }

  _enableFocusButtons(on) {
    const root = document.getElementById(this.mountId);
    if (!root || !root.parentElement) return;
    const wrap = root.parentElement;
    ['.g-expand', '.g-clear-focus'].forEach(sel => {
      const b = wrap.querySelector(sel);
      if (b) b.disabled = !on;
    });
  }

  /** Select a node by id from outside (search, cross-links). */
  selectById(id) {
    if (!this.cy) return false;
    const node = this.cy.getElementById(id);
    if (!node || node.empty()) {
      // Not in the current slice — focus it so the slice is rebuilt around it.
      this.focusId = id; this.overrideLimit = true; this.mount();
      const retry = this.cy && this.cy.getElementById(id);
      if (!retry || retry.empty()) return false;
      this.highlight(id);
      showDetail(retry.data('label') || id, this.defaultNodeDetail(retry.data()));
      return true;
    }
    this.cy.center(node);
    this.highlight(id);
    showDetail(node.data('label') || id, this.defaultNodeDetail(node.data()));
    this._enableFocusButtons(true);
    return true;
  }
}

function mountGraph(viewId, mountId, dataset, options) {
  const gv = new GraphView(mountId, dataset, options);
  STATE.graphs[viewId] = gv;
  return gv;
}

/* --------------------------------------------------------------------------
   6. Views
   -------------------------------------------------------------------------- */

const VIEWS = {};

/* ---- A. Overview ---- */
VIEWS.overview = function () {
  const d = STATE.data.overview;
  const groups = {};
  d.cards.forEach(c => { (groups[c.group] = groups[c.group] || []).push(c); });

  const cardsHtml = Object.keys(groups).map(g => `
    <div class="card-group-head">${esc(g)}</div>
    <div class="card-grid">
      ${groups[g].map(c => `
        <div class="card ${c.emphasis === 'warn' ? 'warn' : ''}">
          <div class="card-val">${typeof c.value === 'number' ? num(c.value) : esc(c.value)}</div>
          <div class="card-lab">${esc(c.label)}</div>
          ${c.note ? `<div class="card-note">${esc(c.note)}</div>` : ''}
        </div>`).join('')}
    </div>`).join('');

  const v = d.validation;
  const validationHtml = v ? `
    <div class="panel">
      <h3>Validation status</h3>
      <div class="btn-row" style="margin-bottom:.5rem">
        ${badge(v.shacl_conforms ? 'badge-verified' : 'badge-rejected', 'SHACL: ' + (v.shacl_conforms ? 'conforms' : 'violations'))}
        ${badge(v.custom_checks_failed === 0 ? 'badge-verified' : 'badge-rejected',
                `Custom checks: ${v.custom_checks_run - v.custom_checks_failed}/${v.custom_checks_run} pass`)}
        <span id="test-status-slot"></span>
      </div>
      <div class="tbl-wrap" style="max-height:280px">
        <table class="tbl"><thead><tr class="nosort">
          <th class="nosort">Check</th><th class="nosort">Result</th><th class="nosort">Items</th><th class="nosort">Violations</th>
        </tr></thead><tbody>
          ${v.checks.map(c => `<tr>
            <td><code>${esc(c.check)}</code>${c.notes && c.notes.length ? `<div class="small muted">${c.notes.map(esc).join('<br>')}</div>` : ''}</td>
            <td>${c.passed ? badge('badge-verified', 'pass') : badge('badge-rejected', 'fail')}</td>
            <td class="right">${num(c.items_checked)}</td>
            <td class="right">${num(c.violations)}</td></tr>`).join('')}
        </tbody></table>
      </div>
    </div>` : `<div class="callout callout-warn"><strong>Validation report not found.</strong>
       Run <code>python3 scripts/validate_ontology.py</code> to populate it.</div>`;

  const verdictHtml = Object.keys(d.substitution_verdicts).sort().map(k =>
    `<tr><td><span class="verdict v-${esc(k)}">${esc(k)}</span></td><td class="right">${num(d.substitution_verdicts[k])}</td></tr>`).join('');

  const sourcesHtml = d.sources.map(s => `
    <tr>
      <td><strong>${esc(s.title)}</strong><div class="small muted">${esc(s.authors.join(', '))}</div></td>
      <td>${esc(s.edition)}</td>
      <td class="right">${num(s.page_count)}</td>
      <td class="right">${num(s.claims)}</td>
      <td class="right">${num(s.spans)}</td>
      <td>${integrityBadge(s.math_text_reliability === 'corrupted' ? 'glyph-mismapped'
            : s.math_text_reliability === 'partial' ? 'partial-glyph-loss' : 'reliable')}</td>
      <td><code class="small">${esc(s.sha256.slice(0, 16))}…</code></td>
    </tr>`).join('');

  return `
    <div class="view-head">
      <h2>Project overview</h2>
      <p>mdkg v0.1 — a general mechanical-design ontology with an evidence-grounded knowledge
         graph built from two textbooks. Every count below is read from the repository's own
         generated reports.</p>
    </div>

    <div class="callout callout-warn">
      <strong>Pilot knowledge graph</strong>
      ${esc(d.warning)}
    </div>

    ${cardsHtml}

    <div class="panel-grid">
      ${validationHtml}
      <div class="panel">
        <h3>Substitution verdicts</h3>
        <div class="tbl-wrap"><table class="tbl"><thead><tr>
          <th class="nosort">Verdict</th><th class="nosort right">Count</th></tr></thead>
          <tbody>${verdictHtml}</tbody></table></div>
        ${d.no_directly_substitutable ? `<div class="callout callout-info" style="margin-top:.6rem">
          <strong>No DirectlySubstitutable assessment exists.</strong>
          Every pair examined in the pilot needs at least a change of shaft or hub feature.
          That is the honest result, not a gap.</div>` : ''}
        <h3 style="margin-top:.9rem">Rules by category</h3>
        <div class="tbl-wrap"><table class="tbl"><thead><tr>
          <th class="nosort">Category</th><th class="nosort right">Count</th></tr></thead>
          <tbody>${Object.keys(d.rule_counts).sort().map(k =>
            `<tr><td>${esc(titleCase(k.replace('_rules', '')))}</td><td class="right">${num(d.rule_counts[k])}</td></tr>`).join('')}
          </tbody></table></div>
      </div>
    </div>

    <div class="panel">
      <h3>Source documents</h3>
      <div class="tbl-wrap"><table class="tbl"><thead><tr>
        <th class="nosort">Book</th><th class="nosort">Ed.</th><th class="nosort right">PDF pages</th>
        <th class="nosort right">Claims</th><th class="nosort right">Spans</th>
        <th class="nosort">Math text layer</th><th class="nosort">SHA-256</th>
      </tr></thead><tbody>${sourcesHtml}</tbody></table></div>
      <p class="small muted" style="margin-top:.5rem">
        Text-layer integrity is measured, not assumed. The Shigley PDF mis-maps mathematics
        glyphs onto ASCII, so affected spans are flagged and never quoted.</p>
    </div>

    <div class="panel">
      <h3>Review states across the graph</h3>
      <div class="btn-row">
        ${Object.keys(d.review_states).map(k => `${reviewBadge(k)} <span class="small muted">${num(d.review_states[k])}</span>`).join(' &nbsp; ')}
      </div>
      <p class="small muted" style="margin-top:.5rem">An automated pipeline may assign at most
        <code>NeedsReview</code>. <code>HumanVerified</code> requires a named reviewer and a date.</p>
    </div>`;
};

VIEWS.overview.after = function () {
  // Test status is a diagnostic artefact; absent unless --validate was run.
  fetch('data/status.json').then(r => r.ok ? r.json() : null).then(status => {
    const slot = document.getElementById('test-status-slot');
    if (!slot) return;
    if (!status || !status.unit_tests) {
      slot.innerHTML = badge('badge-neutral', 'Unit tests: not evaluated in this build');
      return;
    }
    const t = status.unit_tests;
    slot.innerHTML = badge(t.failures === 0 && t.errors === 0 ? 'badge-verified' : 'badge-rejected',
      `Unit tests: ${t.run - t.failures - t.errors}/${t.run} pass`);
  }).catch(() => {});
};

/* ---- B. Core ontology ---- */
VIEWS.ontology = function () {
  const ds = STATE.data.ontology_graph;
  const gv = mountGraph('ontology', 'cy-ontology', ds, { layout: 'cose', nodeLimit: 300 });
  return `
    <div class="view-head">
      <h2>${esc(ds.meta.title)}</h2>
      <p>${esc(ds.meta.description)}</p>
    </div>
    <div class="callout callout-info">
      ${badge('badge-ontology', 'Ontology engineering')}
      Everything in this view is analyst-authored ontology structure. It is not derived from
      either textbook. Source-derived statements live in the Claims view.
    </div>
    <div class="graph-shell">${gv.toolbarHtml()}</div>
    <details class="filters" style="margin-top:1rem">
      <summary>Property catalogue (${num(ds.properties.length)} object and datatype properties)</summary>
      <div style="padding:0 .8rem .8rem">
        <div class="tbl-wrap" style="max-height:420px">
          <table class="tbl"><thead><tr>
            <th>Property</th><th>Kind</th><th>Domain</th><th>Range</th><th>Characteristics</th>
          </tr></thead><tbody>
            ${ds.properties.map(p => `<tr data-prop="${esc(p.curie)}">
              <td><code>${esc(p.curie)}</code><div class="small muted">${esc(p.label)}</div></td>
              <td>${esc(p.kind)}</td>
              <td class="small">${p.domains.length ? p.domains.map(esc).join(', ') : '<span class="missing">none declared</span>'}</td>
              <td class="small">${p.ranges.length ? p.ranges.map(esc).join(', ') : '<span class="missing">none declared</span>'}</td>
              <td class="small">${p.characteristics.length ? esc(p.characteristics.join(', ')) : '—'}</td>
            </tr>`).join('')}
          </tbody></table>
        </div>
      </div>
    </details>`;
};
VIEWS.ontology.after = function (target) {
  const gv = STATE.graphs.ontology;
  gv.mount(); gv.wire(document.getElementById('view-root'));
  document.querySelectorAll('tr[data-prop]').forEach(row => {
    row.addEventListener('click', () => {
      const p = STATE.data.ontology_graph.properties.find(x => x.curie === row.getAttribute('data-prop'));
      if (!p) return;
      showDetail(p.label, [
        fields([
          ['Compact id', `<code>${esc(p.curie)}</code>`],
          ['URI', `<code class="small">${esc(p.uri)}</code>`],
          ['Kind', esc(p.kind + ' property')],
          ['Label (ko)', p.ko ? esc(p.ko) : `<span class="missing">no Korean label</span>`],
          ['Module', p.module ? `<code class="small">${esc(p.module)}</code>` : null],
          ['Domain', p.domains.length ? p.domains.map(x => `<code>${esc(x)}</code>`).join(', ') : null],
          ['Range', p.ranges.length ? p.ranges.map(x => `<code>${esc(x)}</code>`).join(', ') : null],
          ['Characteristics', p.characteristics.length ? esc(p.characteristics.join(', ')) : null],
          ['Inverse of', p.inverse_of.length ? p.inverse_of.map(x => `<code>${esc(x)}</code>`).join(', ') : null]
        ]),
        section('Definition', p.definition ? `<p>${esc(p.definition)}</p>` : `<p class="missing">No definition recorded.</p>`),
        section('Scope note', p.scope_note ? `<p>${esc(p.scope_note)}</p>` : ''),
        badge('badge-ontology', 'Ontology engineering')
      ].join(''));
    });
  });
  if (target) gv.selectById(target);
};

/* ---- C. Mechanical design ---- */
VIEWS.mechanical = function () {
  const ds = STATE.data.function_behavior_graph;
  const gv = mountGraph('mechanical', 'cy-mech', ds, { layout: 'cose', nodeLimit: 260 });
  return `
    <div class="view-head">
      <h2>${esc(ds.meta.title)}</h2>
      <p>${esc(ds.meta.description)}</p>
    </div>
    <div class="callout callout-info">
      <strong>Reading the Function · Behavior · Structure chain</strong>
      A <em>function</em> (◆) is realised by a <em>behavior</em> (⬡), which is enabled by a
      <em>design alternative</em> (⬟). Two alternatives sharing a behavior share a failure family;
      two sharing only a function share almost nothing operationally.
    </div>
    <div class="graph-shell">${gv.toolbarHtml()}</div>`;
};
VIEWS.mechanical.after = function (target) {
  const gv = STATE.graphs.mechanical;
  gv.mount(); gv.wire(document.getElementById('view-root'));
  if (target) gv.selectById(target);
};

/* ---- D. Machine elements ---- */
VIEWS.elements = function () {
  const ds = STATE.data.machine_elements_graph;
  const families = ds.families;
  const gv = mountGraph('elements', 'cy-elem', ds, { layout: 'cose', nodeLimit: 300 });
  gv.expandedFamilies = new Set(ds.default_expanded);
  gv.opts.onNodeSelect = (d) => showDetail(d.label || d.id, elementDetail(d));

  const famChips = families.map(f => {
    const node = ds.nodes.find(n => n.data.id === f);
    const on = ds.default_expanded.indexOf(f) >= 0;
    return `<button class="chip" role="switch" aria-pressed="${on}" data-family="${esc(f)}">
      ${esc(node ? node.data.label : f)}</button>`;
  }).join('');

  return `
    <div class="view-head">
      <h2>${esc(ds.meta.title)}</h2>
      <p>${esc(ds.meta.description)}</p>
    </div>
    <div class="callout callout-info">
      <strong>Element type versus design alternative</strong>
      An <em>element type</em> (▬ / ▭, single border) is an OWL class — a kind of physical part.
      A <em>design alternative</em> (⬟, double border) is an individual — a named solution concept.
      Substitution operates on alternatives, never on element classes.
    </div>
    <details class="filters" open>
      <summary>Expand families</summary>
      <div class="filters-body">
        <div class="fgroup" style="min-width:100%">
          <label class="flabel">Shaft/hub connections and bearings are expanded by default; other families start collapsed</label>
          <div class="chips">${famChips}</div>
          <div class="btn-row" style="margin-top:.4rem">
            <button class="btn" id="fam-all">Expand all</button>
            <button class="btn" id="fam-none">Collapse all</button>
          </div>
        </div>
      </div>
    </details>
    <div class="graph-shell">${gv.toolbarHtml()}</div>`;
};

function elementDetail(d) {
  const ds = STATE.data.machine_elements_graph;
  const nameOf = id => {
    const n = ds.nodes.find(x => x.data.id === id);
    return n ? n.data.label : id;
  };
  const claims = (d.claimIds || []).map(c =>
    `<li>${linkTo('claims', c, c)}</li>`).join('');
  const spans = (d.spanIds || []).map(s =>
    `<li>${linkTo('evidence', s, s)}</li>`).join('');
  return [
    fields([
      ['Compact id', `<code>${esc(d.id)}</code>`],
      ['URI', d.uri ? `<code class="small">${esc(d.uri)}</code>` : null],
      ['Representation', d.nodeType === 'individual'
        ? 'Design alternative (OWL individual)' : 'Element type (OWL class)'],
      ['Label (ko)', d.ko ? esc(d.ko) : `<span class="missing">no Korean label</span>`],
      ['Parent family', d.family ? `<code>${esc(nameOf(d.family))}</code>` : null],
      ['Superclasses', (d.superclasses || []).length ? (d.superclasses || []).map(s => `<code>${esc(s)}</code>`).join(', ') : null],
      ['Supporting claims', num((d.claimIds || []).length)],
      ['Evidence spans', num((d.spanIds || []).length)]
    ]),
    section('Definition', d.definition ? `<p>${esc(d.definition)}</p>` : `<p class="missing">No skos:definition recorded.</p>`),
    section('Scope note', d.scopeNote ? `<p>${esc(d.scopeNote)}</p>` : ''),
    section('Functions', (d.functions || []).length
      ? list(d.functions, f => `<li>${linkTo('functions', f, nameOf(f) || f)}</li>`)
      : `<p class="missing">No function asserted for this node.</p>`),
    section('Behaviors', (d.behaviors || []).length ? list(d.behaviors, b => `<li>${esc(nameOf(b))}</li>`) : ''),
    section('Known failure modes', (d.failureModes || []).length
      ? list(d.failureModes, f => `<li>${esc(nameOf(f))}</li>`)
      : `<p class="missing">No failure mode recorded for this element in v0.1.</p>`),
    section('Required verification', (d.verification || []).length
      ? list(d.verification, v => `<li>${esc(nameOf(v))}</li>`)
      : `<p class="missing">No verification method recorded for this element in v0.1.</p>`),
    section('Related design alternatives', (d.elementTypes || []).length
      ? list(d.elementTypes, t => `<li>${esc(nameOf(t))}</li>`) : ''),
    section('Supporting claims', claims ? `<ul class="dlist">${claims}</ul>` : `<p class="missing">No claim references this node yet.</p>`),
    section('Evidence spans', spans ? `<ul class="dlist">${spans}</ul>` : ''),
    badge('badge-ontology', 'Taxonomy is ontology engineering')
  ].join('');
}

VIEWS.elements.after = function (target) {
  const gv = STATE.graphs.elements;
  const ds = STATE.data.machine_elements_graph;

  const applyFamilies = () => {
    // Collapsed families keep the family node but drop its descendants.
    const expanded = gv.expandedFamilies;
    const allowed = new Set();
    ds.nodes.forEach(n => {
      const d = n.data;
      if (d.isRoot || ds.families.indexOf(d.id) >= 0) { allowed.add(d.id); return; }
      if (!d.family || expanded.has(d.family)) allowed.add(d.id);
    });
    gv.familyAllow = allowed;
  };

  const baseVisible = gv.visibleElements.bind(gv);
  gv.visibleElements = function () {
    const result = baseVisible();
    if (!gv.familyAllow) return result;
    const nodes = result.nodes.filter(n => n.data.isGroup || gv.familyAllow.has(n.data.id));
    const ids = new Set(nodes.map(n => n.data.id));
    const edges = result.edges.filter(e => ids.has(e.data.source) && ids.has(e.data.target));
    return { nodes, edges, truncated: result.truncated };
  };

  applyFamilies();
  gv.mount(); gv.wire(document.getElementById('view-root'));

  document.querySelectorAll('[data-family]').forEach(btn => {
    btn.addEventListener('click', () => {
      const fam = btn.getAttribute('data-family');
      const on = btn.getAttribute('aria-pressed') === 'true';
      btn.setAttribute('aria-pressed', String(!on));
      if (on) gv.expandedFamilies.delete(fam); else gv.expandedFamilies.add(fam);
      applyFamilies(); gv.mount();
    });
  });
  const all = document.getElementById('fam-all');
  if (all) all.addEventListener('click', () => {
    ds.families.forEach(f => gv.expandedFamilies.add(f));
    document.querySelectorAll('[data-family]').forEach(b => b.setAttribute('aria-pressed', 'true'));
    applyFamilies(); gv.mount();
  });
  const none = document.getElementById('fam-none');
  if (none) none.addEventListener('click', () => {
    gv.expandedFamilies.clear();
    document.querySelectorAll('[data-family]').forEach(b => b.setAttribute('aria-pressed', 'false'));
    applyFamilies(); gv.mount();
  });
  if (target) {
    const node = ds.nodes.find(n => n.data.id === target);
    if (node && node.data.family) {
      gv.expandedFamilies.add(node.data.family);
      const chip = document.querySelector(`[data-family="${CSS.escape(node.data.family)}"]`);
      if (chip) chip.setAttribute('aria-pressed', 'true');
      applyFamilies(); gv.mount();
    }
    gv.selectById(target);
  }
};

/* ---- E. Function → alternative ---- */
VIEWS.functions = function () {
  const ds = STATE.data.function_behavior_graph;
  const funcs = ds.functions;
  const items = funcs.map(f => `
    <button class="search-item" data-func="${esc(f.id)}">
      <strong>${esc(f.label)}</strong>
      <span class="si-sub">${esc(f.id)} · ${f.alternative_count} alternative(s)</span>
    </button>`).join('');
  return `
    <div class="view-head">
      <h2>Function → alternative explorer</h2>
      <p>Start from the job to be done, not from the part name. Select a function to see every
         alternative the ontology knows can perform it, with the behavior that delivers it and the
         evidence behind each claim.</p>
    </div>
    <div class="callout callout-warn">
      <strong>Shared function does not imply direct substitutability.</strong>
      Two alternatives listed under the same function may differ completely in interface, capacity,
      failure mode and verification. Use the Substitution view for a directional, context-bound verdict.
    </div>
    <div class="panel-grid" style="grid-template-columns: 320px 1fr">
      <div class="panel" style="max-height:660px;overflow:auto">
        <h3>Functions (${num(funcs.length)})</h3>
        ${items}
      </div>
      <div class="panel" id="func-detail"><p class="muted">Select a function to begin.</p></div>
    </div>`;
};

VIEWS.functions.after = function (target) {
  const ds = STATE.data.function_behavior_graph;
  const render = (fid) => {
    const f = ds.functions.find(x => x.id === fid);
    const box = document.getElementById('func-detail');
    if (!f) { box.innerHTML = '<p class="muted">Function not found.</p>'; return; }
    document.querySelectorAll('[data-func]').forEach(b =>
      b.classList.toggle('active', b.getAttribute('data-func') === fid));

    const alts = f.alternatives.filter(a =>
      STATE.sourceFilter === 'all' || a.source_books.indexOf(STATE.sourceFilter) >= 0 ||
      a.source_books.length === 0);

    const cards = alts.length ? alts.map(a => `
      <div class="panel" style="margin-bottom:.7rem">
        <h4>${esc(a.label)} <code class="small muted">${esc(a.id)}</code></h4>
        ${fields([
          ['Enabled behavior', a.behaviors.length ? a.behaviors.map(b => `<code>${esc(b)}</code>`).join(', ') : null],
          ['Element type', a.element_types.length ? a.element_types.map(b => `<code>${esc(b)}</code>`).join(', ') : null],
          ['Source coverage', a.source_books.length
            ? a.source_books.map(b => badge('badge-neutral', b === 'mott6' ? 'Mott 6e' : 'Shigley 10e')).join('')
            : `<span class="missing">No source claim references this alternative yet</span>`],
          ['Supporting claims', a.claim_count ? `${num(a.claim_count)} — ${a.claim_ids.map(c => linkTo('claims', c, c)).join(', ')}` : null],
          ['Evidence spans', a.span_count ? num(a.span_count) : null]
        ])}
        ${a.failure_modes.length ? section('Associated failure modes (from substitution assessments)',
          list(a.failure_modes, x => `<li><code>${esc(x)}</code></li>`)) :
          `<div class="dsec"><h4>Associated failure modes</h4><p class="missing">${esc(NOT_STATED)} for this alternative in v0.1.</p></div>`}
        ${a.verification.length ? section('Required verification',
          list(a.verification, x => `<li><code>${esc(x)}</code></li>`)) :
          `<div class="dsec"><h4>Required verification</h4><p class="missing">No verification recorded in v0.1.</p></div>`}
        ${a.limitations.length ? section('Known limitations', list(a.limitations, l =>
          `<li>${esc(l.statement)} ${provenanceBadge(l.provenance)}
            <span class="small muted">(${esc(l.assessment)})</span></li>`)) : ''}
      </div>`).join('') : `<p class="missing">No design alternative in v0.1 performs this function.</p>`;

    box.innerHTML = `
      <h3>${esc(f.label)}</h3>
      ${fields([
        ['Compact id', `<code>${esc(f.id)}</code>`],
        ['Preferred label', f.pref_label ? esc(f.pref_label) : null],
        ['Label (ko)', f.ko ? esc(f.ko) : `<span class="missing">no Korean label</span>`],
        ['Broader function', f.broader && f.broader.length ? f.broader.map(b => `<code>${esc(b)}</code>`).join(', ') : null],
        ['Alternatives', num(f.alternative_count)]
      ])}
      ${f.definition ? section('Definition', `<p>${esc(f.definition)}</p>`) : ''}
      ${f.scope_note ? section('Scope note', `<p>${esc(f.scope_note)}</p>`) : ''}
      <div class="callout callout-warn small">Shared function does not imply direct substitutability.</div>
      <h3 style="margin-top:.8rem">Alternatives that can perform it</h3>
      ${cards}`;
    wireCrossLinks(box);
  };

  document.querySelectorAll('[data-func]').forEach(btn =>
    btn.addEventListener('click', () => render(btn.getAttribute('data-func'))));

  const initial = target && ds.functions.some(f => f.id === target)
    ? target
    : (ds.functions.find(f => f.id === 'mech:TransmitTorqueShaftToHub') || ds.functions[0] || {}).id;
  if (initial) render(initial);
};

/* ---- F. Substitution ---- */
function verdictChip(v) { return `<span class="verdict v-${esc(v)}">${esc(v)}</span>`; }

function decoratedList(items, emptyText) {
  if (!items || !items.length) return `<p class="missing">${esc(emptyText || NOT_STATED)}</p>`;
  return `<ul class="dlist">${items.map(i => {
    const cites = (i.citations || []).filter(Boolean);
    return `<li>
      ${esc(i.text || i.statement || '')}
      ${i.criterion_label ? `<div class="small muted">Criterion: ${esc(i.criterion_label)}${i.level ? ' — ' + esc(i.level) : ''}</div>` : ''}
      ${i.failure_label ? `<div class="small muted">Failure mode: ${esc(i.failure_label)}</div>` : ''}
      ${i.method_label ? `<div class="small muted">Method: ${esc(i.method_label)}</div>` : ''}
      ${i.condition_label ? `<div class="small muted">Condition: ${esc(i.condition_label)}</div>` : ''}
      ${i.effort ? `<div class="small muted">Effort: ${esc(i.effort)}</div>` : ''}
      <div>${provenanceBadge(i.provenance)}
        ${i.state ? badge('badge-insufficient', i.state) : ''}
        ${i.test_recommended !== undefined ? badge('badge-authority',
            `Test recommended · procedure ${i.test_procedure_specified ? 'specified' : 'NOT specified'} · criterion ${i.acceptance_criterion_specified ? 'specified' : 'NOT specified'}`) : ''}
        ${authorityBadges(i.external_authority)}
      </div>
      ${cites.length ? `<div class="small muted">${cites.map(c => '▪ ' + esc(c)).join('<br>')}</div>` : ''}
      ${(i.span_ids || []).length ? `<div class="small">${i.span_ids.map(s => linkTo('evidence', s, s)).join(' · ')}</div>` : ''}
    </li>`;
  }).join('')}</ul>`;
}

function assessmentCardHtml(sa) {
  return `
    <div class="compare-col">
      <h3>${esc(sa.id)}</h3>
      ${verdictChip(sa.verdict)}
      <div class="direction-arrow">
        <span class="from">${esc(sa.baseline.label)}</span>
        &nbsp;⟶&nbsp;
        <span class="to">${esc(sa.candidate.label)}</span>
        <div class="small muted">candidate replaces baseline (direction is never mirrored)</div>
      </div>
      ${fields([
        ['Preserved function', esc(sa.function_preserved.label)],
        ['Operating context', esc(sa.context.label)],
        ['Interface', esc(sa.interface_compatibility)],
        ['Confidence', sa.confidence === null || sa.confidence === undefined ? null : esc(sa.confidence)],
        ['Review', reviewBadge(sa.review_status)]
      ])}
      ${section('Context conditions', sa.context.conditions.length
        ? list(sa.context.conditions, c => `<li><code>${esc(c.curie)}</code> — ${esc(c.label)}</li>`) : '')}
      ${section('Satisfied requirements', sa.satisfied_requirements.length
        ? list(sa.satisfied_requirements, r => `<li>${esc(r.label)}</li>`)
        : `<p class="missing">None recorded.</p>`)}
      ${section('Violated requirements', sa.violated_requirements.length
        ? list(sa.violated_requirements, r => `<li>${esc(r.label)}</li>`)
        : `<p class="missing">None recorded.</p>`)}
      ${section('Conditions', decoratedList(sa.conditions, 'No condition recorded.'))}
      ${section('Required modifications', decoratedList(sa.modifications, 'No modification required.'))}
      ${section('Advantages', decoratedList(sa.advantages, 'None recorded.'))}
      ${section('Disadvantages', decoratedList(sa.disadvantages, 'None recorded.'))}
      ${section('Trade-offs', decoratedList(sa.trade_offs, 'None recorded.'))}
      ${section('Introduced failure modes', decoratedList(sa.introduced_failure_modes, 'None recorded.'))}
      ${section('Mitigated failure modes', decoratedList(sa.mitigated_failure_modes, 'None recorded.'))}
      ${section('Required verification', decoratedList(sa.required_verification, 'None recorded.'))}
      ${section('Unresolved evidence gaps', sa.unresolved.length
        ? decoratedList(sa.unresolved) : `<p class="muted">None recorded.</p>`)}
      ${sa.analyst_note ? `<div class="callout callout-warn"><strong>Analyst note</strong>${esc(sa.analyst_note)} ${provenanceBadge('EngineeringInference')}</div>` : ''}
      ${section('Supporting claims', sa.supporting_claims.length ? list(sa.supporting_claims, c =>
        `<li>${linkTo('claims', c.claim_id, c.claim_id)} <span class="small muted">(${esc(c.doc_id)})</span>
           <div class="small">${esc(c.statement.slice(0, 190))}${c.statement.length > 190 ? '…' : ''}</div>
           ${(c.citations || []).filter(Boolean).map(x => `<div class="small muted">▪ ${esc(x)}</div>`).join('')}
         </li>`) : `<p class="missing">No supporting claim recorded.</p>`)}
    </div>`;
}

VIEWS.substitutions = function () {
  const ds = STATE.data.substitutions_graph;
  const gv = mountGraph('substitutions', 'cy-sub', ds, { layout: 'breadthfirst', nodeLimit: 120 });
  const order = ds.verdict_order;
  const counts = ds.verdict_counts;
  const verdictLegend = order.map(v =>
    `<span class="legend-item">${verdictChip(v)} <span class="small muted">${num(counts[v] || 0)}</span></span>`).join('');
  const options = ds.assessments.map(a =>
    `<option value="${esc(a.id)}">${esc(a.id)} — ${esc(a.verdict)}</option>`).join('');

  return `
    <div class="view-head">
      <h2>Substitution assessments</h2>
      <p>${esc(ds.meta.description)}</p>
    </div>
    <div class="callout callout-danger">
      <strong>Direction matters and is never inferred.</strong>
      Each assessment runs baseline → candidate. The reverse relation is never drawn
      automatically, and no transitive edge is composed. SA-001 and SA-006 below assess the
      <em>same pair in the same context</em> in opposite directions and reach opposite verdicts.
    </div>
    ${ds.no_directly_substitutable ? `<div class="callout callout-info">
      <strong>No DirectlySubstitutable assessment exists in the pilot.</strong>
      Every pair examined needs at least a change of shaft or hub feature.</div>` : ''}
    <div class="legend">${verdictLegend}</div>

    <div class="panel">
      <h3>Side-by-side comparison</h3>
      <div class="btn-row" style="margin-bottom:.6rem">
        <label class="ctrl">Left <select id="cmp-left">${options}</select></label>
        <label class="ctrl">Right <select id="cmp-right">${options}</select></label>
        <button class="btn btn-primary" id="cmp-primary">Show the SA-001 / SA-006 pair</button>
      </div>
      <div class="compare-grid" id="cmp-grid"></div>
    </div>

    <div class="panel">
      <h3>Assessment graph</h3>
      <div class="graph-shell">${gv.toolbarHtml()}</div>
    </div>`;
};

VIEWS.substitutions.after = function (target) {
  const ds = STATE.data.substitutions_graph;
  const gv = STATE.graphs.substitutions;
  gv.opts.onNodeSelect = (d) => {
    if (d.nodeType === 'assessment') {
      const sa = ds.assessments.find(a => a.id === d.label);
      if (sa) { showDetail(sa.id, assessmentCardHtml(sa)); return; }
    }
    showDetail(d.label || d.id, gv.defaultNodeDetail(d));
  };
  gv.mount(); gv.wire(document.getElementById('view-root'));

  const left = document.getElementById('cmp-left');
  const right = document.getElementById('cmp-right');
  const grid = document.getElementById('cmp-grid');
  const draw = () => {
    const a = ds.assessments.find(x => x.id === left.value);
    const b = ds.assessments.find(x => x.id === right.value);
    grid.innerHTML = (a ? assessmentCardHtml(a) : '') + (b ? assessmentCardHtml(b) : '');
    wireCrossLinks(grid);
  };
  const primary = () => {
    left.value = ds.primary_pair[0]; right.value = ds.primary_pair[1]; draw();
  };
  left.addEventListener('change', draw);
  right.addEventListener('change', draw);
  document.getElementById('cmp-primary').addEventListener('click', primary);

  if (target && ds.assessments.some(a => a.id === target)) {
    left.value = target;
    const other = ds.assessments.find(a => a.id !== target);
    right.value = (target === 'SA-001') ? 'SA-006' : (other ? other.id : target);
    draw();
  } else {
    primary();
  }
};

/* ---- G. Claims ---- */
VIEWS.claims = function () {
  const ds = STATE.data.claims_graph;
  const topics = ds.topics;
  const subjects = Array.from(new Set(ds.claims.map(c => c.subject))).sort();
  const concepts = Array.from(new Set(ds.claims.flatMap(c => c.about))).sort();
  return `
    <div class="view-head">
      <h2>Claims</h2>
      <p>${num(ds.claims.length)} normalized claims, each attributed to exactly one source and
         reaching a printed page through at least one verified evidence span.</p>
    </div>
    <div class="callout callout-warn">
      ${reviewBadge('NeedsReview')} All claims are at <code>NeedsReview</code>. They were authored
      by an analyst reading the cited pages and mechanically re-verified against the PDF, which is
      stronger than automatic extraction but is not human sign-off.
    </div>
    <details class="filters" open>
      <summary>Filters</summary>
      <div class="filters-body">
        <div class="fgroup"><label class="flabel" for="cf-text">Free text</label>
          <input type="search" id="cf-text" placeholder="statement, subject, object…"></div>
        <div class="fgroup"><label class="flabel" for="cf-topic">Topic</label>
          <select id="cf-topic"><option value="">All topics</option>
            ${topics.map(t => `<option value="${esc(t)}">${esc(titleCase(t))}</option>`).join('')}</select></div>
        <div class="fgroup"><label class="flabel" for="cf-review">Review status</label>
          <select id="cf-review"><option value="">All</option>
            ${Object.keys(ds.review_states).map(r => `<option value="${esc(r)}">${esc(r)}</option>`).join('')}</select></div>
        <div class="fgroup"><label class="flabel" for="cf-integrity">Evidence integrity</label>
          <select id="cf-integrity"><option value="">All</option>
            <option value="reliable">reliable</option>
            <option value="partial-glyph-loss">partial-glyph-loss</option>
            <option value="glyph-mismapped">glyph-mismapped</option>
            <option value="unverified">unverified</option></select></div>
        <div class="fgroup"><label class="flabel" for="cf-subject">Claim subject</label>
          <select id="cf-subject"><option value="">All subjects</option>
            ${subjects.map(s => `<option value="${esc(s)}">${esc(s.slice(0, 60))}</option>`).join('')}</select></div>
        <div class="fgroup"><label class="flabel" for="cf-concept">Ontology concept</label>
          <select id="cf-concept"><option value="">Any concept</option>
            ${concepts.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('')}</select></div>
        <div class="fgroup"><label class="flabel">Content</label>
          <div class="btn-row">
            <label class="ctrl"><input type="checkbox" id="cf-qty"> Has quantities</label>
            <label class="ctrl"><input type="checkbox" id="cf-art"> Eq/table/figure/example</label>
            <label class="ctrl"><input type="checkbox" id="cf-auth"> Needs external authority</label>
          </div></div>
      </div>
    </details>
    <div class="tbl-meta" id="cf-count"></div>
    <div class="tbl-wrap" style="max-height:560px">
      <table class="tbl"><thead><tr>
        <th data-sort="claim_id">Claim</th><th data-sort="doc_id">Source</th>
        <th data-sort="topic">Topic</th><th data-sort="subject">Subject</th>
        <th class="nosort">Statement</th><th data-sort="review_status">Review</th>
        <th class="nosort">Pages</th>
      </tr></thead><tbody id="claims-body"></tbody></table>
    </div>`;
};

function claimDetailHtml(c) {
  const spanCards = c.evidence_span_ids.map((sid, i) => {
    const span = (STATE.data.evidence_graph.spans || []).find(s => s.span_id === sid);
    const cite = c.citations[i];
    if (!span) return `<li>${esc(sid)} <span class="missing">span record not found</span></li>`;
    const warn = span.text_integrity === 'glyph-mismapped'
      ? `<div class="callout callout-danger"><strong>Glyph-mismapped text</strong>
           This PDF mis-maps mathematics glyphs onto unrelated ASCII. The excerpt below is stored
           for traceability only and must <em>not</em> be read as the printed equation.</div>` : '';
    return `<li>
      <div><strong>${esc(sid)}</strong> ${integrityBadge(span.text_integrity)}</div>
      <div class="small muted">▪ ${orMissing(cite)}</div>
      ${warn}
      ${fields([
        ['Book', esc(span.book_title)],
        ['Edition', esc(span.edition)],
        ['Chapter', `${orMissing(span.chapter_number)} — ${orMissing(span.chapter_title)}`],
        ['Section', `${orMissing(span.section_number)} — ${orMissing(span.section_title)}`],
        ['Printed page', orMissing(span.printed_page)],
        ['PDF page index', esc(span.pdf_page_index)],
        ['Block id', `<code class="small">${esc(span.block_id)}</code>`],
        ['Bounding box', `<code class="small">${esc((span.bbox || []).join(', '))}</code>`],
        ['Cited items', span.artifact_labels.length ? esc(span.artifact_labels.join('; ')) : null]
      ])}
      <div class="dnote">${esc(span.extracted_text)}</div>
      <div>${linkTo('evidence', sid, 'Open in Evidence view')}</div>
    </li>`;
  }).join('');

  const qty = c.quantities.map(q => `<li>
      <strong>${esc(q.role)}</strong>:
      ${q.is_range ? `${esc(q.range_min)} – ${esc(q.range_max)}` : esc(q.value)}
      <code>${esc(q.unit)}</code>
      <div class="small muted">As printed: “${esc(q.original_value)}” ${esc(q.original_unit)}</div>
      ${q.conversion_method ? `<div class="small muted">Conversion: ${esc(q.conversion_method)}</div>` : ''}
      ${provenanceBadge(q.value_provenance)}
    </li>`).join('');

  const th = c.threshold;
  return [
    fields([
      ['Claim id', `<code>${esc(c.claim_id)}</code>`],
      ['Source', `${esc(c.book_title)} (${esc(c.edition)} ed.)`],
      ['Topic', esc(titleCase(c.topic))],
      ['Type', esc(c.claim_type)],
      ['Review', reviewBadge(c.review_status) + (c.reviewed_by ? esc(c.reviewed_by) : '')],
      ['Extraction confidence', esc(c.extraction_confidence)],
      ['Extraction method', `<span class="small">${esc(c.extraction_method)}</span>`],
      ['Evidence integrity', integrityBadge(c.text_integrity)],
      ['Printed pages', c.printed_pages.length ? esc(c.printed_pages.join(', ')) : null],
      ['PDF page indices', c.pdf_page_indices.length ? esc(c.pdf_page_indices.join(', ')) : null]
    ]),
    section('Normalized statement', `<p>${esc(c.normalized_statement)}</p>`),
    section('Subject · predicate · object', fields([
      ['Subject', esc(c.subject)], ['Predicate', esc(c.predicate)], ['Object', esc(c.object)]
    ])),
    section('Conditions stated by the source', c.conditions.length ? list(c.conditions) : `<p class="missing">${esc(NOT_STATED)}</p>`),
    section('Assumptions', c.assumptions.length ? list(c.assumptions) : `<p class="missing">${esc(NOT_STATED)}</p>`),
    section('Exceptions', c.exceptions.length ? list(c.exceptions) : ''),
    section('Quantities', qty ? `<ul class="dlist">${qty}</ul>` : `<p class="missing">No numeric quantity in this claim.</p>`),
    th ? section('Threshold definition', `
      ${fields([['Term', esc(th.term)],
                ['Claimed universal', th.is_universal ? 'yes' : 'no — context-dependent']])}
      ${th.scope_note ? `<div class="dnote">${esc(th.scope_note)}</div>` : ''}
      ${!th.is_universal ? `<div class="callout callout-warn small">The source did not fix a universal boundary for this term, so none is asserted.</div>` : ''}`) : '',
    c.verification ? section('Verification recorded by this claim', `
      ${fields([
        ['Method kind', esc(c.verification.method_kind || 'VerificationMethod')],
        ['Test recommended', c.verification.test_recommended ? 'yes' : 'no'],
        ['Procedure specified', c.verification.test_procedure_specified ? 'yes' : '<strong>no</strong>'],
        ['Acceptance criterion specified', c.verification.acceptance_criterion_specified ? 'yes' : '<strong>no</strong>']
      ])}
      ${authorityBadges(c.verification.external_authority)}
      ${!c.verification.test_procedure_specified ? `<div class="callout callout-warn small">
        The source recommends a test but defines no procedure and no acceptance criterion.
        An external authority is required to close the gap.</div>` : ''}`) : '',
    (c.equations.length || c.tables.length || c.figures.length || c.examples.length || c.procedures.length || c.standards.length)
      ? section('Cited items', fields([
          ['Equations', c.equations.length ? esc(c.equations.join(', ')) : null],
          ['Tables', c.tables.length ? esc(c.tables.join(', ')) : null],
          ['Figures', c.figures.length ? esc(c.figures.join(', ')) : null],
          ['Examples', c.examples.length ? esc(c.examples.join(', ')) : null],
          ['Procedures', c.procedures.length ? esc(c.procedures.join(', ')) : null],
          ['Standards', c.standards.length ? esc(c.standards.join('; ')) : null]
        ])) : '',
    c.equation_transcription ? `<div class="callout callout-info small">
      <strong>Equation transcription</strong>
      Source: <code>${esc(c.equation_transcription.source)}</code>.
      ${esc(c.equation_transcription.note || '')}</div>` : '',
    c.external_authority.length ? section('External authority required', authorityBadges(c.external_authority)) : '',
    section('Related ontology entities', c.about.length
      ? list(c.about, a => `<li><code>${esc(a)}</code></li>`)
      : `<p class="missing">No ontology entity linked.</p>`),
    c.analyst_note ? `<div class="callout callout-warn"><strong>Analyst note</strong>${esc(c.analyst_note)} ${provenanceBadge('EngineeringInference')}</div>` : '',
    section(`Supporting evidence (${c.evidence_span_ids.length})`,
      spanCards ? `<ul class="dlist">${spanCards}</ul>` : `<p class="missing">No evidence span — this would fail validation.</p>`)
  ].join('');
};

VIEWS.claims.after = function (target) {
  const ds = STATE.data.claims_graph;
  const body = document.getElementById('claims-body');
  const countEl = document.getElementById('cf-count');
  let sortKey = 'claim_id', sortAsc = true;

  const filtered = () => {
    const text = (document.getElementById('cf-text').value || '').toLowerCase();
    const topic = document.getElementById('cf-topic').value;
    const review = document.getElementById('cf-review').value;
    const integrity = document.getElementById('cf-integrity').value;
    const subject = document.getElementById('cf-subject').value;
    const concept = document.getElementById('cf-concept').value;
    const qty = document.getElementById('cf-qty').checked;
    const art = document.getElementById('cf-art').checked;
    const auth = document.getElementById('cf-auth').checked;

    return ds.claims.filter(c => {
      if (STATE.sourceFilter !== 'all' && c.doc_id !== STATE.sourceFilter) return false;
      if (topic && c.topic !== topic) return false;
      if (review && c.review_status !== review) return false;
      if (integrity && c.text_integrity !== integrity) return false;
      if (subject && c.subject !== subject) return false;
      if (concept && c.about.indexOf(concept) < 0) return false;
      if (qty && !c.has_quantities) return false;
      if (art && !c.has_artifacts) return false;
      if (auth && !c.requires_external_authority) return false;
      if (text) {
        const blob = `${c.claim_id} ${c.normalized_statement} ${c.subject} ${c.predicate} ${c.object}`.toLowerCase();
        if (blob.indexOf(text) < 0) return false;
      }
      return true;
    }).sort((a, b) => {
      const x = String(a[sortKey] || ''), y = String(b[sortKey] || '');
      return sortAsc ? x.localeCompare(y) : y.localeCompare(x);
    });
  };

  const draw = () => {
    const rows = filtered();
    countEl.textContent = `${rows.length} of ${ds.claims.length} claims shown`;
    body.innerHTML = rows.length ? rows.map(c => `
      <tr data-claim="${esc(c.claim_id)}">
        <td class="nowrap"><code>${esc(c.claim_id)}</code></td>
        <td class="nowrap">${esc(c.doc_id)}</td>
        <td class="nowrap">${esc(titleCase(c.topic))}</td>
        <td>${esc(c.subject.slice(0, 46))}${c.subject.length > 46 ? '…' : ''}</td>
        <td>${esc(c.normalized_statement.slice(0, 130))}${c.normalized_statement.length > 130 ? '…' : ''}</td>
        <td class="nowrap">${reviewBadge(c.review_status)}</td>
        <td class="nowrap small">${esc(c.printed_pages.join(', ') || '—')}</td>
      </tr>`).join('')
      : `<tr><td colspan="7" class="muted" style="padding:1.2rem;text-align:center">No claim matches these filters.</td></tr>`;
    body.querySelectorAll('tr[data-claim]').forEach(tr => {
      tr.addEventListener('click', () => {
        body.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
        tr.classList.add('selected');
        const c = ds.claims.find(x => x.claim_id === tr.getAttribute('data-claim'));
        if (c) showDetail(c.claim_id, claimDetailHtml(c));
      });
    });
  };

  ['cf-text', 'cf-topic', 'cf-review', 'cf-integrity', 'cf-subject', 'cf-concept',
   'cf-qty', 'cf-art', 'cf-auth'].forEach(id => {
    const node = document.getElementById(id);
    if (node) node.addEventListener('input', draw);
  });
  document.querySelectorAll('th[data-sort]').forEach(th => th.addEventListener('click', () => {
    const key = th.getAttribute('data-sort');
    sortAsc = (key === sortKey) ? !sortAsc : true;
    sortKey = key; draw();
  }));

  draw();
  if (target) {
    const c = ds.claims.find(x => x.claim_id === target);
    if (c) {
      showDetail(c.claim_id, claimDetailHtml(c));
      const tr = body.querySelector(`tr[data-claim="${CSS.escape(target)}"]`);
      if (tr) { tr.classList.add('selected'); tr.scrollIntoView({ block: 'center' }); }
    }
  }
};

/* ---- G2. Evidence ---- */
VIEWS.evidence = function () {
  const ds = STATE.data.evidence_graph;
  const gv = mountGraph('evidence', 'cy-evid', ds, { layout: 'breadthfirst', nodeLimit: 200 });
  const counts = ds.integrity_counts;
  return `
    <div class="view-head">
      <h2>Evidence spans</h2>
      <p>${num(ds.spans.length)} verified spans. Every one was re-checked against its PDF at build
         time: the anchor phrase must still be on the stated page, and the recorded page label must
         still match the PDF's own label.</p>
    </div>
    <div class="callout callout-info">
      <strong>Citations are assembled, never stored.</strong>
      Book, edition, chapter, section, printed page, PDF page index and any equation/table/figure
      number travel as separate fields and are composed at read time by the project's own
      citation logic.
    </div>
    <details class="filters" open>
      <summary>Filters</summary>
      <div class="filters-body">
        <div class="fgroup"><label class="flabel" for="ef-text">Free text</label>
          <input type="search" id="ef-text" placeholder="excerpt, chapter, section…"></div>
        <div class="fgroup"><label class="flabel">Text integrity</label>
          <div class="chips" id="ef-integrity">
            ${['reliable', 'partial-glyph-loss', 'glyph-mismapped', 'unverified'].map(k =>
              `<button class="chip" role="switch" aria-pressed="true" data-integrity="${esc(k)}">
                 ${esc(k)} <span class="small">(${num(counts[k] || 0)})</span></button>`).join('')}
          </div></div>
        <div class="fgroup"><label class="flabel">Usage</label>
          <div class="btn-row">
            <label class="ctrl"><input type="checkbox" id="ef-unused"> Only spans not cited by any claim</label>
          </div></div>
      </div>
    </details>
    <div class="tbl-meta" id="ef-count"></div>
    <div class="tbl-wrap" style="max-height:420px">
      <table class="tbl"><thead><tr>
        <th class="nosort">Span</th><th class="nosort">Source</th><th class="nosort">Chapter</th>
        <th class="nosort">Section</th><th class="nosort">Printed p.</th><th class="nosort">PDF idx</th>
        <th class="nosort">Integrity</th><th class="nosort">Claims</th>
      </tr></thead><tbody id="evid-body"></tbody></table>
    </div>
    <div class="panel" style="margin-top:1rem">
      <h3>Provenance hierarchy</h3>
      <div class="graph-shell">${gv.toolbarHtml()}</div>
    </div>`;
};

function spanDetailHtml(s) {
  const warn = s.text_integrity === 'glyph-mismapped'
    ? `<div class="callout callout-danger">
        <strong>Glyph-mismapped — the extracted text is not authoritative</strong>
        This document's mathematics fonts decode to unrelated ASCII characters (for example
        <code>a = 10/3</code> extracts as <code>a 5 10y3</code>). The excerpt below is retained for
        traceability only. Any equation resting on this span was transcribed from a rendered page
        image instead.</div>`
    : (s.text_integrity === 'partial-glyph-loss'
      ? `<div class="callout callout-warn"><strong>Partial glyph loss</strong>
          Some mathematics glyphs (primes, operators) are dropped by this document's text layer.</div>` : '');
  return [
    fields([
      ['Span id', `<code>${esc(s.span_id)}</code>`],
      ['Book', esc(s.book_title)],
      ['Authors', esc((s.authors || []).join(', '))],
      ['Edition', esc(s.edition)],
      ['Chapter', `${orMissing(s.chapter_number)} — ${orMissing(s.chapter_title)}`],
      ['Section', `${orMissing(s.section_number)} — ${orMissing(s.section_title)}`],
      ['Printed page', orMissing(s.printed_page)],
      ['PDF page index', esc(s.pdf_page_index)],
      ['PDF page number', esc(s.pdf_page_number)],
      ['Page label / style', `${orMissing(s.page_label)} <span class="small muted">(${esc(s.page_label_style)})</span>`],
      ['Block id', `<code class="small">${esc(s.block_id)}</code>`],
      ['Bounding box', `<code class="small">${esc((s.bbox || []).join(', '))}</code>`],
      ['Text integrity', integrityBadge(s.text_integrity)],
      ['Math-font ratio', esc(s.math_font_char_ratio)],
      ['Extraction method', `<span class="small">${esc(s.extraction_method)}</span>`],
      ['Anchor match mode', esc(s.match_mode)],
      ['Extraction confidence', esc(s.extraction_confidence)]
    ]),
    section('Assembled citation', `<div class="dnote">▪ ${orMissing(s.citation)}</div>`),
    warn,
    section('Extracted excerpt', `<div class="dnote">${esc(s.extracted_text)}</div>
      ${s.excerpt_truncated ? '<p class="small muted">Excerpt truncated — the store proves the citation, it is not a copy of the book.</p>' : ''}`),
    section('Verified anchor', `<div class="dnote small">${esc(s.anchor)}</div>`),
    section('Cited items', s.artifact_labels.length ? list(s.artifact_labels) : `<p class="missing">No numbered item attached.</p>`),
    s.note ? section('Curator note', `<p>${esc(s.note)}</p>`) : '',
    section('Cited by claims', s.used_by_claims.length
      ? list(s.used_by_claims, c => `<li>${linkTo('claims', c, c)}</li>`)
      : `<p class="missing">Not cited by any claim yet.</p>`)
  ].join('');
}

VIEWS.evidence.after = function (target) {
  const ds = STATE.data.evidence_graph;
  const gv = STATE.graphs.evidence;
  gv.opts.onNodeSelect = (d) => {
    if (d.nodeType === 'span') {
      const s = ds.spans.find(x => x.span_id === d.spanId);
      if (s) { showDetail(s.span_id, spanDetailHtml(s)); return; }
    }
    showDetail(d.label || d.id, gv.defaultNodeDetail(d));
  };
  gv.mount(); gv.wire(document.getElementById('view-root'));

  const body = document.getElementById('evid-body');
  const countEl = document.getElementById('ef-count');
  const activeIntegrity = new Set(['reliable', 'partial-glyph-loss', 'glyph-mismapped', 'unverified']);

  const draw = () => {
    const text = (document.getElementById('ef-text').value || '').toLowerCase();
    const unusedOnly = document.getElementById('ef-unused').checked;
    const rows = ds.spans.filter(s => {
      if (STATE.sourceFilter !== 'all' && s.doc_id !== STATE.sourceFilter) return false;
      if (!activeIntegrity.has(s.text_integrity)) return false;
      if (unusedOnly && s.used_by_claims.length) return false;
      if (text) {
        const blob = `${s.span_id} ${s.extracted_text} ${s.chapter_title} ${s.section_title} ${s.anchor}`.toLowerCase();
        if (blob.indexOf(text) < 0) return false;
      }
      return true;
    });
    countEl.textContent = `${rows.length} of ${ds.spans.length} spans shown`;
    body.innerHTML = rows.length ? rows.map(s => `
      <tr data-span="${esc(s.span_id)}">
        <td class="nowrap"><code>${esc(s.span_id)}</code></td>
        <td class="nowrap">${esc(s.doc_id)}</td>
        <td class="nowrap">${esc(s.chapter_number)}</td>
        <td>${esc(String(s.section_number))} ${esc(String(s.section_title).slice(0, 34))}</td>
        <td class="nowrap right">${esc(s.printed_page)}</td>
        <td class="nowrap right">${esc(s.pdf_page_index)}</td>
        <td class="nowrap">${integrityBadge(s.text_integrity)}</td>
        <td class="nowrap right">${num(s.used_by_claims.length)}</td>
      </tr>`).join('')
      : `<tr><td colspan="8" class="muted" style="padding:1.2rem;text-align:center">No span matches these filters.</td></tr>`;
    body.querySelectorAll('tr[data-span]').forEach(tr => tr.addEventListener('click', () => {
      body.querySelectorAll('tr').forEach(r => r.classList.remove('selected'));
      tr.classList.add('selected');
      const s = ds.spans.find(x => x.span_id === tr.getAttribute('data-span'));
      if (s) showDetail(s.span_id, spanDetailHtml(s));
    }));
  };

  document.getElementById('ef-text').addEventListener('input', draw);
  document.getElementById('ef-unused').addEventListener('change', draw);
  document.querySelectorAll('[data-integrity]').forEach(btn => btn.addEventListener('click', () => {
    const k = btn.getAttribute('data-integrity');
    const on = btn.getAttribute('aria-pressed') === 'true';
    btn.setAttribute('aria-pressed', String(!on));
    if (on) activeIntegrity.delete(k); else activeIntegrity.add(k);
    draw();
  }));

  draw();
  if (target) {
    const s = ds.spans.find(x => x.span_id === target);
    if (s) {
      showDetail(s.span_id, spanDetailHtml(s));
      const tr = body.querySelector(`tr[data-span="${CSS.escape(target)}"]`);
      if (tr) { tr.classList.add('selected'); tr.scrollIntoView({ block: 'center' }); }
    }
  }
};

/* ---- H. Cross-book alignments ---- */
VIEWS.alignments = function () {
  const ds = STATE.data.alignments_graph;
  const gv = mountGraph('alignments', 'cy-align', ds, { layout: 'cose', nodeLimit: 150 });
  const typeChips = ds.all_types.map(t => {
    const n = (ds.alignment_type_counts[t] || 0) + (ds.terminology_type_counts[t] || 0);
    return `<button class="chip" role="switch" aria-pressed="${n > 0}" data-atype="${esc(t)}" ${n === 0 ? 'disabled' : ''}>
      ${esc(t)} <span class="small">(${n})</span></button>`;
  }).join('');

  const featured = ds.featured.map(f => `
    <div class="panel">
      <h3>${esc(f.title)}</h3>
      <p class="small">${esc(f.summary)}</p>
      <div class="btn-row">
        ${f.claim_ids.map(id => `<button class="btn" data-open-align="${esc(id)}">${esc(id)}</button>`).join('')}
        ${f.concept_ids.map(id => `<button class="btn" data-open-term="${esc(id)}">${esc(id)}</button>`).join('')}
      </div>
    </div>`).join('');

  return `
    <div class="view-head">
      <h2>Cross-book alignments</h2>
      <p>Mott 6e on the left, Shigley 10e on the right. ${num(ds.alignments.length)} claim
         alignments and ${num(ds.terminology.length)} terminology alignments.</p>
    </div>
    <div class="callout callout-danger">
      <strong>Nothing is merged.</strong>
      Where the books differ, both claims stay in the graph and the alignment records the
      difference and its reason. Conflicting or differently scoped claims are never combined
      into a single statement.
    </div>
    <h3>Featured comparisons</h3>
    <div class="panel-grid">${featured}</div>
    <details class="filters" open>
      <summary>Filter alignments</summary>
      <div class="filters-body">
        <div class="fgroup" style="min-width:100%"><label class="flabel">Alignment type</label>
          <div class="chips">${typeChips}</div></div>
        <div class="fgroup"><label class="flabel" for="af-topic">Topic</label>
          <select id="af-topic"><option value="">All topics</option>
            ${Array.from(new Set(ds.alignments.flatMap(a => a.topics))).sort()
              .map(t => `<option value="${esc(t)}">${esc(titleCase(t))}</option>`).join('')}</select></div>
      </div>
    </details>
    <div class="tbl-meta" id="af-count"></div>
    <div id="align-list"></div>
    <div class="panel" style="margin-top:1rem">
      <h3>Terminology alignments</h3>
      <div class="tbl-wrap" style="max-height:340px">
        <table class="tbl"><thead><tr>
          <th class="nosort">Id</th><th class="nosort">Common concept</th>
          <th class="nosort">Mott term / symbol</th><th class="nosort">Shigley term / symbol</th>
          <th class="nosort">Type</th>
        </tr></thead><tbody id="term-body"></tbody></table>
      </div>
    </div>
    <div class="panel" style="margin-top:1rem">
      <h3>Alignment graph</h3>
      <div class="graph-shell">${gv.toolbarHtml()}</div>
    </div>`;
};

function alignmentSplitHtml(a) {
  const side = (c, cls, book) => `
    <div class="align-side ${cls}">
      <h4>${esc(book)}</h4>
      <div><code>${esc(c.claim_id)}</code> <span class="small muted">${esc(titleCase(c.topic))}</span></div>
      <p class="small">${esc(c.statement)}</p>
      ${(c.citations || []).filter(Boolean).map(x => `<div class="small muted">▪ ${esc(x)}</div>`).join('')}
      <div class="btn-row" style="margin-top:.4rem">${linkTo('claims', c.claim_id, 'Open claim')}</div>
    </div>`;
  return `
    <div class="align-split">
      ${side(a.claim_a, 'mott', 'Mott 6e')}
      <div class="align-mid">
        <span class="align-type">${esc(a.alignment_type)}</span>
        <div class="small muted" style="margin-top:.3rem">${esc(a.relation || '')}</div>
      </div>
      ${side(a.claim_b, 'shigley', 'Shigley 10e')}
    </div>
    ${fields([
      ['Common concept', esc(a.common_concept)],
      ['Review', reviewBadge(a.review_status)]
    ])}
    ${a.differing_conditions ? section('Differing conditions', `<p>${esc(a.differing_conditions)}</p>`) : ''}
    ${a.differing_assumptions ? section('Differing assumptions', `<p>${esc(a.differing_assumptions)}</p>`) : ''}
    ${a.analyst_note ? `<div class="callout callout-warn"><strong>Analyst note</strong>${esc(a.analyst_note)} ${provenanceBadge('EngineeringInference')}</div>` : ''}`;
}

VIEWS.alignments.after = function (target) {
  const ds = STATE.data.alignments_graph;
  const gv = STATE.graphs.alignments;
  gv.opts.onNodeSelect = (d) => {
    if (d.nodeType === 'alignment') {
      const a = ds.alignments.find(x => x.id === d.label);
      if (a) { showDetail(a.id, alignmentSplitHtml(a)); return; }
    }
    if (d.nodeType === 'claim') { navigate('claims', d.label); return; }
    showDetail(d.label || d.id, gv.defaultNodeDetail(d));
  };
  gv.mount(); gv.wire(document.getElementById('view-root'));

  const activeTypes = new Set(ds.all_types.filter(t =>
    (ds.alignment_type_counts[t] || 0) + (ds.terminology_type_counts[t] || 0) > 0));
  const listEl = document.getElementById('align-list');
  const countEl = document.getElementById('af-count');
  const termBody = document.getElementById('term-body');

  const draw = () => {
    const topic = document.getElementById('af-topic').value;
    const rows = ds.alignments.filter(a => {
      if (!activeTypes.has(a.alignment_type)) return false;
      if (topic && a.topics.indexOf(topic) < 0) return false;
      if (STATE.sourceFilter !== 'all') {
        if (a.claim_a.doc_id !== STATE.sourceFilter && a.claim_b.doc_id !== STATE.sourceFilter) return false;
      }
      return true;
    });
    countEl.textContent = `${rows.length} of ${ds.alignments.length} claim alignments shown`;
    listEl.innerHTML = rows.length ? rows.map(a => `
      <div class="panel" id="align-${esc(a.id)}">
        <h3>${esc(a.id)} <span class="align-type">${esc(a.alignment_type)}</span></h3>
        ${alignmentSplitHtml(a)}
      </div>`).join('')
      : `<div class="panel muted">No alignment matches these filters.</div>`;
    wireCrossLinks(listEl);

    const terms = ds.terminology.filter(t => activeTypes.has(t.alignment_type));
    termBody.innerHTML = terms.map(t => `
      <tr data-term="${esc(t.id)}">
        <td class="nowrap"><code>${esc(t.id)}</code></td>
        <td>${esc(t.common_concept)}</td>
        <td>${esc(t.mott6_term.slice(0, 54))}<div class="small muted mono">${esc(t.mott6_symbol)}</div></td>
        <td>${esc(t.shigley10_term.slice(0, 54))}<div class="small muted mono">${esc(t.shigley10_symbol)}</div></td>
        <td class="nowrap">${esc(t.alignment_type)}</td>
      </tr>`).join('');
    termBody.querySelectorAll('tr[data-term]').forEach(tr => tr.addEventListener('click', () => {
      const t = ds.terminology.find(x => x.id === tr.getAttribute('data-term'));
      if (!t) return;
      showDetail(t.common_concept, [
        fields([
          ['Alignment id', `<code>${esc(t.id)}</code>`],
          ['Type', esc(t.alignment_type)],
          ['Core concept', esc(t.core_concept)],
          ['Mott 6e term', esc(t.mott6_term)],
          ['Mott 6e symbol', `<code>${esc(t.mott6_symbol)}</code>`],
          ['Shigley 10e term', esc(t.shigley10_term)],
          ['Shigley 10e symbol', `<code>${esc(t.shigley10_symbol)}</code>`],
          ['Review', reviewBadge(t.review_status)]
        ]),
        t.analyst_note ? `<div class="callout callout-warn"><strong>Analyst note</strong>${esc(t.analyst_note)} ${provenanceBadge('EngineeringInference')}</div>` : '',
        section('Evidence', t.evidence_span_ids.length
          ? list(t.evidence_span_ids, s => `<li>${linkTo('evidence', s, s)}</li>`)
          : `<p class="missing">No evidence span linked.</p>`),
        `<div class="callout callout-info small">Symbols from the two books are never merged:
          the same letter can mean different quantities in each.</div>`
      ].join(''));
    }));
  };

  document.querySelectorAll('[data-atype]').forEach(btn => btn.addEventListener('click', () => {
    if (btn.disabled) return;
    const t = btn.getAttribute('data-atype');
    const on = btn.getAttribute('aria-pressed') === 'true';
    btn.setAttribute('aria-pressed', String(!on));
    if (on) activeTypes.delete(t); else activeTypes.add(t);
    draw();
  }));
  document.getElementById('af-topic').addEventListener('change', draw);
  document.querySelectorAll('[data-open-align]').forEach(b => b.addEventListener('click', () => {
    const a = ds.alignments.find(x => x.id === b.getAttribute('data-open-align'));
    if (a) {
      showDetail(a.id, alignmentSplitHtml(a));
      const node = document.getElementById('align-' + a.id);
      if (node) node.scrollIntoView({ block: 'center' });
    }
  }));
  document.querySelectorAll('[data-open-term]').forEach(b => b.addEventListener('click', () => {
    const tr = termBody.querySelector(`tr[data-term="${CSS.escape(b.getAttribute('data-open-term'))}"]`);
    if (tr) { tr.click(); tr.scrollIntoView({ block: 'center' }); }
  }));

  draw();
  if (target) {
    const a = ds.alignments.find(x => x.id === target);
    if (a) {
      showDetail(a.id, alignmentSplitHtml(a));
      const node = document.getElementById('align-' + a.id);
      if (node) node.scrollIntoView({ block: 'center' });
    } else {
      const t = ds.terminology.find(x => x.id === target);
      if (t) {
        const tr = termBody.querySelector(`tr[data-term="${CSS.escape(target)}"]`);
        if (tr) tr.click();
      }
    }
  }
};

/* ---- I. Rules ---- */
VIEWS.rules = function () {
  const ds = STATE.data.rules;
  return `
    <div class="view-head">
      <h2>Rule layer</h2>
      <p>${num(ds.rules.length)} selection, substitution and verification rules. The rule layer is
         deliberately kept out of OWL: this logic is conditional, context-bound and revisable, and
         expressing it as subclass axioms would make it monotonic.</p>
    </div>
    <div class="callout callout-warn"><strong>Declarative, not executed.</strong> ${esc(ds.notice)}</div>
    <details class="filters" open>
      <summary>Filters</summary>
      <div class="filters-body">
        <div class="fgroup"><label class="flabel" for="rf-group">Category</label>
          <select id="rf-group"><option value="">All</option>
            ${Object.keys(ds.counts_by_group).map(g =>
              `<option value="${esc(g)}">${esc(titleCase(g.replace('_rules', '')))} (${ds.counts_by_group[g]})</option>`).join('')}
          </select></div>
        <div class="fgroup"><label class="flabel">Attribution</label>
          <div class="btn-row">
            <label class="ctrl"><input type="checkbox" id="rf-analyst"> Analyst-authored only</label>
            <label class="ctrl"><input type="checkbox" id="rf-nonexec"> Not executable</label>
            <label class="ctrl"><input type="checkbox" id="rf-auth"> Needs external authority</label>
          </div></div>
        <div class="fgroup"><label class="flabel" for="rf-text">Free text</label>
          <input type="search" id="rf-text" placeholder="rule id, title, statement…"></div>
      </div>
    </details>
    <div class="tbl-meta" id="rf-count"></div>
    <div class="tbl-wrap" style="max-height:520px">
      <table class="tbl"><thead><tr>
        <th class="nosort">Rule</th><th class="nosort">Kind</th><th class="nosort">Title</th>
        <th class="nosort">Attribution</th><th class="nosort">Executable</th><th class="nosort">Authority</th>
      </tr></thead><tbody id="rules-body"></tbody></table>
    </div>`;
};

function ruleDetailHtml(r) {
  const guardHtml = r.guard ? `<pre class="dnote small mono">${esc(JSON.stringify(r.guard, null, 2))}</pre>` : '';
  const appliesHtml = r.applies_when ? `<pre class="dnote small mono">${esc(JSON.stringify(r.applies_when, null, 2))}</pre>` : '';
  const appliesToHtml = r.applies_to ? `<pre class="dnote small mono">${esc(JSON.stringify(r.applies_to, null, 2))}</pre>` : '';
  const effectHtml = r.effect ? `<pre class="dnote small mono">${esc(JSON.stringify(r.effect, null, 2))}</pre>` : '';
  const verifHtml = (r.requires_verification || []).length
    ? `<pre class="dnote small mono">${esc(JSON.stringify(r.requires_verification, null, 2))}</pre>` : '';
  return [
    fields([
      ['Rule id', `<code>${esc(r.id)}</code>`],
      ['Category', esc(titleCase(r.group.replace('_rules', '')))],
      ['Kind', esc(r.kind)],
      ['Attribution', r.analyst_authored
        ? provenanceBadge('EngineeringInference') + ' analyst-authored'
        : provenanceBadge('SourceDerivedValue') + ' derived from cited claims'],
      ['Confidence', r.confidence === null || r.confidence === undefined ? null : esc(r.confidence)],
      ['Review', reviewBadge(r.review_status)],
      ['Executable', r.executable === false
        ? '<strong>No</strong> — see below'
        : (r.executable === true ? 'Yes' : 'Not declared (declarative layer only)')]
    ]),
    section('Statement', `<p>${esc(r.statement)}</p>`),
    r.not_executable_because ? `<div class="callout callout-warn">
      <strong>Not currently executable</strong>${esc(r.not_executable_because)}</div>` : '',
    section('Applies when (inputs / preconditions)', appliesHtml || appliesToHtml || guardHtml
      || `<p class="missing">No guard recorded.</p>`),
    guardHtml && (appliesHtml || appliesToHtml) ? section('Guard', guardHtml) : '',
    section('Result / consequence', effectHtml || `<p class="missing">${esc(NOT_STATED)}</p>`),
    (r.prohibitions || []).length ? section('Prohibitions', list(r.prohibitions)) : '',
    (r.preconditions || []).length ? section('Preconditions', list(r.preconditions, p =>
      `<li>${esc(p.statement || p)}${p.derived_from ? `<div class="small muted">from ${esc((p.derived_from || []).join(', '))}</div>` : ''}</li>`)) : '',
    verifHtml ? section('Required verification', verifHtml) : '',
    r.acceptance ? section('Acceptance', `
      ${fields([['Specified by source', r.acceptance.specified_by_source ? 'yes' : '<strong>no</strong>']])}
      <p class="small">${esc(r.acceptance.statement || NOT_STATED)}</p>
      ${authorityBadges(r.acceptance.requires_external_authority)}`) : '',
    (r.open_parameters || []).length ? section('Unresolved parameters', list(r.open_parameters, p =>
      `<li><code>${esc(p.symbol)}</code> — ${esc(p.name)}
        <div class="small">${badge('badge-insufficient', p.status || 'not specified')}</div></li>`)) : '',
    (r.unit_constraints || []).length ? section('Unit constraints', list(r.unit_constraints)) : '',
    r.external_authorities.length ? section('External authority required', authorityBadges(r.external_authorities)) : '',
    section('Referenced ontology entities', r.referenced_entities.length
      ? list(r.referenced_entities, e => `<li><code>${esc(e)}</code></li>`)
      : `<p class="missing">None referenced.</p>`),
    section('Evidence requirement', `<p>${esc(r.evidence_requirement)}</p>`),
    section('Referenced claims', r.derived_from_details.length
      ? list(r.derived_from_details, c => `<li>${linkTo('claims', c.claim_id, c.claim_id)}
          <span class="small muted">(${esc(c.doc_id)})</span>
          <div class="small">${esc(c.statement.slice(0, 190))}${c.statement.length > 190 ? '…' : ''}</div></li>`)
      : `<p class="missing">No cited claim — this rule declares itself analyst-authored.</p>`),
    r.notes ? `<div class="callout callout-info"><strong>Note</strong>${esc(r.notes)}</div>` : ''
  ].join('');
}

VIEWS.rules.after = function (target) {
  const ds = STATE.data.rules;
  const body = document.getElementById('rules-body');
  const countEl = document.getElementById('rf-count');

  const draw = () => {
    const group = document.getElementById('rf-group').value;
    const analyst = document.getElementById('rf-analyst').checked;
    const nonexec = document.getElementById('rf-nonexec').checked;
    const auth = document.getElementById('rf-auth').checked;
    const text = (document.getElementById('rf-text').value || '').toLowerCase();
    const rows = ds.rules.filter(r => {
      if (group && r.group !== group) return false;
      if (analyst && !r.analyst_authored) return false;
      if (nonexec && r.executable !== false) return false;
      if (auth && !r.external_authorities.length) return false;
      if (text && `${r.id} ${r.title} ${r.statement}`.toLowerCase().indexOf(text) < 0) return false;
      return true;
    });
    countEl.textContent = `${rows.length} of ${ds.rules.length} rules shown`;
    body.innerHTML = rows.length ? rows.map(r => `
      <tr data-rule="${esc(r.id)}">
        <td class="nowrap"><code>${esc(r.id)}</code></td>
        <td class="nowrap">${esc(r.kind.replace('Rule', ''))}</td>
        <td>${esc(r.title)}</td>
        <td class="nowrap">${r.analyst_authored ? provenanceBadge('EngineeringInference') : provenanceBadge('SourceDerivedValue')}</td>
        <td class="nowrap">${r.executable === false ? badge('badge-insufficient', 'not executable') : badge('badge-neutral', 'declarative')}</td>
        <td class="nowrap">${r.external_authorities.length ? authorityBadges(r.external_authorities.slice(0, 1)) + (r.external_authorities.length > 1 ? `<span class="small muted">+${r.external_authorities.length - 1}</span>` : '') : '—'}</td>
      </tr>`).join('')
      : `<tr><td colspan="6" class="muted" style="padding:1.2rem;text-align:center">No rule matches these filters.</td></tr>`;
    body.querySelectorAll('tr[data-rule]').forEach(tr => tr.addEventListener('click', () => {
      body.querySelectorAll('tr').forEach(x => x.classList.remove('selected'));
      tr.classList.add('selected');
      const r = ds.rules.find(x => x.id === tr.getAttribute('data-rule'));
      if (r) showDetail(r.id, ruleDetailHtml(r));
    }));
  };

  ['rf-group', 'rf-analyst', 'rf-nonexec', 'rf-auth', 'rf-text'].forEach(id => {
    const node = document.getElementById(id);
    if (node) node.addEventListener('input', draw);
  });
  draw();
  if (target) {
    const r = ds.rules.find(x => x.id === target);
    if (r) {
      showDetail(r.id, ruleDetailHtml(r));
      const tr = body.querySelector(`tr[data-rule="${CSS.escape(target)}"]`);
      if (tr) { tr.classList.add('selected'); tr.scrollIntoView({ block: 'center' }); }
    }
  }
};

/* ---- J. Coverage ---- */
VIEWS.coverage = function () {
  const ds = STATE.data.coverage;
  const depthClass = pages => pages === 0 ? 'cov-0' : pages < 30 ? 'cov-1' : pages < 55 ? 'cov-2' : pages < 80 ? 'cov-3' : 'cov-4';
  const rows = ds.rows.map(r => `
    <tr data-topic="${esc(r.topic_key)}">
      <td>${esc(r.topic)}<div class="small muted">${esc(r.group)}</div></td>
      <td class="cov-cell ${depthClass(r.mott6.pages)}">
        ${r.mott6.covered ? `${num(r.mott6.pages)} pp.<div class="small">ch. ${esc(r.mott6.chapters.join(', '))}</div>` : '—'}</td>
      <td class="cov-cell ${depthClass(r.shigley10.pages)}">
        ${r.shigley10.covered ? `${num(r.shigley10.pages)} pp.<div class="small">ch. ${esc(r.shigley10.chapters.join(', '))}</div>` : '—'}</td>
      <td class="nowrap">${esc(r.coverage)}</td>
      <td class="right">${r.claim_count ? num(r.claim_count) : '<span class="muted">0</span>'}</td>
      <td class="nowrap">
        ${r.is_pilot_topic ? badge('badge-source', 'Pilot topic') : badge('badge-neutral', 'Taxonomy only')}
        ${r.has_substitution_assessment ? badge('badge-normalized', 'Has substitution') : ''}
      </td>
    </tr>`).join('');
  return `
    <div class="view-head">
      <h2>Source coverage</h2>
      <p>${num(ds.rows.length)} domain topics against the two books. Chapter numbers and page
         ranges come from each PDF's own outline; the mapping of chapters onto topics is analyst
         judgement.</p>
    </div>
    <div class="callout callout-warn"><strong>Structure is complete; claims are a pilot.</strong> ${esc(ds.notice)}</div>
    <div class="legend">
      ${['cov-0', 'cov-1', 'cov-2', 'cov-3', 'cov-4'].map((c, i) =>
        `<span class="legend-item"><span class="legend-swatch ${c}" style="border-color:var(--border-strong)"></span>
          ${['not covered', '<30 pp.', '30–55 pp.', '55–80 pp.', '80+ pp.'][i]}</span>`).join('')}
    </div>
    <div class="tbl-meta">
      ${Object.keys(ds.coverage_counts).sort().map(k =>
        `<strong>${esc(k)}</strong>: ${num(ds.coverage_counts[k])}`).join(' &nbsp;·&nbsp; ')}
    </div>
    <div class="tbl-wrap" style="max-height:620px">
      <table class="tbl"><thead><tr>
        <th class="nosort">Topic</th><th class="nosort">Mott 6e</th><th class="nosort">Shigley 10e</th>
        <th class="nosort">Coverage</th><th class="nosort right">Claims</th><th class="nosort">Status</th>
      </tr></thead><tbody>${rows}</tbody></table>
    </div>`;
};

VIEWS.coverage.after = function (target) {
  const ds = STATE.data.coverage;
  document.querySelectorAll('tr[data-topic]').forEach(tr => tr.addEventListener('click', () => {
    const r = ds.rows.find(x => x.topic_key === tr.getAttribute('data-topic'));
    if (!r) return;
    document.querySelectorAll('tr[data-topic]').forEach(x => x.classList.remove('selected'));
    tr.classList.add('selected');
    showDetail(r.topic, [
      fields([
        ['Topic key', `<code>${esc(r.topic_key)}</code>`],
        ['Group', esc(r.group)],
        ['Coverage', esc(r.coverage)],
        ['Depth note', esc(r.depth_note)],
        ['Normalized claims', num(r.claim_count)],
        ['Status', esc(r.status)]
      ]),
      section('Mott 6e', r.mott6.covered ? fields([
        ['Chapters', esc(r.mott6.chapters.join(', '))],
        ['Chapter titles', esc(r.mott6.chapter_titles)],
        ['Pages', num(r.mott6.pages)],
        ['Sections', num(r.mott6.sections)],
        ['Starts at printed p.', esc(r.mott6.printed_pages.join(', '))]
      ]) : `<p class="missing">Not covered by this source.</p>`),
      section('Shigley 10e', r.shigley10.covered ? fields([
        ['Chapters', esc(r.shigley10.chapters.join(', '))],
        ['Chapter titles', esc(r.shigley10.chapter_titles)],
        ['Pages', num(r.shigley10.pages)],
        ['Sections', num(r.shigley10.sections)],
        ['Starts at printed p.', esc(r.shigley10.printed_pages.join(', '))]
      ]) : `<p class="missing">Not covered by this source.</p>`),
      r.coverage !== 'both' ? `<div class="callout callout-info small">
        Only one book covers this topic, so no cross-book alignment is possible. A query asking
        whether the books agree correctly returns nothing rather than a fabricated consensus.</div>` : '',
      !r.is_pilot_topic ? `<div class="callout callout-warn small">
        Taxonomy only: page structure was extracted, but v0.1 contains no normalized claims for
        this topic.</div>` : ''
    ].join(''));
  }));
  if (target) {
    const tr = document.querySelector(`tr[data-topic="${CSS.escape(target)}"]`);
    if (tr) { tr.click(); tr.scrollIntoView({ block: 'center' }); }
  }
};

/* ---- K. Evidence pipeline ---- */
const PIPELINE = [
  { stage: 'Source PDF', detail: 'The concrete file, identified by SHA-256 so provenance cannot drift onto a different scan.',
    checks: ['SHA-256 source identity recorded on ev:SourceDocument and re-checked on every build'] },
  { stage: 'Page', detail: 'PDF page index (0-based) and the printed page label, read from the PDF page-label tree.',
    checks: ['Printed page never computed from the PDF index', 'Page-label style recorded (arabic / roman / named / none)'] },
  { stage: 'Text block', detail: 'Text blocks with bounding boxes and per-block font statistics.',
    checks: ['Math-font character ratio computed per block', 'Text-integrity verdict assigned'] },
  { stage: 'Evidence seed', detail: 'The analyst writes only: document, PDF page index, and a short anchor phrase read on that page.',
    checks: ['Seed file has no fields for chapter, section or page — they cannot be typed'] },
  { stage: 'Verified EvidenceSpan', detail: 'The builder resolves the printed page, chapter, section, block and bounding box, and verifies the anchor.',
    checks: ['Anchor verification — build FAILS if the phrase is not on the stated page',
             'Page-label verification against the PDF\'s own label',
             'De-hyphenated match, with a hyphenation-blind fallback recorded in match_mode'],
    gate: false },
  { stage: 'Extracted / Normalized Claim', detail: 'Claim content joined to its spans; location copied from the span, never typed.',
    checks: ['A claim with no evidence is rejected outright', 'Units validated with Pint; a missing unit is an error',
             'Review status clamped — the pipeline may never emit HumanVerified'] },
  { stage: 'Alignment', detail: 'Cross-book comparison as a reified record; both claims survive.',
    checks: ['Conflicting claims are never merged', 'Alignment must join two different documents'] },
  { stage: 'Candidate rule', detail: 'A normalized claim proposed for promotion into the rule layer.',
    checks: ['Every rule must cite a claim or declare itself analyst-authored'] },
  { stage: 'Substitution assessment', detail: 'Reified, directional judgement bound to a function, a context and a requirement set.',
    checks: ['No reverse edge is generated automatically', 'No transitive edge is composed',
             'ConditionallySubstitutable requires a condition or a modification',
             'DirectlySubstitutable requires positive interface evidence'] },
  { stage: 'HUMAN REVIEW GATE', detail: 'Only a person may promote a claim past NeedsReview. The pipeline cannot cross this line.',
    checks: ['HumanVerified requires a named reviewer and a date', 'v0.1 contains zero HumanVerified claims'],
    gate: true },
  { stage: 'Possible promotion', detail: 'A human-validated rule may become an OWL axiom or an executable rule.',
    checks: ['Not reached in v0.1'] }
];

VIEWS.pipeline = function () {
  const d = STATE.data.overview;
  const v = d.validation;
  const stages = PIPELINE.map((s, i) => `
    ${i ? '<div class="pipe-arrow" aria-hidden="true">↓</div>' : ''}
    <div class="pipe-stage ${s.gate ? 'pipe-gate' : ''}">
      <h4>${s.gate ? '⛔ ' : ''}${esc(s.stage)}</h4>
      <p class="small">${esc(s.detail)}</p>
      <div class="pipe-checks">${s.checks.map(c => badge('badge-verified', c)).join('')}</div>
    </div>`).join('');

  const globalChecks = v ? v.checks.map(c =>
    `<tr><td><code>${esc(c.check)}</code></td>
       <td>${c.passed ? badge('badge-verified', 'pass') : badge('badge-rejected', 'fail')}</td>
       <td class="right">${num(c.items_checked)}</td></tr>`).join('') : '';

  return `
    <div class="view-head">
      <h2>Evidence pipeline</h2>
      <p>How a page of a book becomes a citable claim, and what stops a citation being invented at
         each step.</p>
    </div>
    <div class="callout callout-ok">
      <strong>The anti-fabrication mechanism</strong>
      The authoring order is inverted. An analyst writes only a document, a page index and an anchor
      phrase; everything citable is resolved from the PDF and verified against it. A drifted
      citation breaks the build rather than lying.
    </div>
    <div class="panel-grid">
      <div>${stages}</div>
      <div>
        <div class="panel">
          <h3>Repository-wide checks</h3>
          ${v ? `<div class="tbl-wrap"><table class="tbl"><thead><tr>
            <th class="nosort">Check</th><th class="nosort">Result</th><th class="nosort right">Items</th>
          </tr></thead><tbody>${globalChecks}</tbody></table></div>`
            : `<p class="missing">Validation report not available.</p>`}
        </div>
        <div class="panel">
          <h3>Text-integrity distribution</h3>
          <div class="tbl-wrap"><table class="tbl"><thead><tr>
            <th class="nosort">Status</th><th class="nosort right">Occurrences</th></tr></thead><tbody>
            ${Object.keys(d.text_integrity).sort().map(k =>
              `<tr><td>${integrityBadge(k)}</td><td class="right">${num(d.text_integrity[k])}</td></tr>`).join('')}
          </tbody></table></div>
          <p class="small muted" style="margin-top:.5rem">Counts include documents, spans and claims,
            each of which carries its own integrity verdict.</p>
        </div>
        <div class="panel">
          <h3>Reproducibility</h3>
          <p class="small">The whole pipeline is idempotent: unchanged inputs produce byte-identical
            outputs. Verified by building twice and comparing digests.</p>
          ${badge('badge-verified', 'Deterministic JSON — sorted keys, no timestamps')}
          ${badge('badge-verified', 'Vendored library pinned by SHA-256')}
        </div>
      </div>
    </div>`;
};

/* --------------------------------------------------------------------------
   7. Global search
   -------------------------------------------------------------------------- */

function runSearch(query) {
  const box = document.getElementById('search-results');
  const input = document.getElementById('global-search');
  const q = query.trim().toLowerCase();
  if (q.length < 2) {
    box.hidden = true; input.setAttribute('aria-expanded', 'false'); return;
  }
  const tokens = q.split(/\s+/).filter(Boolean);
  const scored = [];
  STATE.data.search_index.entries.forEach(e => {
    let score = 0;
    for (const t of tokens) {
      const inLabel = e.label.toLowerCase().indexOf(t);
      const inId = e.id.toLowerCase().indexOf(t);
      const inText = e.text.indexOf(t);
      if (inLabel < 0 && inId < 0 && inText < 0) { score = -1; break; }
      if (inId === 0 || inLabel === 0) score += 12;
      else if (inLabel >= 0) score += 7;
      else if (inId >= 0) score += 5;
      else score += 1;
    }
    if (score > 0) scored.push({ e, score });
  });
  scored.sort((a, b) => b.score - a.score || a.e.label.localeCompare(b.e.label));

  const groups = {};
  scored.slice(0, 90).forEach(({ e }) => { (groups[e.type] = groups[e.type] || []).push(e); });

  box.innerHTML = Object.keys(groups).length
    ? Object.keys(groups).sort().map(type => `
        <div class="search-group-head">${esc(type)} (${groups[type].length})</div>
        ${groups[type].slice(0, 12).map(e => `
          <button class="search-item" data-view="${esc(e.view)}" data-target="${esc(e.target)}">
            ${esc(e.label)}${STATE.showKo && e.ko ? ' · ' + esc(e.ko) : ''}
            <span class="si-sub">${esc(e.sub || e.id)}</span>
          </button>`).join('')}`).join('')
    : `<div class="search-empty">No match for “${esc(query)}”.</div>`;

  box.hidden = false;
  input.setAttribute('aria-expanded', 'true');
  box.querySelectorAll('.search-item').forEach(btn => btn.addEventListener('click', () => {
    box.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    navigate(btn.getAttribute('data-view'), btn.getAttribute('data-target'));
  }));
}

/* --------------------------------------------------------------------------
   8. Routing
   -------------------------------------------------------------------------- */

function navigate(view, target) {
  if (!VIEWS[view]) { toast(`Unknown view: ${view}`); return; }
  STATE.view = view;
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.getAttribute('data-view') === view) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  const root = document.getElementById('view-root');
  root.innerHTML = VIEWS[view]();
  wireCrossLinks(root);
  if (VIEWS[view].after) {
    try { VIEWS[view].after(target); }
    catch (err) { console.error(`view "${view}" after-hook failed`, err); toast('View failed to initialise; see console.'); }
  }
  const hash = target ? `#${view}/${encodeURIComponent(target)}` : `#${view}`;
  if (location.hash !== hash) history.replaceState(null, '', hash);
  document.getElementById('main').scrollTop = 0;
  window.scrollTo(0, 0);
}

function readHash() {
  const raw = (location.hash || '').replace(/^#/, '');
  if (!raw) return { view: 'overview', target: null };
  const [view, ...rest] = raw.split('/');
  return { view: VIEWS[view] ? view : 'overview', target: rest.length ? decodeURIComponent(rest.join('/')) : null };
}

/* --------------------------------------------------------------------------
   9. Boot
   -------------------------------------------------------------------------- */

function wireChrome() {
  document.querySelectorAll('.nav-btn').forEach(btn =>
    btn.addEventListener('click', () => navigate(btn.getAttribute('data-view'))));

  document.getElementById('detail-close').addEventListener('click', hideDetail);

  const search = document.getElementById('global-search');
  let searchTimer = null;
  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => runSearch(search.value), 110);
  });
  search.addEventListener('keydown', ev => {
    const box = document.getElementById('search-results');
    if (ev.key === 'Escape') { box.hidden = true; search.setAttribute('aria-expanded', 'false'); search.blur(); }
    if (ev.key === 'ArrowDown' && !box.hidden) {
      const first = box.querySelector('.search-item');
      if (first) { ev.preventDefault(); first.focus(); }
    }
    if (ev.key === 'Enter') {
      const first = box.querySelector('.search-item');
      if (first && !box.hidden) { ev.preventDefault(); first.click(); }
    }
  });
  document.addEventListener('click', ev => {
    const box = document.getElementById('search-results');
    if (!box.hidden && !ev.target.closest('.search-wrap')) {
      box.hidden = true; search.setAttribute('aria-expanded', 'false');
    }
  });
  document.addEventListener('keydown', ev => {
    if (ev.key === '/' && document.activeElement !== search &&
        !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      ev.preventDefault(); search.focus();
    }
    if (ev.key === 'Escape') hideDetail();
  });

  document.getElementById('toggle-ko').addEventListener('change', ev => {
    STATE.showKo = ev.target.checked;
    Object.values(STATE.graphs).forEach(g => { if (g.cy) g.cy.style().update(); });
    navigate(STATE.view);
  });
  document.getElementById('filter-source').addEventListener('change', ev => {
    STATE.sourceFilter = ev.target.value;
    navigate(STATE.view);
  });
  window.addEventListener('hashchange', () => {
    const { view, target } = readHash();
    if (view !== STATE.view || target) navigate(view, target);
  });
}

function boot() {
  Promise.all(DATASETS.map(name =>
    fetch(`data/${name}.json`).then(r => {
      if (!r.ok) throw new Error(`${name}.json → HTTP ${r.status}`);
      return r.json();
    }).then(json => [name, json])
  )).then(pairs => {
    pairs.forEach(([name, json]) => { STATE.data[name] = json; });
    document.getElementById('loading').hidden = true;
    document.getElementById('view-root').hidden = false;
    document.getElementById('pilot-text').textContent = STATE.data.overview.warning;
    wireChrome();
    const { view, target } = readHash();
    navigate(view, target);
  }).catch(err => {
    console.error(err);
    document.getElementById('loading').innerHTML = `
      <div class="callout callout-danger" style="text-align:left;max-width:640px;margin:0 auto">
        <strong>Could not load the generated datasets.</strong>
        ${esc(err.message)}<br><br>
        This application must be served over HTTP — <code>fetch()</code> is blocked on
        <code>file://</code>. From the repository root run:<br>
        <code>python3 -m http.server 8000</code><br>
        then open <code>http://localhost:8000/outputs/visualizations/</code><br><br>
        If the files are missing, rebuild them with:<br>
        <code>python3 scripts/build_html_visualization.py</code>
      </div>`;
  });
}

document.addEventListener('DOMContentLoaded', boot);
