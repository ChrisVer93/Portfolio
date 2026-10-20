import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HELP_ARTICLES, helpRecapHTML, setupSteps, topicForIssue} from '../../dist/tools/loss-lab/help-content.js';
import {demoProject} from '../../dist/tools/loss-lab/io.js';
import {checkProject} from '../../dist/tools/loss-lab/preflight.js';
import {runProject} from '../../dist/tools/loss-lab/engine.js';

const root = new URL('../../dist/tools/loss-lab/', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8');
const manual = read('manual.html');

test('V8 manual removes the marked overview sections in print and quick help', () => {
  for (const id of ['quick-start', 'characteristics', 'zero-floor', 'sensitivity', 'limits']) {
    assert.ok(!HELP_ARTICLES.some(a => a.id === id), id);
    assert.ok(!manual.includes('id="manual-' + id + '"'), id);
    assert.ok(!manual.includes('href="#manual-' + id + '"'), id);
    assert.ok(!helpRecapHTML().includes('id="manual-' + id + '"'), id);
  }
  assert.equal((manual.match(/class="doc-tool-screenshot"/g) || []).length, 18);
  for (const article of HELP_ARTICLES) assert.ok(manual.includes('id="manual-' + article.id + '"'), article.id);
  for (const step of setupSteps(demoProject(), checkProject(demoProject()), null)) {
    assert.ok(HELP_ARTICLES.some(a => a.id === step.topic), step.title);
  }
  assert.equal(topicForIssue({curveId:'curve-1',message:'Curve unavailable'}), 'components');
  assert.equal(topicForIssue({message:'Negative physical magnitude projected'}), 'interpolation');
});

test('V8 corrections are reflected in Help Centre and full manual', () => {
  const get = id => HELP_ARTICLES.find(a => a.id === id);
  assert.ok(get('waveforms').sections[0].paragraphs[0].includes('MATLAB level-5 MAT'));
  assert.ok(!get('waveforms').sections.some(s => s.heading === 'Current limits'));
  assert.ok(!get('waveforms').sections[0].paragraphs.join(' ').includes('invalid unused column'));
  assert.equal(get('passives').title, 'Capacitor ESR, inductor winding and core loss');
  assert.ok(!get('passives').sections.some(s => s.heading === 'Spectral quality'));
  assert.ok(!get('debug').sections.some(s => s.heading === 'Linked traces'));
  for (const forbidden of [
    'An invalid unused column can still fail validation.',
    'The spectral form is P = Idc²Rdc',
    '<h3>Current limits</h3>',
    '<h3>Linked traces</h3>',
    'Equal-weight means are over the selected sampled operating points',
  ]) assert.ok(!manual.includes(forbidden), forbidden);
  assert.ok(manual.includes('Capacitor ESR, inductor winding and core loss'));
});

test('V8 supported upload types match picker and drag-and-drop validation', () => {
  const html = read('index.html'), app = read('app.js');
  assert.ok(html.includes('id="waveFiles" multiple accept=".csv,.txt,.json,.mat"'));
  assert.match(app, /Unsupported file type\. Import CSV, TXT, JSON or MATLAB level-5 MAT/);
  assert.ok(manual.includes('JSON files with a columns object or a named numeric matrix'));
});

test('V8 study limits are enforced before large allocations', () => {
  const project = demoProject(), c = project.instances[0].candidates[0];
  project.instances[0].candidates = Array.from({length: 201}, (_, index) => ({
    ...c, id: 'v8-alt-' + index,
  }));
  assert.ok(checkProject(project).errors.some(x => /at most 200 alternative combinations/.test(x.message)));
  assert.throws(() => runProject(project), /More than 200 combinations/);
});
