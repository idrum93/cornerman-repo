# Workflow staging folder

Byte-identical copies of the files in `.github/workflows/`. They live here
because GitHub's web uploader drops dotted folders, which forces
copy-pasting, and pasting rendered text from a browser can insert
non-breaking spaces that break YAML.

## Getting them into place without pasting

For each file: open `workflows/<name>.yml` -> pencil -> in the filename box
replace the name with `../.github/workflows/<name>.yml` -> commit.

**If a file already exists at the destination, delete it first**, or the
rename fails. Pasting over an existing file is what once left two deploy steps
in one job.

## Current round

| file | action |
|---|---|
| `capture.yml` | **updated** — delete the old one first, then rename |
| `refresh.yml` | **updated** — delete the old one first, then rename |
| `tests.yml` | unchanged |

Why capture and refresh changed: if a push lost a race with another job, the
old capture step could exit "nothing to commit" without ever pushing the
commit it had made — silently dropping ledger rows — and refresh swallowed a
failed push entirely. Both now commit once and retry the push.

## Verifying

The Actions sidebar should show **refresh**, **capture** and **tests**. A file path instead of a name means it did not parse; open it from
the sidebar and the error names the line.
