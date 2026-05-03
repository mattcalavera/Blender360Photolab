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
Blender360Photolab-v0.35.0-beta-extension.zip
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
Blender360Photolab-v0.35.0-beta-extension.zip
```

Do not assume that GitHub's automatically generated source-code ZIP is suitable for Blender add-on installation.

---

## Recommended Release Assets

For `v0.35.0-beta`:

```text
Blender360Photolab-v0.35.0-beta-extension.zip
```

The ZIP should be tested before publication.

---
