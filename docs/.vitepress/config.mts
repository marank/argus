import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { defineConfig, type DefaultTheme, type LocaleConfig } from 'vitepress'

const base = '/docs/'

// The CSP allows scripts from our own origin only. VitePress inlines two small scripts
// (dark mode, macOS shortcut labels); they move into files that load just as early.
function externalizeInlineScripts(html: string, outDir: string): string {
  return html.replace(/<script( id="[^"]*")?>([\s\S]*?)<\/script>/g, (_, id: string | undefined, code: string) => {
    const name = `inline.${createHash('sha256').update(code).digest('hex').slice(0, 12)}.js`
    mkdirSync(join(outDir, 'assets'), { recursive: true })
    writeFileSync(join(outDir, 'assets', name), code)
    return `<script${id ?? ''} src="${base}assets/${name}"></script>`
  })
}

type Lang = 'de' | 'en'
const LANGS: Lang[] = ['de', 'en']
/** German and English text of one label. */
type Text = Record<Lang, string>
/** A page: its path inside the area ('' for the area's index) and its title. */
type Page = [path: string, title: Text]
type Group = { text: Text; pages: Page[]; collapsed?: boolean; area?: Area }
type Area = 'employees' | 'approvers' | 'it' | 'development'

// Every page exists in de/ and en/ under the same path; only the titles differ.
const EMPLOYEES: Page[] = [
  ['', { de: 'Übersicht', en: 'Overview' }],
  ['getting-started', { de: 'Erste Schritte', en: 'Getting started' }],
  ['request', { de: 'Anfordern', en: 'Requesting' }],
  ['overview', { de: 'Meine Anforderungen, Geräte und Software', en: 'My requests, devices and software' }],
  ['pickup', { de: 'Abholen und zurückgeben', en: 'Pickup and return' }],
  ['report-issue', { de: 'Probleme melden', en: 'Reporting a problem' }],
  ['account', { de: 'Konto und Einstellungen', en: 'Account and settings' }],
  ['faq', { de: 'FAQ', en: 'FAQ' }],
]
const APPROVERS: Page[] = [
  ['', { de: 'Übersicht', en: 'Overview' }],
  ['approvals', { de: 'Genehmigen oder ablehnen', en: 'Approving or rejecting' }],
  ['delegation', { de: 'Vertretung bei Abwesenheit', en: 'Delegation while away' }],
]
const FOR_EMPLOYEES: Text = { de: 'Für Mitarbeitende', en: 'For employees' }
const FOR_APPROVERS: Text = { de: 'Für Genehmiger', en: 'For approvers' }
const GETTING_STARTED: Text = { de: 'Erste Schritte', en: 'Getting started' }

