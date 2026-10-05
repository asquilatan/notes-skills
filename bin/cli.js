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
${c.bold('notes-skills CLI')}
${c.dim('Install, update, or remove notes & learning skills for your agent')}
`);
}

function printUsage() {
  printBanner();
  console.log(`${c.bold('Usage:')}
  npx github:asquilatan/notes-skills [options]

${c.bold('Options:')}
  ${c.green('--repo, --local')}         Target current project repository (.agents/skills)
  ${c.green('--global, -g')}            Target globally (~/.agents/skills)
  ${c.green('--dest <path>')}           Target a custom directory
  ${c.green('--update, -u')}            Update existing installed notes-* skills
  ${c.green('--remove, -r')}            Remove installed notes-* skills
  ${c.green('--all, -y, --yes')}        Apply to all skills without prompting
  ${c.green('--force')}                 Force overwrite without asking
  ${c.green('--help, -h')}              Show this help message

${c.bold('Examples:')}
  ${c.dim('# Interactive wizard (Install, Update, or Remove)')}
  npx github:asquilatan/notes-skills

  ${c.dim('# Install to current repo')}
  npx github:asquilatan/notes-skills --repo

  ${c.dim('# Update existing skills in current repo')}
  npx github:asquilatan/notes-skills --update --repo

  ${c.dim('# Update existing skills globally')}
  npx github:asquilatan/notes-skills --update --global

  ${c.dim('# Remove from current repo')}
  npx github:asquilatan/notes-skills --remove --repo

  ${c.dim('# Remove globally')}
  npx github:asquilatan/notes-skills --remove --global
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

