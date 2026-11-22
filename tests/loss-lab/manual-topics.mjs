import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

export const manual = readFileSync(new URL('../../dist/tools/loss-lab/manual.html', import.meta.url), 'utf8');

// The full manual has editorial chapters; quick helpers keep their compact copy.
// Verify each helper topic still resolves to a substantive manual section.
export function assertManualTopic(topic) {
  const section = [...manual.matchAll(/<section\b[^>]*>[\s\S]*?<\/section>/g)]
    .find(match => match[0].includes(`id="manual-${topic}"`))?.[0];
  assert.ok(section, `Manual section for ${topic}`);
  const text = section.replace(/<[^>]*>/g, '').trim();
  assert.ok(text.length > 100, `Substantive guidance for ${topic}`);
  return section;
}
