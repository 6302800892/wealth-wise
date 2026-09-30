#!/usr/bin/env node
// WealthWise hook (PreToolUse Write|Edit): committed migrations are append-only (NFR-05) — this also keeps
// published policy/template seeds immutable (AC-10). New, uncommitted migration files may be edited freely.
'use strict';

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

function isCommitted(filePath) {
  const result = spawnSync('git', ['ls-files', '--error-unmatch', path.basename(filePath)], {
    cwd: path.dirname(filePath),
    encoding: 'utf8',
  });
  return result.status === 0;
}

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (_) {
    return 0;
  }
  const filePath = (input.tool_input && input.tool_input.file_path) || '';
  const normalized = filePath.replace(/\\/g, '/');
  if (!/\/migrations\/\d{4}_[a-z0-9_]+\.sql$/.test(normalized)) return 0;
  if (!fs.existsSync(filePath) || !isCommitted(filePath)) return 0;
  process.stderr.write(
    `BLOCKED (migration-append-only): ${path.basename(filePath)} is already committed and may have been applied.\n` +
      'Migrations are append-only (NFR-05); the runner refuses to start when an applied checksum changes.\n' +
      'Fix: create the next numbered file, e.g. migrations/NNNN_describe_change.sql, with the corrective SQL.\n'
  );
  return 2;
}

process.exit(main());
