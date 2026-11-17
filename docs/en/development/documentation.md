# Writing documentation

This documentation lives in `docs/` (VitePress). The image serves it at `/docs/`; the
app's user menu links to it as *Help*, in the interface's language (IT staff to
`/docs/<lang>/it/`, everyone else to `/docs/<lang>/employees/`).

## Languages and areas

Every page exists in German and English, under the same path in `de/` and `en/`. The
switch in the top bar leads to the same page in the other language. A change goes into
both versions in the same commit; the build fails when a page lacks its counterpart.

Each language has four areas, each with its own navigation and search (VitePress locales
in `docs/.vitepress/config.mts`):

| Folder | For |
| --- | --- |
| `employees/`, `approvers/` | everyone; may be linked publicly |
| `it/` | daily IT work, administration and operations |
| `development/` | contributors |

Pages in `employees/` and `approvers/` never link into `it/`; the build fails otherwise.
File and folder names are English. A new page is added to `SIDEBARS` in the config with
its German and English title.

Use the exact interface labels from `frontend/src/i18n/locales/de` and `.../en`. Old
links without a language folder (`/docs/it/…`) are redirected to the German pages by
nginx.

## Run and build

```bash
cd docs
pnpm install
pnpm dev --port 5175      # http://localhost:5175/docs/; the frontend dev server proxies /docs there
```

```bash
pnpm build                # also fails on dead links, missing anchors, IT links in the open areas and missing translations
```

VS Code tasks: **Dev: docs**, **Check: docs**.

Update the user documentation whenever users or operators notice a change.
