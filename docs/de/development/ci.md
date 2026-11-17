# CI und Releases

`.github/workflows/build.yaml` läuft bei jedem Push auf `main`, bei Versions-Tags
(`v1.2.3`) und bei Pull Requests, auch aus Forks. Die Jobs `backend`, `frontend`, `docs`
und `repository` laufen parallel (dieselben Prüfungen wie **Check: all**, dazu Trivy auf
dem Repository); anschließend baut `image` das Image, startet es gegen eine
Wegwerf-PostgreSQL, scannt es und überträgt es, außer bei Pull Requests, nach
`ghcr.io/marank/argus` (`latest`, `sha-…` und bei Tags `1.2.3`/`1.2`/`1`). Für den Push
wird das `GITHUB_TOKEN` des Workflows verwendet; Secrets sind nicht nötig.

Ein Release ist ein Versions-Tag auf `main`:

```bash
git tag v1.2.3 && git push origin v1.2.3
```

## Repository-Einstellungen auf GitHub

1. **`main` schützen** (*Settings → Branches* oder *Rules*): Änderungen nur per Pull
   Request, mit den Status-Checks `backend`, `frontend`, `docs`, `repository` und `image`
   als Pflicht.
2. **Dependabot** (*Settings → Advanced Security*): Abhängigkeitsgraph, Dependabot-Warnungen
   und Sicherheitsupdates einschalten. Wöchentliche Versionsupdates kommen aus
   `.github/dependabot.yml`. Nicht abgedeckt: `SUPERVISOR_VERSION` im Dockerfile, das
   Trivy-Image im Workflow und die pre-commit-Hooks (`pre-commit autoupdate`).
3. **Sichtbarkeit des Pakets**: Das Paket `argus` auf ghcr.io ist öffentlich, sodass das
   Image ohne Anmeldung geladen werden kann.

Ein privater Spiegel auf Gitea oder anderswo ist ein Pull-Spiegel des GitHub-Repositorys;
er führt keine eigene CI aus.
