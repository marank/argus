# CI und Releases

`.github/workflows/build.yaml` läuft bei jedem Push auf `main`, bei Versions-Tags
(`v1.2.3`) und bei Pull Requests, auch aus Forks. Die Jobs `backend`, `frontend`, `docs`,
`workflows` und `repository` laufen parallel (die ersten vier führen die Rezepte
`just check-…` aus, dasselbe wie `just check`; `repository` führt Trivy auf dem Repository
aus); anschließend baut `image` das Image, startet es gegen eine
Wegwerf-PostgreSQL, scannt es und überträgt es, außer bei Pull Requests, nach
`ghcr.io/marank/argus` (`latest`, `sha-…` und bei Tags `1.2.3`/`1.2`/`1`). Für den Push
wird das `GITHUB_TOKEN` des Workflows verwendet; Secrets sind nicht nötig.

Jeden Montag läuft der Workflow zusätzlich auf `main`, auch ohne Änderung. Jeder Build
installiert die Systempakete des Images neu (`--no-cache-filter runtime`), daher
veröffentlicht der wöchentliche Lauf `latest` mit Debians Sicherheitsupdates, und
ein Scan, der eine neue kritische Lücke findet, färbt ihn rot. Images von Versions-Tags
werden nicht neu gebaut; dort braucht eine Korrektur ein neues Release. Der wöchentliche
Lauf hat zusätzlich den Job `eol` (`just check-eol`): Er wird 180 Tage bevor Python,
Debian, Node.js, PostgreSQL oder Django keine Sicherheitsupdates mehr bekommen rot, damit
Hauptversions-Upgrades, die Dependabot auslässt (PostgreSQL), rechtzeitig auffallen.
`image` hängt nicht von ihm ab.

## Releases

Releases kommen von release-please (`.github/workflows/release.yaml`). Aus den
Commit-Nachrichten auf `main` hält es einen Pull Request „chore(main): release X.Y.Z“ mit
der nächsten Version und `CHANGELOG.md` aktuell. Wird er gemergt, setzt es den Tag
`vX.Y.Z`, legt das GitHub-Release an und baut das Image mit den Versions-Tags.

Die Commit-Nachrichten bestimmen die Version, daher sind sie
[Conventional Commits](https://www.conventionalcommits.org/): `feat:` ergibt ein
Minor-Release, `fix:` ein Patch-Release, `feat!:` oder eine Fußzeile `BREAKING CHANGE:` ein
Major-Release (vor 1.0 ein Minor-Release). `docs:`, `refactor:`, `test:`, `build:`, `ci:`
und `chore:` ergeben kein Release und stehen nicht im Changelog. Dependabot schreibt
`fix(deps):` für alles, was im Image oder bei Betreibern landet, und `chore(deps):` für
Entwicklungswerkzeuge und CI.

::: info Gut zu wissen
Pull Requests werden mit *Squash and merge* übernommen: Der Titel des Pull Requests wird
zum Commit auf `main` und muss daher ein Conventional Commit sein.
:::

## Repository-Einstellungen auf GitHub

1. **`main` schützen** (*Settings → Branches* oder *Rules*): Änderungen nur per Pull
   Request, mit den Status-Checks `backend`, `frontend`, `docs`, `workflows`, `repository`
   und `image` als Pflicht.
2. **Dependabot** (*Settings → Advanced Security*): Abhängigkeitsgraph, Dependabot-Warnungen
   und Sicherheitsupdates einschalten. Wöchentliche Versionsupdates kommen aus
   `.github/dependabot.yml`, jedes Release erst, wenn es eine Woche alt ist. Nicht
   abgedeckt: `SUPERVISOR_VERSION` im Dockerfile; in `build.yaml` die Job-Container,
   `TRIVY_IMAGE`, `POSTGRES_IMAGE` (gleiche Hauptversion wie `compose.yml`) und `JUST_VERSION`;
   `actionlint` und `zizmor` im `justfile`; die pre-commit-Hooks (`pre-commit autoupdate`).
3. **Releases** (*Settings → Actions → General*): *Allow GitHub Actions to create and
   approve pull requests* einschalten, sonst kann release-please seinen Pull Request nicht
   öffnen. Unter *Settings → General → Pull Requests* nur *Squash merging* erlauben, mit
   dem Titel des Pull Requests als Standard-Commit-Nachricht.
4. **Sichtbarkeit des Pakets**: Das Paket `argus` auf ghcr.io ist öffentlich, sodass das
   Image ohne Anmeldung geladen werden kann.

Actions sind auf den Commit-SHA eines Releases festgelegt
(`actions/checkout@<sha> # v7.0.1`), Images im Dockerfile und in den Workflows auf Tag und Digest, sodass ein
verschobener Tag nicht ändern kann, was läuft. `compose.yml` und `compose.dev.yml` nennen
Images nur mit Tag, wie Betreiber es erwarten. Workflows vergeben standardmäßig keine Berechtigungen; jeder
Job fordert an, was er braucht.

Ein privater Spiegel auf Gitea oder anderswo ist ein Pull-Spiegel des GitHub-Repositorys;
er führt keine eigene CI aus.
