# Packaging Notes

This document explains how to prepare Blender360Photolab for GitHub releases.

---

## Single-File Beta Release

For the first beta release, the simplest and safest distribution method is a single Python file:

```text
blender360photolab.py
```

This file can be installed directly from Blender:

```text
Edit > Preferences > Add-ons > Install from Disk
```

Release asset:

```text
blender360photolab-v0.29.0-beta.py
```

Recommended public instruction:

```text
Download the .py file from the release assets and install it from Blender Preferences.
```

---

## ZIP Release

A ZIP release should be provided only if it is tested as installable in Blender.

Recommended ZIP asset name:

```text
Blender360Photolab-v0.29.0-beta-installable.zip
```

Do not assume that GitHub's automatically generated source-code ZIP is suitable for Blender add-on installation.

---

## Recommended Release Assets

For `v0.29.0-beta`:

```text
blender360photolab-v0.29.0-beta.py
Blender360Photolab-v0.29.0-beta-installable.zip
```

The ZIP should be tested before publication.

---

## Pre-Release Checks

Before publishing a release:

- install the add-on from a clean Blender session;
- enable the add-on;
- load a test equirectangular image;
- generate previews;
- export PNG;
- disable the add-on;
- restart Blender and verify that no startup error appears.
