#!/usr/bin/env node

import fs from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const packageRoot = path.resolve(__dirname, '..');

const isColorSupported = !process.env.NO_COLOR && (Boolean(process.stdout.isTTY) || Boolean(process.env.FORCE_COLOR));
const c = {
  cyan: (s) => isColorSupported ? `\x1b[36m${s}\x1b[0m` : s,
  green: (s) => isColorSupported ? `\x1b[32m${s}\x1b[0m` : s,
  yellow: (s) => isColorSupported ? `\x1b[33m${s}\x1b[0m` : s,
  red: (s) => isColorSupported ? `\x1b[31m${s}\x1b[0m` : s,
  dim: (s) => isColorSupported ? `\x1b[2m${s}\x1b[0m` : s,
  bold: (s) => isColorSupported ? `\x1b[1m${s}\x1b[0m` : s,
  magenta: (s) => isColorSupported ? `\x1b[35m${s}\x1b[0m` : s,
};

const SKILL_DESCRIPTIONS = {
  'notes-start': 'Coordinates the learning flow and diagnostic questions',
  'notes-create-outline': 'Generates course outlines and Mermaid dependency graphs',
  'notes-conduct-quiz': 'Runs diagnostics, check-in quizzes, and review questions',
  'notes-ask': 'Answers mid-lesson questions and logs them to questions.md',
  'notes-create-coding-lessons': 'Generates programming lessons with code examples',
  'notes-create-general-lessons': 'Generates lessons for non-coding and practical topics',
  'notes-validate-coding-lessons': 'Checks coding lessons for syntax and API accuracy',
  'notes-validate-general-lessons': 'Checks non-coding lessons for factual accuracy',
};

function printBanner() {
  console.log(`
${c.bold('notes-skills installer')}
${c.dim('Install notes & learning skills for your agent')}
`);
}

function printUsage() {
  printBanner();
  console.log(`${c.bold('Usage:')}
  npx github:asquilatan/notes-skills [options]

${c.bold('Options:')}
  ${c.green('--repo, --local')}         Install into current project repository (.agent/skills)
  ${c.green('--global, -g')}            Install into global Gemini config (~/.gemini/config/skills)
  ${c.green('--agents-global')}         Install into global Agents config (~/.agents/skills)
  ${c.green('--dest <path>')}           Install into a custom target directory
  ${c.green('--all, -y, --yes')}        Install all skills without confirmation
  ${c.green('--force')}                 Overwrite existing skill directories without asking
  ${c.green('--help, -h')}              Show this help message

${c.bold('Examples:')}
  ${c.dim('# Interactive wizard (Recommended)')}
  npx github:asquilatan/notes-skills

  ${c.dim('# Install locally in the current repo')}
  npx github:asquilatan/notes-skills --repo

  ${c.dim('# Install globally for all projects')}
  npx github:asquilatan/notes-skills --global
`);
}

