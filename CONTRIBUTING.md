# Contributing to Argus

Thanks for your interest in Argus.

> [!IMPORTANT]
> Argus is still in active development, and its structure changes often. Until that
> settles, **pull requests are not accepted**: they would mostly collide with ongoing
> work, and pull requests opened anyway are closed without review. Bug reports and ideas
> as issues are welcome. This note goes away once contributions are open.

## Issues

- **Bugs:** what you did, what you expected, what happened instead, and the version
  (image tag or commit). Screenshots or logs help; remove personal data first.
- **Ideas:** describe the problem you want solved before the solution, so we can find
  the fitting place in Argus together.
- **Security issues:** do not open a public issue; report them privately through
  *Security → Report a vulnerability* on GitHub.

## Pull requests

Not accepted for now (see above). Once they are, this is how a change gets in:

1. Discuss larger changes in an issue first.
2. Fork, branch from `main`, keep the change focused on one topic.
3. Set up the project as in [Development setup](docs/en/development/index.md); `seed_demo` fills the
   database with demo data.
4. Follow the conventions in [AGENTS.md](AGENTS.md): structure, services, UUID models,
   strict typing, i18n (English and German), no inline scripts.
5. Add or update tests; backend coverage must stay at or above 90 %.
6. After model changes run `just migrations` (**DB: make migrations**), after API changes
   `just api-types` (**API: update types**),
   and commit the generated files.
7. Update the documentation in `docs/` (German and English) when users or operators notice the change.
8. Run `just check` (**Check: all**, see [Checks and tests](docs/en/development/checks.md)) before you push;
   CI runs the same checks on the pull request.

Commit messages and pull request titles are [Conventional Commits](https://www.conventionalcommits.org/)
in English, since release-please makes versions and the changelog from them:
`type(scope): imperative summary` (`feat(requests): show the model on the device page`),
a blank line, then what changed and why. Types: `feat`, `fix`, `perf`, `docs`, `refactor`,
`test`, `build`, `ci`, `chore`; `!` after the type or a `BREAKING CHANGE:` footer marks a
breaking change. See [CI and releases](docs/en/development/ci.md#releases).

## License

Argus is licensed under the [AGPL-3.0-or-later](LICENSE). By submitting a contribution
you agree that it is licensed under the same terms. Dependencies must be compatible
with it: permissive licenses, LGPL, GPL-3.0 and AGPL-3.0 are fine, GPL-2.0-only and SSPL
are not (checked in CI).
