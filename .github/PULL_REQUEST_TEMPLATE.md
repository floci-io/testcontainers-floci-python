## Summary

<!-- Briefly describe what this PR does and why. -->

## Related issue

<!-- Link the issue this PR addresses, e.g. "Fixes #123" or "Closes #456". -->
<!-- If there is no issue, explain why the change is needed. -->

## Type of change

<!-- Check the one that applies. -->

- [ ] Bug fix (`fix:` commit)
- [ ] New feature (`feat:` commit)
- [ ] Breaking change (`feat!:` commit or `BREAKING CHANGE:` footer)
- [ ] Documentation or chore

## Checklist

- [ ] `ruff check . && ruff format --check . && mypy floci && pytest -m "not integration"` passes, and `pytest -m integration` if Docker is available
- [ ] New or changed behaviour is covered by tests
- [ ] All commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.)
- [ ] Commits are signed off for the DCO (`git commit -s`)
- [ ] I have no more than 2 open, non-draft pull requests and no more than 4 open pull requests in total (drafts included) in this repository (maintainers and dependency bots are exempt).
