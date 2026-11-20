# CI and releases

`.github/workflows/build.yaml` runs on every push to `main`, on version tags (`v1.2.3`)
and on pull requests, also from forks. The jobs `backend`, `frontend`, `docs`,
`workflows` and `repository` run in parallel (the first four run the `just check-…`
recipes, the same as `just check`; `repository` runs Trivy on the repository); `image` then builds the image, starts it against a throwaway PostgreSQL,
scans it and, except for pull requests, pushes it to `ghcr.io/marank/argus` (`latest`,
`sha-…`, and `1.2.3`/`1.2`/`1` for tags). The push uses the workflow's `GITHUB_TOKEN`;
no secrets are needed.

Every Monday the workflow also runs on `main` without a change. Every build installs the
image's system packages anew (`--no-cache-filter runtime`), so the weekly run publishes
`latest` with Debian's security fixes, and a scan that finds a new critical
vulnerability turns it red. Images of version tags are not rebuilt; a fix there needs
a new release.

## Releases

Releases come from release-please (`.github/workflows/release.yaml`). From the commit
messages on `main` it keeps a pull request "chore(main): release X.Y.Z" up to date with
the next version and `CHANGELOG.md`. Merging it tags `vX.Y.Z`, creates the GitHub release
and builds the image with the version tags.

The commit messages decide the version, so they are
[Conventional Commits](https://www.conventionalcommits.org/): `feat:` makes a minor
release, `fix:` a patch release, `feat!:` or a `BREAKING CHANGE:` footer a major one
(before 1.0 a minor one). `docs:`, `refactor:`, `test:`, `build:`, `ci:` and `chore:` make
no release and stay out of the changelog. Dependabot writes `fix(deps):` for what ends up
in the image or with operators and `chore(deps):` for development tools and CI.

::: info Good to know
Pull requests are merged with *Squash and merge*: the pull request's title becomes the
commit on `main`, so the title has to be a Conventional Commit.
:::

## Repository settings on GitHub

1. **Protect `main`** (*Settings → Branches* or *Rules*): changes only by pull request,
   with the status checks `backend`, `frontend`, `docs`, `workflows`, `repository` and
   `image` required.
2. **Dependabot** (*Settings → Advanced Security*): switch on the dependency graph,
   Dependabot alerts and security updates. Weekly version updates come from
   `.github/dependabot.yml`, each release only once it is a week old. Not covered:
   `SUPERVISOR_VERSION` in the Dockerfile; in `build.yaml` the job containers, `TRIVY_IMAGE`,
   `POSTGRES_IMAGE` (same major as `compose.yml`) and `JUST_VERSION`; `actionlint` and
   `zizmor` in the `justfile`; the pre-commit hooks (`pre-commit autoupdate`).
3. **Releases** (*Settings → Actions → General*): switch on *Allow GitHub Actions to
   create and approve pull requests*, or release-please cannot open its pull request.
   Under *Settings → General → Pull Requests* allow only *squash merging*, with the pull
   request title as the default commit message.
4. **Package visibility**: the `argus` package on ghcr.io is public, so the image can be
   pulled without a login.

Actions are pinned to the commit SHA of a release (`actions/checkout@<sha> # v7.0.1`) and
images in the Dockerfile and the workflows to tag and digest, so a moved tag cannot change what
runs. `compose.yml` and `compose.dev.yml` name images by tag only, as operators expect. Workflows grant no
permissions by default; each job asks for what it needs.

A private mirror on Gitea or elsewhere is a pull mirror of the GitHub repository; it runs
no CI of its own.
