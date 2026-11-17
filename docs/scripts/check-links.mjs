// Checks the built docs beyond VitePress' own dead-link check:
// - every link with #anchor points to an id that exists on the target page;
// - pages of the employee and approver areas never link into the IT area, so those
//   areas can be shared with everyone;
// - every page exists in both languages (de/ and en/ under the same path).
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { join, posix, relative, sep } from 'node:path'

const root = process.argv[2]
const dist = join(root, '.vitepress', 'dist')
const LANGS = ['de', 'en']
const PUBLIC_AREAS = LANGS.flatMap((lang) => [`${lang}/employees/`, `${lang}/approvers/`])
const IT_AREAS = LANGS.map((lang) => `${lang}/it/`)
const files = []
const walk = (dir) => {
  for (const name of readdirSync(dir)) {
    if (name === 'node_modules' || name.startsWith('.')) continue
    const p = join(dir, name)
    if (statSync(p).isDirectory()) walk(p)
    else if (name.endsWith('.md')) files.push(p)
  }
}
walk(root)

const problems = []
for (const file of files) {
  const rel = relative(root, file).split(sep).join('/')
  if (rel === 'review-decisions.md') continue
  const text = readFileSync(file, 'utf8')
  for (const m of text.matchAll(/\]\(([^)\s]+)\)/g)) {
    const href = m[1]
    if (/^(https?:|mailto:)/.test(href)) continue
    const [path, anchor] = href.split('#')
    let target = path
      ? path.startsWith('/')
        ? path.slice(1)
        : posix.normalize(posix.join(posix.dirname(rel), path))
      : rel
    target = target.replace(/\.md$/, '')
    if (PUBLIC_AREAS.some((area) => rel.startsWith(area)) && IT_AREAS.some((area) => target.startsWith(area))) {
      problems.push(`${rel}: ${href} leads into the IT area`)
    }
    if (!anchor) continue
    const candidates = [join(dist, target + '.html'), join(dist, target, 'index.html')]
    const html = candidates.find((c) => existsSync(c))
    if (!html || !readFileSync(html, 'utf8').includes(`id="${anchor}"`)) {
      problems.push(`${rel}: ${href} has no such anchor`)
    }
  }
}
// Every page in one language has its counterpart in the other.
const pages = new Set(files.map((file) => relative(root, file).split(sep).join('/')))
for (const page of pages) {
  const [lang, ...rest] = page.split('/')
  if (!LANGS.includes(lang)) continue
  for (const other of LANGS) {
    const counterpart = [other, ...rest].join('/')
    if (!pages.has(counterpart)) problems.push(`${page}: no ${other}/ version (${counterpart})`)
  }
}

for (const problem of problems) console.log(problem)
console.log(problems.length ? `${problems.length} problems` : 'links ok')
process.exit(problems.length ? 1 : 0)
