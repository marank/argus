# Contributing to Argus

Thanks for helping. Bug reports, ideas and pull requests are welcome.

## Issues

- **Bugs:** what you did, what you expected, what happened instead, and the version
  (image tag or commit). Screenshots or logs help; remove personal data first.
- **Ideas:** describe the problem you want solved before the solution, so we can find
  the fitting place in Argus together.
- **Security issues:** do not open a public issue; report them privately through
  *Security → Report a vulnerability* on GitHub.

## Pull requests

1. Discuss larger changes in an issue first.
2. Fork, branch from `main`, keep the change focused on one topic.
3. Set up the project as in the [README](README.md#quick-start); `seed_demo` fills the
   database with demo data.
4. Follow the conventions in [AGENTS.md](AGENTS.md): structure, services, UUID models,
   strict typing, i18n (English and German), no inline scripts.
5. Add or update tests; backend coverage must stay at or above 90 %.
6. After model changes run **DB: make migrations**, after API changes **API: update types**,
   and commit the generated files.
7. Update the user documentation in `docs/` (German) when users or operators notice the change.
8. Run **Check: all** (or the commands under [Checks](README.md#checks)) before you push;
   CI runs the same checks on the pull request.

Commit messages: an imperative summary line in English ("Show the model on the device
page"), a blank line, then what changed and why.

## License

Argus is licensed under the [AGPL-3.0-or-later](LICENSE). By submitting a contribution
you agree that it is licensed under the same terms. Dependencies must not be under
GPL, AGPL or SSPL (checked in CI).
