// Fail if a production dependency has a license incompatible with Argus' AGPL-3.0-or-later.
// Reads `pnpm licenses list --prod --json`. Permissive licenses, LGPL, GPL-3.0 and AGPL-3.0
// are compatible (GPLv3 and AGPLv3 section 13), and so is GPL-2.0 "or later". Incompatible:
// GPL-2.0-only, a GPL without a version (check it by hand and add it to ALLOW) and SSPL.
// Alternatives ("MIT OR GPL-2.0") pass if one of them does; same rule as
// backend/scripts/check_licenses.py.
import { execFileSync } from 'node:child_process'

const SSPL = /SSPL|Server Side Public/i
const LESSER = /LGPL|Lesser General Public|Library General Public/i
// Whole tokens only, so "LGPL" doesn't count as "GPL".
const GPL = /(?<![A-Za-z])A?GPL|General Public License/i
const V3_OR_LATER = /v3|(?<![\d.])3(\.0)?(?![\d.])|or[- ]later|\+/i
// Packages whose metadata is wrong or ambiguous, after checking them by hand:
// { 'package-name': 'reason' }
const ALLOW = {}

const strip = (s) => s.replace(/^[()\s]+|[()\s]+$/g, '')
const compatiblePart = (license) => {
  if (SSPL.test(license)) return false
  if (LESSER.test(license) || !GPL.test(license)) return true
  return V3_OR_LATER.test(license)
}
const compatible = (license) =>
  strip(license)
    .split(/\s+OR\s+|;\s*/i)
    .some((alternative) =>
      strip(alternative)
        .split(/\s+AND\s+/i)
        .every(compatiblePart),
    )

const byLicense = JSON.parse(
  // On Windows pnpm is a .cmd script, which Node starts only through a shell (fixed arguments).
  execFileSync('pnpm', ['licenses', 'list', '--prod', '--json'], {
    encoding: 'utf8',
    shell: process.platform === 'win32',
  }),
)
const bad = []
for (const [license, packages] of Object.entries(byLicense)) {
  if (compatible(license)) continue
  for (const pkg of packages) {
    if (!(pkg.name in ALLOW)) bad.push(`${pkg.name} ${pkg.versions?.join(', ') ?? ''}: ${license}`)
  }
}
for (const line of bad) console.log(`incompatible license: ${line}`)
if (!bad.length) console.log('licenses ok')
process.exit(bad.length ? 1 : 0)
