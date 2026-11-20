# CI and releases

`.github/workflows/build.yaml` runs on every push to `main`, on version tags (`v1.2.3`)
and on pull requests, also from forks. The jobs `backend`, `frontend`, `docs` and
`repository` run in parallel (the same checks as **Check: all**, plus Trivy on the
repository); `image` then builds the image, starts it against a throwaway PostgreSQL,
scans it and, except for pull requests, pushes it to `ghcr.io/marank/argus` (`latest`,
`sha-…`, and `1.2.3`/`1.2`/`1` for tags). The push uses the workflow's `GITHUB_TOKEN`;
no secrets are needed.

Every Monday the workflow also runs on `main` without a change. The image's system
packages are installed anew each day (build argument `APT_REFRESH`), so the weekly run
publishes `latest` with Debian's security fixes, and a scan that finds a new critical
vulnerability turns it red. Images of version tags are not rebuilt; a fix there needs
a new release.

A release is a version tag on `main`:

```bash
git tag v1.2.3 && git push origin v1.2.3
```

## Repository settings on GitHub

1. **Protect `main`** (*Settings → Branches* or *Rules*): changes only by pull request,
   with the status checks `backend`, `frontend`, `docs`, `repository` and `image` required.
2. **Dependabot** (*Settings → Advanced Security*): switch on the dependency graph,
   Dependabot alerts and security updates. Weekly version updates come from
   `.github/dependabot.yml`. Not covered: `SUPERVISOR_VERSION` in the Dockerfile, the
   Trivy image in the workflow and the pre-commit hooks (`pre-commit autoupdate`).
3. **Package visibility**: the `argus` package on ghcr.io is public, so the image can be
   pulled without a login.

A private mirror on Gitea or elsewhere is a pull mirror of the GitHub repository; it runs
no CI of its own.
