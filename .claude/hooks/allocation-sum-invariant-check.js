#!/usr/bin/env node
// WealthWise hook (PostToolUse Write|Edit): every seeded allocation-template row must sum to exactly
// 10 000 basis points (100.00%) — AC-02, BR-09, NFR-08. Blocks with exit 2 and a fix hint.
'use strict';

const fs = require('fs');

const ROW = /\(\s*(\d+)\s*,\s*'(CONSERVATIVE|MODERATE|AGGRESSIVE)'\s*,\s*'(SHORT|MEDIUM|LONG)'\s*,\s*'([A-Z][A-Z0-9_]*)'\s*,\s*(-?\d+)\s*\)/g;

function sums(sql) {
  const totals = new Map();
  let match;
  while ((match = ROW.exec(sql)) !== null) {
    const key = `v${match[1]} ${match[2]}/${match[3]}`;
    totals.set(key, (totals.get(key) || 0) + Number.parseInt(match[5], 10));
  }
  return totals;
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (_) {
    return 0;
  }
  const filePath = ((input.tool_input && input.tool_input.file_path) || '').replace(/\\/g, '/');
  if (!/\/migrations\/[^/]+\.sql$/.test(filePath)) return 0;
  let sql;
  try {
    sql = fs.readFileSync(filePath, 'utf8');
  } catch (_) {
    return 0;
  }
  if (!sql.includes('allocation_template_rows')) return 0;
  const bad = [...sums(sql).entries()].filter(([, total]) => total !== 10000);
  if (bad.length === 0) return 0;
  const lines = bad.map(([key, total]) => `  ${key}: ${total} bp (${(total / 100).toFixed(2)}%)`).join('\n');
  process.stderr.write(
    `BLOCKED (allocation-sum-invariant): template rows in ${filePath} must each total 10000 bp:\n${lines}\n` +
      'Fix: adjust target_bp so every (version, band, horizon) row sums to exactly 10000, and include every ' +
      'active asset class (KD-07). See .claude/skills/policy-version-validator/SKILL.md.\n'
  );
  return 2;
}

process.exit(main());
