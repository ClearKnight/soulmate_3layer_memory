// Simple local validation - no external API calls required
const fs = require('fs');
const path = require('path');

console.log('Validating Soulmate Memory System...');

const checks = [
  { name: 'config.py', path: path.join(__dirname, '..', 'config.py') },
  { name: 'memory_system dir', path: path.join(__dirname, '..', 'memory_system') },
  { name: 'api dir', path: path.join(__dirname, '..', 'api') },
  { name: 'evomap dir', path: path.join(__dirname, '..', 'evomap') }
];

let passed = 0;
let failed = 0;

for (const check of checks) {
  if (fs.existsSync(check.path)) {
    console.log(`✓ ${check.name} exists`);
    passed++;
  } else {
    console.log(`✗ ${check.name} not found`);
    failed++;
  }
}

// Also check for key files
const keyFiles = [
  'memory_system/memory_system.py',
  'memory_system/models.py',
  'api/main.py',
  'evomap/gep_adapter.py'
];

for (const file of keyFiles) {
  const filePath = path.join(__dirname, '..', file);
  if (fs.existsSync(filePath)) {
    console.log(`✓ ${file}`);
    passed++;
  } else {
    console.log(`✗ ${file} not found`);
    failed++;
  }
}

console.log(`\nValidation result: ${passed} passed, ${failed} failed`);

if (failed > 0) {
  process.exit(1);
}

console.log('✓ All checks passed');
process.exit(0);