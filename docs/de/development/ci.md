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
werden nicht neu gebaut; dort braucht eine Korrektur ein neues Release.

Ein Release ist ein Versions-Tag auf `main`:

```bash
git tag v1.2.3 && git push origin v1.2.3
```

## Repository-Einstellungen auf GitHub

1. **`main` schützen** (*Settings → Branches* oder *Rules*): Änderungen nur per Pull
   Request, mit den Status-Checks `backend`, `frontend`, `docs`, `workflows`, `repository`
   und `image` als Pflicht.
2. **Dependabot** (*Settings → Advanced Security*): Abhängigkeitsgraph, Dependabot-Warnungen
   und Sicherheitsupdates einschalten. Wöchentliche Versionsupdates kommen aus
   `.github/dependabot.yml`, jedes Release erst, wenn es eine Woche alt ist. Nicht
   abgedeckt: `SUPERVISOR_VERSION` im Dockerfile; in `build.yaml` die Job-Container,
   `TRIVY_IMAGE`, `POSTGRES_IMAGE` (zusammen mit `compose.yml`) und `JUST_VERSION`;
   `actionlint` und `zizmor` im `justfile`; die pre-commit-Hooks (`pre-commit autoupdate`).
3. **Sichtbarkeit des Pakets**: Das Paket `argus` auf ghcr.io ist öffentlich, sodass das
   Image ohne Anmeldung geladen werden kann.

Actions sind auf den Commit-SHA eines Releases festgelegt
(`actions/checkout@<sha> # v7.0.1`), Images auf Tag und Digest, sodass ein verschobener Tag
nicht ändern kann, was läuft. Workflows vergeben standardmäßig keine Berechtigungen; jeder
Job fordert an, was er braucht.

Ein privater Spiegel auf Gitea oder anderswo ist ein Pull-Spiegel des GitHub-Repositorys;
er führt keine eigene CI aus.