function findGitRoot(startDir = process.cwd()) {
  let current = path.resolve(startDir);
  while (true) {
    if (existsSync(path.join(current, '.git'))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return null;
}

async function discoverLocalSkills() {
  try {
    const entries = await fs.readdir(packageRoot, { withFileTypes: true });
    const skills = entries
      .filter((e) => e.isDirectory() && e.name.startsWith('notes-'))
      .map((e) => e.name);

    skills.sort((a, b) => {
      if (a === 'notes-start') return -1;
      if (b === 'notes-start') return 1;
      return a.localeCompare(b);
    });

    return skills;
  } catch {
    return [];
  }
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    printUsage();
    process.exit(0);
  }

  printBanner();

  const isForce = args.includes('--force');
  const isAutoYes = args.includes('--all') || args.includes('-y') || args.includes('--yes');
  const isRepoFlag = args.includes('--repo') || args.includes('--local');
  const isGlobalFlag = args.includes('--global') || args.includes('-g');
  const isAgentsGlobalFlag = args.includes('--agents-global');

  let destArg = null;
  const destIndex = args.indexOf('--dest');
  if (destIndex !== -1 && args[destIndex + 1]) {
    destArg = path.resolve(args[destIndex + 1]);
  }

  const gitRoot = findGitRoot();
  const repoDefaultPath = gitRoot
    ? path.join(gitRoot, '.agent', 'skills')
    : path.join(process.cwd(), '.agent', 'skills');

  const geminiGlobalPath = path.join(os.homedir(), '.gemini', 'config', 'skills');
  const agentsGlobalPath = path.join(os.homedir(), '.agents', 'skills');

  let targetDir = destArg;
  if (!targetDir) {
    if (isRepoFlag) {
      targetDir = repoDefaultPath;
    } else if (isGlobalFlag) {
      targetDir = geminiGlobalPath;
    } else if (isAgentsGlobalFlag) {
      targetDir = agentsGlobalPath;
    }
  }

  const availableSkills = await discoverLocalSkills();
  if (availableSkills.length === 0) {
    console.error(c.red('❌ Error: Could not locate notes-* skills in package.'));
    process.exit(1);
  }

  let rl;
  const getRl = () => {
    if (!rl) {
      rl = readline.createInterface({ input, output });
    }
    return rl;
  };

  try {
    if (!targetDir) {
      console.log(`${c.bold('Where would you like to install the notes-* skills?')}`);
      console.log(`  ${c.cyan('[1]')} Current repository ${c.dim('(.agent/skills)')}`);
      console.log(`      ${c.dim('Target:')} ${c.yellow(repoDefaultPath)}`);
      console.log(`  ${c.cyan('[2]')} Global Gemini / Antigravity config ${c.dim('(~/.gemini/config/skills)')}`);
      console.log(`      ${c.dim('Target:')} ${c.yellow(geminiGlobalPath)}`);
      console.log(`  ${c.cyan('[3]')} Global Agent skills ${c.dim('(~/.agents/skills)')}`);
      console.log(`      ${c.dim('Target:')} ${c.yellow(agentsGlobalPath)}`);
      console.log(`  ${c.cyan('[4]')} Custom path`);

      const choice = (await getRl().question(`\n${c.bold('Enter choice [1-4]')} ${c.dim('(default: 1)')}: `)).trim() || '1';

      if (choice === '1') {
        targetDir = repoDefaultPath;
      } else if (choice === '2') {
        targetDir = geminiGlobalPath;
      } else if (choice === '3') {
        targetDir = agentsGlobalPath;
      } else if (choice === '4') {
        const custom = (await getRl().question(`${c.bold('Enter destination directory:')} `)).trim();
        if (!custom) {
          console.log(c.yellow('Defaulting to repository path.'));
          targetDir = repoDefaultPath;
        } else {
          targetDir = path.resolve(custom);
        }
      } else {
        console.log(c.yellow('Invalid choice, defaulting to repository path.'));
        targetDir = repoDefaultPath;
      }
      console.log('');
    }

    let selectedSkills = availableSkills;
    if (!isAutoYes) {
      console.log(`${c.bold('Which skills would you like to install?')}`);
      console.log(`  ${c.cyan('[1]')} All ${availableSkills.length} skills ${c.green('(Recommended)')}`);
      console.log(`  ${c.cyan('[2]')} Choose individual skills`);

      const skillChoice = (await getRl().question(`\n${c.bold('Enter choice [1-2]')} ${c.dim('(default: 1)')}: `)).trim() || '1';

      if (skillChoice === '2') {
        console.log(`\n${c.bold('Available skills:')}`);
        availableSkills.forEach((name, idx) => {
          const desc = SKILL_DESCRIPTIONS[name] || '';
          console.log(`  ${c.cyan(`[${idx + 1}]`)} ${c.bold(name)}: ${c.dim(desc)}`);
        });

        const selectedInput = (await getRl().question(`\n${c.bold('Enter numbers to install (comma-separated, e.g. 1,2,3):')} `)).trim();
        if (selectedInput) {
          const indices = selectedInput
            .split(/[, ]+/)
            .map((s) => Number.parseInt(s.trim(), 10) - 1)
            .filter((i) => !Number.isNaN(i) && i >= 0 && i < availableSkills.length);

          if (indices.length > 0) {
            selectedSkills = [...new Set(indices)].map((i) => availableSkills[i]);
          } else {
            console.log(c.yellow('No valid numbers entered. Defaulting to all skills.'));
          }
        }
      }
      console.log('');
    }

    // Check existing
    const existing = selectedSkills.filter((s) => existsSync(path.join(targetDir, s)));
    if (existing.length > 0 && !isForce) {
      console.log(c.yellow(`⚠️  The following skill(s) already exist in ${targetDir}:`));
      existing.forEach((s) => console.log(`   - ${s}`));
      const overwriteAns = (await getRl().question(`\n${c.bold('Overwrite existing skills? [y/N]:')} `)).trim().toLowerCase();
      if (overwriteAns !== 'y' && overwriteAns !== 'yes') {
        console.log(c.dim('Installation aborted. No files were changed.'));
        process.exit(0);
      }
      console.log('');
    }

    if (rl) {
      rl.close();
      rl = null;
    }

    console.log(`${c.bold('📦 Installing skills to:')} ${c.yellow(targetDir)}\n`);

    await fs.mkdir(targetDir, { recursive: true });

    for (const skill of selectedSkills) {
      const src = path.join(packageRoot, skill);
      const dest = path.join(targetDir, skill);
      await fs.cp(src, dest, { recursive: true, force: true });
      const desc = SKILL_DESCRIPTIONS[skill] ? ` ${c.dim(`(${SKILL_DESCRIPTIONS[skill]})`)}` : '';
      console.log(`  ${c.green('✔')} ${c.bold(skill)}${desc}`);
    }

    console.log(`\n${c.green(c.bold('✨ Successfully installed ' + selectedSkills.length + ' skills!'))}\n`);
    console.log(`${c.bold('🚀 How to start learning:')}`);
    console.log(`  1. In your agent chat or terminal session, type:`);
    console.log(`     ${c.cyan('Teach me [Topic]')}`);
    console.log(`     ${c.dim('or')}`);
    console.log(`     ${c.cyan('/learn [Topic]')}`);
    console.log(`  2. The master orchestrator (${c.bold('notes-start')}) will guide your customized curriculum!`);
    console.log('');
  } catch (err) {
    if (rl) rl.close();
    if (err.name === 'AbortError') {
      console.log('\n' + c.dim('Aborted.'));
      process.exit(0);
    }
    console.error(c.red(`\n❌ Error: ${err.message}`));
    process.exit(1);
  }
}

main();
