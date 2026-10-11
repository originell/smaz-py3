# Publishing a release

For package version `2.0.0`, publish a GitHub release tagged `v2.0.0`.
The Publish workflow builds the distributions, checks their metadata, runs the
tests against installed wheels and the source archive, and uploads the same files
to TestPyPI. After installation checks pass, approve the `pypi` deployment to
upload those files to PyPI.

Release tests install the `test` dependency group from `uv.lock` and verify its
package hashes. They do not rebuild the project when installing test tools.
Use uv 0.13.0 or newer to verify build dependency hashes.

Complete the account settings below **before publishing a GitHub release**.
The workflow declares environment names; approval rules live in GitHub settings.

## Configure GitHub environments

Open [repository environments](https://github.com/originell/smaz-py3/settings/environments)
and create these two environments:

| Setting | `pypi` | `testpypi` |
| --- | --- | --- |
| Deployment branches and tags | Selected branches and tags | Selected branches and tags |
| Allowed ref | Tag matching `v*` | Tag matching `v*` |
| Required reviewers | Your GitHub account or trusted release maintainers | Optional |
| Allow administrators to bypass protection | Disable | Disable if you require reviewers |
| Environment secrets | None | None |

Add a **Tag** rule, not a Branch rule. Do not add a branch deployment rule.
For a solo maintainer, leave **Prevent self-review** unchecked so you can approve
your own release. Enable it when another trusted maintainer can approve releases.

See [GitHub's environment instructions](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
for the controls and approval behavior.

## Register PyPI Trusted Publishers

Open [smaz-py3's PyPI publishing settings](https://pypi.org/manage/project/smaz-py3/settings/publishing/).
Under **Add a new publisher**, choose GitHub and enter:

| Field | Value |
| --- | --- |
| Owner | `originell` |
| Repository name | `smaz-py3` |
| Workflow filename | `publish.yml` |
| Environment name | `pypi` |

Use the filename `publish.yml`, without the `.github/workflows/` prefix.
Click **Add**.

Repeat on [TestPyPI](https://test.pypi.org/manage/project/smaz-py3/settings/publishing/)
with the same owner, repository, and workflow, but environment name `testpypi`.
PyPI and TestPyPI have separate accounts and publisher settings. If the TestPyPI
project does not exist, register a pending publisher for project `smaz-py3` under
[your TestPyPI account's Publishing settings](https://test.pypi.org/manage/account/publishing/).

Do not create API tokens. These jobs request short-lived credentials through
GitHub's identity service, and the publishing action generates signed publishing
attestations. See [PyPI's Trusted Publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

After merging the updated workflow and registering both publishers, delete
`PYPI_RELEASE_TOKEN` and `PYPI_TEST_TOKEN` from the repository's Actions secrets.
Revoke the corresponding tokens in PyPI and TestPyPI account settings too;
deleting a GitHub secret alone does not revoke its token.

## Protect the release source and tags

In [repository rulesets](https://github.com/originell/smaz-py3/settings/rules),
protect `main` with pull requests, required CI checks, and restrictions on force
pushes and deletion. After CI has run, require **Ruff and Rust checks** and the
Python test matrix checks.
When a second trusted maintainer can review your changes, require code-owner
approval too. `.github/CODEOWNERS` assigns the workflow and release configuration
to `@originell`; GitHub enforces that ownership only when review rules require it.

Create an active **tag ruleset** targeting `v*` with **Restrict creations**.
Give only the release maintainers a bypass; for this personal repository, that
can be the repository admin role. This controls who can create release tags.

Create a second active tag ruleset targeting `v*` with **Restrict updates** and
**Restrict deletions**, without bypasses. This keeps published tags fixed. Release
a new version to correct a problem instead of moving or replacing an old tag.

See [GitHub's ruleset instructions](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository).

Actions use full commit SHAs; publishing and Linux build containers use immutable
digests.
`.github/dependabot.yml` requests weekly Action updates. Review those pull requests
and their upstream release notes before merging; do not enable automatic merging
for publishing workflow updates.

When updating Maturin, update its workflow version, constraints, approved archive
hashes, and `uv.lock` together. Keep other workflow tool versions aligned.

Review and update container digests manually, keeping both publishing steps on
the same digest. Run the Publish workflow manually after tool or image updates.

In **Settings → Actions → General**, set workflow permissions to read-only,
disable workflow approval of pull requests, and require approval for all external
fork contributors.

## Rehearse without publishing

Merge the workflow onto `main`, then open **Actions → Publish → Run workflow**
and select `main`. This manual run builds and tests the release artifacts and
checks package metadata. It skips both publishing jobs and does not contact PyPI
for authentication. It therefore checks the build matrix, not the Trusted
Publisher account settings.

The wheel matrix builds 45 wheels: five Python versions across nine targets.
Tests run against the installed wheels on native Linux x64, Windows x64 and x86,
and macOS Intel and ARM runners. The additional Linux architectures are
cross-built and receive archive and metadata checks. The source archive is
installed and tested separately on Python 3.11.

If you change the build matrix, update `--expected-wheels` in `publish.yml`.
The completeness check deliberately fails when an expected artifact is missing.

## Publish

1. Set a new, unused version in `Cargo.toml`, update `Cargo.lock`, and add the
   release notes to `CHANGELOG.md`. Python package metadata gets its version from
   Cargo. For example, use `1.2.0` in Cargo and `v1.2.0` for the Git tag.
2. Merge the release changes into `main` and wait for CI to pass. The Publish
   workflow rejects release commits that are not part of `main`.
3. In **Releases → Draft a new release**, create the matching `v...` tag on that
   commit, add the release notes, and click **Publish release**.
4. Watch **Actions → Publish**. It builds and checks every distribution, runs
   package tests, uploads to TestPyPI, and tests installation from TestPyPI.
5. When **Upload to PyPI** waits for approval, inspect the commit and successful
   checks. Click **Review deployments**, select `pypi`, and approve.
6. Open [the PyPI project](https://pypi.org/project/smaz-py3/) and verify the new
   version, wheel files, source archive, and publishing attestations.

The production uploader fails on existing files. Do not rebuild an already
published version to retry a failed upload: retain the original artifacts and
inspect which files were accepted. PyPI does not let you overwrite published
files. Fix release contents with a new version. TestPyPI tolerates existing files
on retries, but those files remain unchanged.
