import test from 'node:test';
import assert from 'node:assert/strict';
import {manual} from './manual-topics.mjs';

test('official V18 manual has complete navigation and self-contained screenshots', () => {
  const ids = [...manual.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(new Set(ids).size, ids.length, 'unique section and control IDs');
  for (const match of manual.matchAll(/href="#([^"]+)"/g)) {
    assert.ok(ids.includes(match[1]), `valid link to ${match[1]}`);
  }
  const images = [...manual.matchAll(/<img\b[^>]*\bsrc="([^"]+)"/g)];
  assert.equal(images.length, 29);
  for (const [, src] of images) {
    assert.ok(src.startsWith('data:image/png;base64,'), 'embedded PNG screenshot');
    assert.equal(Buffer.from(src.split(',')[1].replace(/\s/g, ''), 'base64').subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  }
  assert.ok(manual.includes('href="Loss_Lab_Manual_Offline.zip"'));
  assert.ok(manual.includes('href="./"'));
  assert.ok(!manual.includes('OFFLINE PREVIEW · NOT DEPLOYED'));
  assert.ok(!manual.includes('published Portfolio manual remains unchanged'));
});

test('V18 publishes the annotated results chapter with diagnostics and sensitivity', () => {
  const section = id => manual.match(new RegExp(`<section\\b[^>]*id="${id}"[^>]*>[\\s\\S]*?<\\/section>`))?.[0] || '';
  assert.ok(!section('s-6-6'));
  for (const id of ['s-6-2', 's-6-3', 's-6-4', 's-6-5', 's-6-8', 's-6-9']) {
    assert.ok(section(id).includes('section6-figure'), `supplied screenshot in ${id}`);
  }
  assert.ok(!section('s-6-4').includes('<table'));
  assert.ok(!section('s-6-3').includes('Reading filters'));
  assert.ok(section('s-6-9').includes('This section shall be used to validate the tool results.'));
  assert.ok(section('s-6-9').includes('Diagnostics and result validation'));
  assert.ok(section('s-6-9').includes('Sensitivity analysis'));
  assert.equal((section('s-6-9').match(/section6-figure/g) || []).length, 3);
});
