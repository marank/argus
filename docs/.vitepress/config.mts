import { createHash } from 'node:crypto'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { defineConfig } from 'vitepress'

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

// Served by the app container under /docs/ (see docker/nginx.conf).
export default defineConfig({
  lang: 'de-DE',
  title: 'Argus',
  description: 'Dokumentation zu Argus, der IT-Asset-Verwaltung',
  base,
  cleanUrls: true,
  // Page metadata as a separate script instead of inline: the CSP allows no inline scripts.
  metaChunk: true,
  transformHtml: (html, _id, { siteConfig }) => externalizeInlineScripts(html, siteConfig.outDir),
  srcExclude: ['README.md', 'review-decisions.md'],
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
  // Three areas as VitePress locales: each has its own navigation and its own search
  // index, so a link into the employee or approver area shows nothing of the IT area.
  // The empty labels hide the locale switcher.
  locales: {
    root: { label: '', lang: 'de-DE', themeConfig: { sidebar: [] } },
    employees: {
      label: '',
      lang: 'de-DE',
      link: '/employees/',
      title: 'Argus für Mitarbeitende',
      themeConfig: {
        nav: [{ text: 'FAQ', link: '/employees/faq' }],
        sidebar: [
          {
            text: 'Für Mitarbeitende',
            items: [
              { text: 'Übersicht', link: '/employees/' },
              { text: 'Erste Schritte', link: '/employees/getting-started' },
              { text: 'Anfordern', link: '/employees/request' },
              { text: 'Meine Anforderungen, Geräte und Software', link: '/employees/overview' },
              { text: 'Abholen und zurückgeben', link: '/employees/pickup' },
              { text: 'Probleme melden', link: '/employees/report-issue' },
              { text: 'Konto und Einstellungen', link: '/employees/account' },
              { text: 'FAQ', link: '/employees/faq' },
            ],
          },
        ],
      },
    },
    approvers: {
      label: '',
      lang: 'de-DE',
      link: '/approvers/',
      title: 'Argus für Genehmiger',
      themeConfig: {
        nav: [{ text: 'Für Mitarbeitende', link: '/employees/' }],
        sidebar: [
          {
            text: 'Für Genehmiger',
            items: [
              { text: 'Übersicht', link: '/approvers/' },
              { text: 'Genehmigen oder ablehnen', link: '/approvers/approvals' },
              { text: 'Vertretung bei Abwesenheit', link: '/approvers/delegation' },
            ],
          },
        ],
      },
    },
    it: {
      label: '',
      lang: 'de-DE',
      link: '/it/',
      title: 'Argus für die IT',
      themeConfig: {
        nav: [
          { text: 'Erste Schritte', link: '/it/getting-started' },
          { text: 'Administration', link: '/it/administration/getting-started' },
          { text: 'Betrieb', link: '/it/operations/installation' },
          { text: 'Mitarbeitende', link: '/employees/' },
          { text: 'FAQ', link: '/it/faq' },
        ],
        sidebar: [
          {
            text: 'Einführung',
            items: [
              { text: 'Was ist Argus?', link: '/it/introduction' },
              { text: 'Begriffe', link: '/it/glossary' },
              { text: 'Abläufe im Überblick', link: '/it/workflows' },
              { text: 'Erste Schritte', link: '/it/getting-started' },
            ],
          },
          {
            text: 'IT-Arbeitsplatz',
            items: [
              { text: 'Dashboard und Kalender', link: '/it/dashboard-calendar' },
              { text: 'Anforderungen bearbeiten', link: '/it/requests' },
              { text: 'Abholterminal', link: '/it/terminal' },
              { text: 'Geräte', link: '/it/devices' },
              { text: 'Geräte importieren', link: '/it/device-import' },
              { text: 'Verbrauchsmaterial', link: '/it/consumables' },
              { text: 'Lizenzen', link: '/it/licenses' },
              { text: 'Meldungen', link: '/it/issues' },
              { text: 'Beschaffung', link: '/it/procurement' },
              { text: 'Scannen', link: '/it/scanning' },
            ],
          },
          {
            text: 'Administration',
            items: [
              { text: 'Checkliste für den Start', link: '/it/administration/getting-started' },
              { text: 'Stammdaten', link: '/it/administration/master-data' },
              { text: 'Rollen und Rechte', link: '/it/administration/roles' },
              { text: 'Einstellungen', link: '/it/administration/settings' },
              { text: 'E-Mail und Benachrichtigungen', link: '/it/administration/email' },
              { text: 'LDAP-Anmeldung', link: '/it/administration/ldap' },
              { text: 'Anmeldung und Sicherheit', link: '/it/administration/sign-in' },
            ],
          },
          {
            text: 'Betrieb',
            items: [
              { text: 'Installation', link: '/it/operations/installation' },
              { text: 'Konfiguration', link: '/it/operations/configuration' },
              { text: 'Backups', link: '/it/operations/backups' },
              { text: 'Updates und Fehlersuche', link: '/it/operations/maintenance' },
              { text: 'Sicherheit', link: '/it/operations/security' },
            ],
          },
          // The open areas, so IT can find and link them; they open with their own navigation.
          {
            text: 'Für Mitarbeitende',
            collapsed: true,
            items: [
              { text: 'Übersicht', link: '/employees/' },
              { text: 'Erste Schritte', link: '/employees/getting-started' },
              { text: 'Anfordern', link: '/employees/request' },
              { text: 'Meine Anforderungen, Geräte und Software', link: '/employees/overview' },
              { text: 'Abholen und zurückgeben', link: '/employees/pickup' },
              { text: 'Probleme melden', link: '/employees/report-issue' },
              { text: 'Konto und Einstellungen', link: '/employees/account' },
              { text: 'FAQ', link: '/employees/faq' },
            ],
          },
          {
            text: 'Für Genehmiger',
            collapsed: true,
            items: [
              { text: 'Übersicht', link: '/approvers/' },
              { text: 'Genehmigen oder ablehnen', link: '/approvers/approvals' },
              { text: 'Vertretung bei Abwesenheit', link: '/approvers/delegation' },
            ],
          },
          {
            text: 'Hilfe',
            items: [
              { text: 'FAQ', link: '/it/faq' },
              { text: 'Statusübersicht', link: '/it/status' },
            ],
          },
        ],
      },
    },
  },
  themeConfig: {
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Suchen', buttonAriaLabel: 'Suchen' },
          modal: {
            noResultsText: 'Keine Treffer für',
            resetButtonTitle: 'Suche zurücksetzen',
            displayDetails: 'Details anzeigen',
            backButtonTitle: 'Zurück',
            footer: { selectText: 'Auswählen', navigateText: 'Navigieren', closeText: 'Schließen' },
          },
        },
      },
    },
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
