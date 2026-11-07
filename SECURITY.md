# Security policy

## Credentials and environment files

- Never commit `.env`, private keys, access tokens, passwords, or production connection strings.
- Keep local configuration in an ignored `.env` file. Use `.env.example` only for non-secret variable names and safe placeholders.
- Configure automation credentials with narrowly scoped GitHub Actions secrets or environment secrets.
- If a credential was ever committed, revoke or rotate it immediately. Deleting the file in a later commit does not remove it from Git history or existing clones.
- If history cleanup is required, coordinate a repository-wide history rewrite, invalidate exposed credentials first, and notify collaborators before force-pushing.

## Reporting

Report suspected vulnerabilities privately to the repository maintainers. Do not publish active credentials or exploit details in public issues.