const SIDEBARS: Record<Area, Group[]> = {
  employees: [{ text: FOR_EMPLOYEES, pages: EMPLOYEES }],
  approvers: [{ text: FOR_APPROVERS, pages: APPROVERS }],
  it: [
    {
      text: { de: 'Einführung', en: 'Introduction' },
      pages: [
        ['introduction', { de: 'Was ist Argus?', en: 'What is Argus?' }],
        ['glossary', { de: 'Begriffe', en: 'Terms' }],
        ['workflows', { de: 'Abläufe im Überblick', en: 'Workflows at a glance' }],
        ['getting-started', GETTING_STARTED],
      ],
    },
    {
      text: { de: 'IT-Arbeitsplatz', en: 'IT workspace' },
      pages: [
        ['dashboard-calendar', { de: 'Dashboard und Kalender', en: 'Dashboard and calendar' }],
        ['activities', { de: 'Aktivitäten', en: 'Activities' }],
        ['requests', { de: 'Anforderungen bearbeiten', en: 'Handling requests' }],
        ['terminal', { de: 'Abholterminal', en: 'Pickup terminal' }],
        ['devices', { de: 'Geräte', en: 'Devices' }],
        ['device-import', { de: 'Geräte importieren', en: 'Importing devices' }],
        ['consumables', { de: 'Verbrauchsmaterial', en: 'Consumables' }],
        ['licenses', { de: 'Lizenzen', en: 'Licenses' }],
        ['issues', { de: 'Meldungen', en: 'Problem reports' }],
        ['procurement', { de: 'Beschaffung', en: 'Procurement' }],
        ['scanning', { de: 'Scannen', en: 'Scanning' }],
      ],
    },
    {
      text: { de: 'Administration', en: 'Administration' },
      pages: [
        ['administration/getting-started', { de: 'Checkliste für den Start', en: 'Launch checklist' }],
        ['administration/master-data', { de: 'Stammdaten', en: 'Master data' }],
        ['administration/roles', { de: 'Rollen und Rechte', en: 'Roles and permissions' }],
        ['administration/settings', { de: 'Einstellungen', en: 'Settings' }],
        ['administration/email', { de: 'E-Mail und Benachrichtigungen', en: 'Email and notifications' }],
        ['administration/ldap', { de: 'LDAP-Anmeldung', en: 'LDAP sign-in' }],
        ['administration/sign-in', { de: 'Anmeldung und Sicherheit', en: 'Sign-in and security' }],
      ],
    },
    {
      text: { de: 'Betrieb', en: 'Operations' },
      pages: [
        ['operations/installation', { de: 'Installation', en: 'Installation' }],
        ['operations/configuration', { de: 'Konfiguration', en: 'Configuration' }],
        ['operations/backups', { de: 'Backups', en: 'Backups' }],
        ['operations/maintenance', { de: 'Updates und Fehlersuche', en: 'Updates and troubleshooting' }],
        ['operations/security', { de: 'Sicherheit', en: 'Security' }],
      ],
    },
    // The open areas, so IT can find and link them; they open with their own navigation.
    { text: FOR_EMPLOYEES, pages: EMPLOYEES, collapsed: true, area: 'employees' },
    { text: FOR_APPROVERS, pages: APPROVERS, collapsed: true, area: 'approvers' },
    {
      text: { de: 'Hilfe', en: 'Help' },
      pages: [
        ['faq', { de: 'FAQ', en: 'FAQ' }],
        ['status', { de: 'Statusübersicht', en: 'Status overview' }],
      ],
    },
  ],
  development: [
    {
      text: { de: 'Entwicklung', en: 'Development' },
      pages: [
        ['', { de: 'Einrichtung', en: 'Setup' }],
        ['architecture', { de: 'Architektur', en: 'Architecture' }],
        ['checks', { de: 'Prüfungen und Tests', en: 'Checks and tests' }],
        ['api-and-translations', { de: 'API-Typen und Übersetzungen', en: 'API types and translations' }],
        ['documentation', { de: 'Dokumentation schreiben', en: 'Writing documentation' }],
        ['ci', { de: 'CI und Releases', en: 'CI and releases' }],
      ],
    },
  ],
}

const NAV: Record<Area, [path: string, text: Text][]> = {
  employees: [['employees/faq', { de: 'FAQ', en: 'FAQ' }]],
  approvers: [['employees/', FOR_EMPLOYEES]],
  it: [
    ['it/getting-started', GETTING_STARTED],
    ['it/administration/getting-started', { de: 'Administration', en: 'Administration' }],
    ['it/operations/installation', { de: 'Betrieb', en: 'Operations' }],
    ['employees/', { de: 'Mitarbeitende', en: 'Employees' }],
    ['it/faq', { de: 'FAQ', en: 'FAQ' }],
  ],
  development: [],
}

const TITLES: Record<Area, Text> = {
  employees: { de: 'Argus für Mitarbeitende', en: 'Argus for employees' },
  approvers: { de: 'Argus für Genehmiger', en: 'Argus for approvers' },
  it: { de: 'Argus für die IT', en: 'Argus for IT' },
  development: { de: 'Argus entwickeln', en: 'Developing Argus' },
}

const LABELS: Record<Lang, DefaultTheme.Config> = {
  de: {
    outline: { level: [2, 3], label: 'Auf dieser Seite' },
    docFooter: { prev: 'Zurück', next: 'Weiter' },
    darkModeSwitchLabel: 'Darstellung',
    lightModeSwitchTitle: 'Helle Darstellung',
    darkModeSwitchTitle: 'Dunkle Darstellung',
    sidebarMenuLabel: 'Menü',
    returnToTopLabel: 'Nach oben',
    langMenuLabel: 'Sprache',
    notFound: {
      title: 'Seite nicht gefunden',
      quote: 'Diese Seite gibt es nicht oder nicht mehr.',
      linkText: 'Zur Startseite',
    },
  },
  en: {
    outline: { level: [2, 3], label: 'On this page' },
    docFooter: { prev: 'Previous', next: 'Next' },
    darkModeSwitchLabel: 'Appearance',
    lightModeSwitchTitle: 'Switch to light theme',
    darkModeSwitchTitle: 'Switch to dark theme',
    sidebarMenuLabel: 'Menu',
    returnToTopLabel: 'Return to top',
    langMenuLabel: 'Language',
    notFound: {
      title: 'Page not found',
      quote: 'This page does not exist (any more).',
      linkText: 'Take me home',
    },
  },
}

