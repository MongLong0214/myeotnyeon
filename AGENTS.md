# myeotnyeon — working rules

Project-local development and verification rules.

## Layout

- `.agent-control-plane/project.json` — the portable project contract. Changing it is a
  contract change and takes effect on the next run, never on the one judging it.
- `.github/workflows/project-ci.yml` — publishes the `project-ci` check.

## Verification

- `test` — `npm test`

## CommitLore

CommitLore is `preferred` for this repository. When initialization is needed, run
`commitlore init --mcp-scope none`, then `commitlore doctor` in this clone.
Decision records live in
commit trailers; Git does not carry active hooks into a fresh clone.

## Rules

- Do not weaken verification commands, workflow or manifest to make the same change pass.
- Verify legitimate contract changes under the existing approved contract. After separate approval,
  the new contract applies from the next run.
- Use `dev` for integration and `main` for releases.
