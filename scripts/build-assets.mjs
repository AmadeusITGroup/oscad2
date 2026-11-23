#!/usr/bin/env node
// Build the packaged frontend assets for OSCAd.
//
// * Compiles `bootstrap.scss`, `main.scss` and `theme.scss` from
//   `oscad/assets/scss/` into `oscad/static/css/`.
// * For every bundled theme, compiles the same entry points with the theme's
//   `assets/scss/` directory first on the load path, and writes the result to
//   `<theme>/static/css/` only when it differs from the base output (the
//   theme's `static/` directory overrides `oscad:static/` at runtime).
// * Copies Bootstrap's JavaScript bundle and the Bootstrap / Bootstrap Icons
//   licenses into the repository.
//
// Usage: `npm run build` to write files, `npm run check` to fail if the
// committed files are out of date.

import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as sass from 'sass';

const require = createRequire(import.meta.url);
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const nodeModules = join(root, 'node_modules');
const bootstrapDist = dirname(dirname(require.resolve('bootstrap/dist/js/bootstrap.bundle.min.js')));
const check = process.argv.includes('--check');

const BASE = 'oscad';
const THEMES = ['oscad_theme_basic', 'oscad_theme_amadeus'];
const ENTRIES = ['bootstrap', 'main', 'theme'];

const outdated = [];

function emit(target, content) {
  const rel = relative(root, target);
  const current = existsSync(target) ? readFileSync(target) : null;
  const next = Buffer.from(content);
  if (current && current.equals(next)) {
    return;
  }
  if (check) {
    outdated.push(rel);
    return;
  }
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, next);
  console.log(`wrote ${rel}`);
}

function remove(target) {
  if (!existsSync(target)) {
    return;
  }
  if (check) {
    outdated.push(`${relative(root, target)} (stale)`);
    return;
  }
  rmSync(target);
  console.log(`removed ${relative(root, target)}`);
}

function compile(entry, scssDirs) {
  const file = scssDirs.map((d) => join(d, `${entry}.scss`)).find(existsSync);
  const { css } = sass.compile(file, {
    // `defaults/` comes after the theme directories so a theme's
    // `_variables.scss` shadows the base one.
    loadPaths: [...scssDirs, join(baseScss, 'defaults'), nodeModules],
    style: 'compressed',
    quietDeps: true,
    // Bootstrap 5.3 is still written with `@import`; theme variable
    // overrides depend on it, so silence the related deprecations.
    silenceDeprecations: ['import', 'global-builtin', 'color-functions', 'if-function'],
  });
  return css + '\n';
}

const baseScss = join(root, BASE, 'assets', 'scss');
const baseCss = {};
for (const entry of ENTRIES) {
  baseCss[entry] = compile(entry, [baseScss]);
  emit(join(root, BASE, 'static', 'css', `${entry}.css`), baseCss[entry]);
}

for (const theme of THEMES) {
  const themeScss = join(root, theme, 'assets', 'scss');
  for (const entry of ENTRIES) {
    const css = compile(entry, [themeScss, baseScss]);
    const target = join(root, theme, 'static', 'css', `${entry}.css`);
    if (css === baseCss[entry]) {
      remove(target);
    } else {
      emit(target, css);
    }
  }
}

const bootstrapStatic = join(root, BASE, 'static', 'bootstrap', 'js');
for (const name of ['bootstrap.bundle.min.js', 'bootstrap.bundle.min.js.map']) {
  emit(join(bootstrapStatic, name), readFileSync(join(bootstrapDist, 'js', name)));
}
emit(join(root, 'LICENSE_BOOTSTRAP'), readFileSync(join(dirname(bootstrapDist), 'LICENSE')));
// The question-circle icon is inlined in oscad/templates/oscad/icons.jinja2.
emit(join(root, 'LICENSE_BOOTSTRAP_ICONS'),
  readFileSync(join(dirname(require.resolve('bootstrap-icons/package.json')), 'LICENSE')));

if (outdated.length) {
  console.error('Generated assets are out of date. Run `npm run build`:');
  for (const f of outdated) {
    console.error(`  ${f}`);
  }
  process.exit(1);
}
