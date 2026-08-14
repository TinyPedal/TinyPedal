# AUR packaging helpers

This folder provides templates and scripts to publish TinyPedal to the AUR
using a release tarball.

## Quick start

1) Copy `vars.example` to `vars.env` and set your AUR account name:

```sh
cp packaging/aur/vars.example packaging/aur/vars.env
```

2) Render the package files:

```sh
./packaging/aur/render.sh
```

3) Update the checksum (required for publishing):

```sh
cd packaging/aur/out
updpkgsums
```

4) Sync to your AUR repo:

```sh
./packaging/aur/push.sh
```

## What gets generated

- `packaging/aur/out/PKGBUILD`
- `packaging/aur/out/.SRCINFO`
- `packaging/aur/out/tinypedal.install`

Both are rendered from templates. `pkgver` is derived from the latest git tag
in this repo (for example, `v2.40.0` -> `2.40.0`).

## AUR authentication

The helper scripts use SSH by default. The maintainer running `push.sh` must
have an SSH key configured for the AUR account specified in `AUR_SSH_USER`.
You can also override `AUR_GIT_URL` in `vars.env` if you need a different
authentication method.

## Notes

- `.SRCINFO` can be regenerated using `makepkg --printsrcinfo > .SRCINFO`.
