# Security

lastweek fetches public pages and writes local dumps. It does not post, like,
or modify remote content. It does not read browser cookies.

## Secrets

Never commit `~/.config/lastweek/env`, `.env`, or tokens. The engine must not
print `GITHUB_TOKEN` or `BRAVE_API_KEY`.

## Reports

Open a GitHub issue for non-sensitive bugs. For a token leak or injection in
render output, email the maintainer via GitHub profile and rotate the token.