const SEARCH: Record<Lang, DefaultTheme.LocalSearchOptions['translations']> = {
  de: {
    button: { buttonText: 'Suchen', buttonAriaLabel: 'Suchen' },
    modal: {
      noResultsText: 'Keine Treffer für',
      resetButtonTitle: 'Suche zurücksetzen',
      displayDetails: 'Details anzeigen',
      backButtonTitle: 'Zurück',
      footer: { selectText: 'Auswählen', navigateText: 'Navigieren', closeText: 'Schließen' },
    },
  },
  en: {},
}

const AREAS = Object.keys(SIDEBARS) as Area[]
const key = (lang: Lang, area: Area) => `${lang}/${area}`

function sidebar(lang: Lang, area: Area): DefaultTheme.SidebarItem[] {
  return SIDEBARS[area].map((group) => ({
    text: group.text[lang],
    collapsed: group.collapsed,
    items: group.pages.map(([path, title]) => ({
      text: title[lang],
      link: `/${lang}/${group.area ?? area}/${path}`,
    })),
  }))
}

// Each language × area is a VitePress locale: each has its own navigation and its own
// search index, so a link into the employee or approver area shows nothing of the IT
// area. The empty labels hide VitePress' own locale switcher, which would list every
// area; the theme's LanguageSwitch links to the same page in the other language.
const locales: LocaleConfig<DefaultTheme.Config> = {
  root: { label: '', lang: 'en-US', themeConfig: { sidebar: [] } },
}
for (const lang of LANGS) {
  for (const area of AREAS) {
    locales[key(lang, area)] = {
      label: '',
      lang: lang === 'de' ? 'de-DE' : 'en-US',
      link: `/${lang}/${area}/`,
      title: TITLES[area][lang],
      themeConfig: {
        ...LABELS[lang],
        nav: NAV[area].map(([path, text]) => ({ text: text[lang], link: `/${lang}/${path}` })),
        sidebar: sidebar(lang, area),
      },
    }
  }
}
// The language's start page (de/index.md, en/index.md). VitePress takes the first locale
// whose path matches, so these come after the areas they contain.
for (const lang of LANGS) {
  locales[lang] = {
    label: '',
    lang: lang === 'de' ? 'de-DE' : 'en-US',
    link: `/${lang}/`,
    themeConfig: { ...LABELS[lang], sidebar: [] },
  }
}

// Served by the app container under /docs/ (see docker/nginx.conf).
export default defineConfig({
  lang: 'en-US',
  title: 'Argus',
  description: 'Argus, IT asset management: documentation · Dokumentation',
  base,
  cleanUrls: true,
  // Page metadata as a separate script instead of inline: the CSP allows no inline scripts.
  metaChunk: true,
  transformHtml: (html, _id, { siteConfig }) => externalizeInlineScripts(html, siteConfig.outDir),
  srcExclude: ['README.md'],
  vite: {
    plugins: [
      {
        // The dev server only serves below /docs/; send http://localhost:5175/introduction
        // and the bare root there instead of showing VitePress' 404 page.
        name: 'argus-docs-base-redirect',
        configureServer(server) {
          server.middlewares.use((req, res, next) => {
            const url = req.url ?? '/'
            if (url.startsWith(base) || url === base.slice(0, -1)) return next()
            res.writeHead(302, { Location: base + url.replace(/^\//, '') })
            res.end()
          })
        },
      },
    ],
  },
  locales,
  themeConfig: {
    ...LABELS.en,
    search: {
      provider: 'local',
      options: {
        locales: Object.fromEntries(
          AREAS.map((area) => [key('de', area), { translations: SEARCH.de }]),
        ),
      },
    },
  },
  markdown: {
    container: {
      tipLabel: 'Tipp',
      warningLabel: 'Achtung',
      dangerLabel: 'Wichtig',
      infoLabel: 'Gut zu wissen',
      detailsLabel: 'Details',
    },
  },
})
