# matrix-mautrix-telegram

openSUSE RPM packaging for the [mautrix-telegram](https://github.com/mautrix/telegram)
Matrix-Telegram puppeting bridge, built from upstream source instead of the
`dock.mau.dev/mautrix/telegram` Docker image.

## Why this exists

Docker was used as a stopgap to get the mautrix bridges running quickly. This repo
is part of migrating each bridge, one at a time, to:

1. a pinned upstream **git tag** (not a `:latest` floating tag),
2. a **security audit** of that exact tag (`govulncheck` + `osv-scanner`, see `audit/`),
3. a **native RPM package** built via the openSUSE Build Service, distributed like any
   other distro package (`zypper install matrix-mautrix-telegram`), and
4. a **systemd service** under a dedicated unprivileged system user, instead of a
   container.

## Packaged version

- Upstream tag: `v0.2608.0` (displayed by the binary as `v26.08`)
- Note: the currently-running Docker `:latest` image was actually built from an
  unreleased dev snapshot 14 commits past this tag — that's inherent to floating
  Docker tags and one more reason to move off them. This package uses the last
  proper stable release instead.

## Security audit

See `audit/govulncheck-v26.08.txt` and `audit/osv-scanner-v26.08.txt`.

Summary: **0 exploitable vulnerabilities** (govulncheck dataflow analysis — nothing
the bridge's own code path actually reaches). 3 vulnerabilities were found in the
transitive `golang.org/x/crypto@0.55.0` dependency (SSH-client DoS + unmaintained
`openpgp` package) — none of which mautrix-telegram uses (it has no SSH client and
doesn't touch OpenPGP). `0001-bump-x-crypto-0.56.0-security.patch` bumps the
dependency anyway as defense-in-depth; it fixes 2 of the 3 (the third, GO-2026-5932,
has no fix — `openpgp` is upstream-deprecated and unused here regardless).

Re-run the audit yourself:

```bash
git clone --branch v0.2608.0 https://github.com/mautrix/telegram.git
cd telegram
git apply /path/to/0001-bump-x-crypto-0.56.0-security.patch
govulncheck ./...
osv-scanner scan source -r .
```

Requires `olm-devel` installed (mautrix-telegram CGO-links against libolm via
`maunium.net/go/mautrix/crypto/libolm`) or both scanners fail on the CGO package
with a `olm/olm.h: No such file or directory` error that looks unrelated at first
glance.

## Build dependencies

- `go1.27`
- `olm-devel` (build), `libolm3` (runtime)
- `zstd` (build, for unpacking the vendor tarball)

## Vendored dependencies (`vendor.tar.zst`)

OBS build workers have no network access, so Go module downloads that work
fine locally (`go build` reaching proxy.golang.org) fail on the build farm.
The standard openSUSE fix is vendoring: `vendor.tar.zst` in this repo
contains the full `vendor/` tree (`go mod vendor` output, zstd-compressed),
and the spec builds with `-mod=vendor` against it.

To regenerate after a `go.mod`/`go.sum` change (e.g. the next audit-driven
dependency bump):

```bash
cd mautrix-telegram-src   # the upstream checkout, patched to this package's tag
go mod vendor
tar --zstd -cf vendor.tar.zst vendor/
```

(The `openSUSE/obs-service-go_modules` OBS source service automates exactly
this — `osc service manualrun` — once that service is available in this
project; the `_service` file here documents the equivalent manual command
until then.)

## Package layout

- Binary: `/usr/bin/matrix-mautrix-telegram`
- Config: `/etc/matrix-mautrix-telegram/` (generated on first run by the binary itself,
  same as upstream's docker-run.sh does — run `matrix-mautrix-telegram -c
  /etc/matrix-mautrix-telegram/config.yaml -e` once by hand to generate it, then
  `-g -r registration.yaml` to generate the appservice registration)
- Data (SQLite DB, media cache): `/var/lib/matrix-mautrix-telegram/`
- Logs: `/var/log/matrix-mautrix-telegram/`
- Runs as dedicated system user `matrix-mautrix-telegram` (sysusers.d), never as root.

## OBS packaging

This package's source lives in this git repository; the OBS package definition
points at it via `<scmsync>` (git-based OBS workflow, not the classic in-OBS
checkout model) so source review happens as normal git history/PRs here, and OBS
just builds whatever this repo's default branch currently contains.

## Status

- [x] Upstream tag pinned, source vendored as reproducible tarball
- [x] Security audit (govulncheck + osv-scanner)
- [x] RPM spec, systemd unit, sysusers/tmpfiles config
- [x] Go module dependencies vendored (vendor.tar.zst) for offline OBS builds
- [ ] Built and tested in OBS
- [ ] Deployed on `doom`, Docker container decommissioned