async function findInstalledSkills(targetDir) {
  if (!existsSync(targetDir)) return [];
  try {
    const entries = await fs.readdir(targetDir, { withFileTypes: true });
    return entries
      .filter((e) => e.isDirectory() && e.name.startsWith('notes-'))
      .map((e) => e.name)
      .sort((a, b) => {
        if (a === 'notes-start') return -1;
        if (b === 'notes-start') return 1;
        return a.localeCompare(b);
      });
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
  let isRemove = args.includes('--remove') || args.includes('--uninstall') || args.includes('-r');
  let isUpdate = args.includes('--update') || args.includes('-u');

  let destArg = null;
  const destIndex = args.indexOf('--dest');
  if (destIndex !== -1 && args[destIndex + 1]) {
    destArg = path.resolve(args[destIndex + 1]);
  }

  const gitRoot = findGitRoot();
  const repoDefaultPath = gitRoot
    ? path.join(gitRoot, '.agents', 'skills')
    : path.join(process.cwd(), '.agents', 'skills');

  const globalPath = path.join(os.homedir(), '.agents', 'skills');

  let targetDir = destArg;
  if (!targetDir) {
    if (isRepoFlag) {
      targetDir = repoDefaultPath;
    } else if (isGlobalFlag) {
      targetDir = globalPath;
    }
  }

  let rl;
  const getRl = () => {
    if (!rl) {
      rl = readline.createInterface({ input, output });
    }
    return rl;
  };

  try {
    // If action not specified by flag and no quick flags, ask what to do
    const hasExplicitTargetFlag = isRepoFlag || isGlobalFlag || Boolean(destArg);
    const hasExplicitActionFlag = isRemove || isUpdate;
    if (!hasExplicitActionFlag && !hasExplicitTargetFlag) {
      console.log(`${c.bold('What would you like to do?')}`);
      console.log(`  ${c.cyan('[1]')} Install skills ${c.dim('(default)')}`);
      console.log(`  ${c.cyan('[2]')} Update existing skills ${c.dim('(overwrite installed skills with latest)')}`);
      console.log(`  ${c.cyan('[3]')} Remove skills`);

      const actionChoice = (await getRl().question(`\n${c.bold('Enter choice [1-3]')} ${c.dim('(default: 1)')}: `)).trim() || '1';
      if (actionChoice === '2') {
        isUpdate = true;
      } else if (actionChoice === '3') {
        isRemove = true;
      }
      console.log('');
    }

    // Select target directory if not set
    if (!targetDir) {
      let verb = 'install skills to';
      if (isRemove) verb = 'remove skills from';
      else if (isUpdate) verb = 'update skills in';
      console.log(`${c.bold(`Where would you like to ${verb}?`)}`);
      console.log(`  ${c.cyan('[1]')} Current repository ${c.dim('(.agents/skills)')}`);
      console.log(`      ${c.dim('Target:')} ${c.yellow(repoDefaultPath)}`);
      console.log(`  ${c.cyan('[2]')} Globally ${c.dim('(~/.agents/skills)')}`);
      console.log(`      ${c.dim('Target:')} ${c.yellow(globalPath)}`);
      console.log(`  ${c.cyan('[3]')} Custom path`);

      const choice = (await getRl().question(`\n${c.bold('Enter choice [1-3]')} ${c.dim('(default: 1)')}: `)).trim() || '1';

      if (choice === '1') {
        targetDir = repoDefaultPath;
      } else if (choice === '2') {
        targetDir = globalPath;
      } else if (choice === '3') {
        const custom = (await getRl().question(`${c.bold('Enter target directory:')} `)).trim();
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

    // ==========================================
    // REMOVE FLOW
    // ==========================================
    if (isRemove) {
      const installed = await findInstalledSkills(targetDir);

      if (installed.length === 0) {
        console.log(c.yellow(`ℹ️  No notes-* skills found in: ${targetDir}`));
        if (rl) rl.close();
        return;
      }

      console.log(`${c.bold('Found installed skills in')} ${c.yellow(targetDir)}:`);
      installed.forEach((s) => console.log(`  - ${s}`));
      console.log('');

      let skillsToRemove = installed;
      if (!isAutoYes) {
        console.log(`${c.bold('Which skills would you like to remove?')}`);
        console.log(`  ${c.cyan('[1]')} All ${installed.length} skills ${c.dim('(default)')}`);
        console.log(`  ${c.cyan('[2]')} Choose individual skills`);

        const removeChoice = (await getRl().question(`\n${c.bold('Enter choice [1-2]')} ${c.dim('(default: 1)')}: `)).trim() || '1';

        if (removeChoice === '2') {
          console.log(`\n${c.bold('Select skills to remove:')}`);
          installed.forEach((name, idx) => {
            console.log(`  ${c.cyan(`[${idx + 1}]`)} ${name}`);
          });

          const selectedInput = (await getRl().question(`\n${c.bold('Enter numbers to remove (comma-separated, e.g. 1,2):')} `)).trim();
          if (selectedInput) {
            const indices = selectedInput
              .split(/[, ]+/)
              .map((s) => Number.parseInt(s.trim(), 10) - 1)
              .filter((i) => !Number.isNaN(i) && i >= 0 && i < installed.length);

            if (indices.length > 0) {
              skillsToRemove = [...new Set(indices)].map((i) => installed[i]);
            }
          }
        }
        console.log('');

        if (!isForce) {
          const confirm = (await getRl().question(`${c.bold(`Are you sure you want to remove ${skillsToRemove.length} skill(s)? [y/N]:`)} `)).trim().toLowerCase();
          if (confirm !== 'y' && confirm !== 'yes') {
            console.log(c.dim('Removal cancelled. No files were deleted.'));
            if (rl) rl.close();
            return;
          }
          console.log('');
        }
      }

      if (rl) {
        rl.close();
        rl = null;
      }

      console.log(`${c.bold('🗑️  Removing skills from:')} ${c.yellow(targetDir)}\n`);
      for (const skill of skillsToRemove) {
        const skillDir = path.join(targetDir, skill);
        await fs.rm(skillDir, { recursive: true, force: true });
        console.log(`  ${c.green('✔')} Removed ${skill}`);
      }

      console.log(`\n${c.green(c.bold(`✨ Successfully removed ${skillsToRemove.length} skill(s)!`))}\n`);
      return;
    }

    // ==========================================
    // UPDATE FLOW
    // ==========================================
    if (isUpdate) {
      const installed = await findInstalledSkills(targetDir);

      if (installed.length === 0) {
        console.log(c.yellow(`ℹ️  No installed notes-* skills found in: ${targetDir}`));
        console.log(c.dim('Tip: Run install first to set up skills.'));
        if (rl) rl.close();
        return;
      }

      console.log(`${c.bold('Found installed skills in')} ${c.yellow(targetDir)}:`);
      installed.forEach((s) => {
        const desc = SKILL_DESCRIPTIONS[s] ? ` ${c.dim(`(${SKILL_DESCRIPTIONS[s]})`)}` : '';
        console.log(`  - ${c.bold(s)}${desc}`);
      });
      console.log('');

      let skillsToUpdate = installed;
      if (!isAutoYes) {
        console.log(`${c.bold('Which skills would you like to update?')}`);
        console.log(`  ${c.cyan('[1]')} All ${installed.length} installed skills ${c.green('(default)')}`);
        console.log(`  ${c.cyan('[2]')} Choose individual skills`);

        const updateChoice = (await getRl().question(`\n${c.bold('Enter choice [1-2]')} ${c.dim('(default: 1)')}: `)).trim() || '1';

        if (updateChoice === '2') {
          console.log(`\n${c.bold('Select skills to update:')}`);
          installed.forEach((name, idx) => {
            console.log(`  ${c.cyan(`[${idx + 1}]`)} ${name}`);
          });

          const selectedInput = (await getRl().question(`\n${c.bold('Enter numbers to update (comma-separated, e.g. 1,2):')} `)).trim();
          if (selectedInput) {
            const indices = selectedInput
              .split(/[, ]+/)
              .map((s) => Number.parseInt(s.trim(), 10) - 1)
              .filter((i) => !Number.isNaN(i) && i >= 0 && i < installed.length);

            if (indices.length > 0) {
              skillsToUpdate = [...new Set(indices)].map((i) => installed[i]);
            }
          }
        }
        console.log('');
      }

      if (rl) {
        rl.close();
        rl = null;
      }

      console.log(`${c.bold('🔄 Updating skills in:')} ${c.yellow(targetDir)}\n`);
      let updatedCount = 0;
      for (const skill of skillsToUpdate) {
        const src = path.join(packageRoot, skill);
        const dest = path.join(targetDir, skill);
        if (!existsSync(src)) {
          console.log(`  ${c.yellow('⚠')} ${skill} is no longer in this package, skipping.`);
          continue;
        }
        await fs.cp(src, dest, { recursive: true, force: true });
        const desc = SKILL_DESCRIPTIONS[skill] ? ` ${c.dim(`(${SKILL_DESCRIPTIONS[skill]})`)}` : '';
        console.log(`  ${c.green('✔')} Updated ${c.bold(skill)}${desc}`);
        updatedCount++;
      }

      console.log(`\n${c.green(c.bold(`✨ Successfully updated ${updatedCount} skill(s) to latest version!`))}\n`);
      return;
    }

    // ==========================================
    // INSTALL FLOW
    // ==========================================
    const availableSkills = await discoverLocalSkills();
    if (availableSkills.length === 0) {
      console.error(c.red('❌ Error: Could not locate notes-* skills in package.'));
      process.exit(1);
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
    console.log(`${c.bold('🚀 How to start:')}`);
    console.log(`  In your agent chat or terminal session, run:`);
    console.log(`    ${c.cyan('/notes-start [topic]')}`);
    console.log(`    ${c.dim('or')}`);
    console.log(`    ${c.cyan('Teach me [topic]')}`);
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
