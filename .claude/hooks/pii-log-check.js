#!/usr/bin/env node
// WealthWise hook (PostToolUse Write|Edit on src/**/*.py): logs carry IDs and codes only (NFR-03).
// Blocks f-string log messages and `extra=` keys that name PII or financial-position data.
'use strict';

const fs = require('fs');

const DENY = new Set([
  'full_name', 'name', 'email', 'date_of_birth', 'dob', 'note', 'reason', 'units', 'value', 'amount',
  'target_amount', 'current_value', 'total', 'total_value', 'nav', 'percent_complete', 'password', 'token',
  'answers',
]);
const LOG_CALL = /\blog(?:ger)?\.(?:debug|info|warning|error|exception|critical)\(\s*f["']/g;
const EXTRA = /\bextra\s*=\s*\{([^}]*)\}/g;
const KEY = /["']([a-zA-Z_]+)["']\s*:/g;

function findProblems(source) {
  const problems = [];
  if (LOG_CALL.test(source)) problems.push('log message is an f-string (event names must be constant)');
  let block;
  while ((block = EXTRA.exec(source)) !== null) {
    let key;
    while ((key = KEY.exec(block[1])) !== null) {
      if (DENY.has(key[1].toLowerCase())) problems.push(`extra key "${key[1]}" may contain PII or balances`);
    }
  }
  return problems;
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (_) {
    return 0;
  }
  const filePath = ((input.tool_input && input.tool_input.file_path) || '').replace(/\\/g, '/');
  if (!/\/src\/.+\.py$/.test(filePath)) return 0;
  let source;
  try {
    source = fs.readFileSync(filePath, 'utf8');
  } catch (_) {
    return 0;
  }
  const problems = findProblems(source);
  if (problems.length === 0) return 0;
  process.stderr.write(
    `BLOCKED (pii-log-check): ${filePath}\n${problems.map((p) => `  - ${p}`).join('\n')}\n` +
      'Fix: log only IDs, codes, counts and durations, e.g. log.info("goal_created", extra={"goal_id": goal_id}).\n'
  );
  return 2;
}

process.exit(main());
