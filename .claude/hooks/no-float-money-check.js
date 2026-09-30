#!/usr/bin/env node
// WealthWise hook (PostToolUse Write|Edit): no floating point in money layers (NFR-01).
// Applies to src/types, src/domain, src/repository and src/service Python files.
'use strict';

const fs = require('fs');

const STRINGS = /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/g;
const COMMENTS = /#.*$/gm;
const FLOAT_USE = /\bfloat\b/;
const FLOAT_LITERAL = /(?<![\w.])\d+\.\d*(?:[eE][+-]?\d+)?(?![\w.])|(?<![\w.])\d+[eE][+-]?\d+(?![\w.])/;

function main() {
  let input;
  try {
    input = JSON.parse(fs.readFileSync(0, 'utf8'));
  } catch (_) {
    return 0;
  }
  const filePath = ((input.tool_input && input.tool_input.file_path) || '').replace(/\\/g, '/');
  if (!/\/src\/(types|domain|repository|service)\/.+\.py$/.test(filePath)) return 0;
  let source;
  try {
    source = fs.readFileSync(filePath, 'utf8');
  } catch (_) {
    return 0;
  }
  const code = source.replace(STRINGS, '""').replace(COMMENTS, '');
  const problems = [];
  code.split('\n').forEach((line, index) => {
    if (FLOAT_USE.test(line)) problems.push(`line ${index + 1}: uses float`);
    else if (FLOAT_LITERAL.test(line)) problems.push(`line ${index + 1}: float literal`);
  });
  if (problems.length === 0) return 0;
  process.stderr.write(
    `BLOCKED (no-float-money): ${filePath}\n${problems.map((p) => `  - ${p}`).join('\n')}\n` +
      'Fix: use decimal.Decimal with string construction (Decimal("0.01")) and the helpers in ' +
      'src/types/fixed_point.py. See .claude/skills/drift-calculator/SKILL.md.\n'
  );
  return 2;
}

process.exit(main());
