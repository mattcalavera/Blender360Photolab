# Packaging Notes

This document explains how to prepare **360 PhotoLab** for GitHub releases and Blender Extensions submission.

---

## Public name and technical ID

Public extension name:

```text
360 PhotoLab
```

Technical manifest ID:

```text
photo360_lab
```

The public name avoids using the Blender trademark as part of the product name. The word Blender may still be used descriptively, for example “an add-on for Blender”.

---

## Extension manifest

The release ZIP must include `blender_manifest.toml`.

Recommended manifest:

```toml
schema_version = "1.0.0"

id = "photo360_lab"
version = "0.36.0"
name = "360 PhotoLab"
tagline = "Reframe equirectangular 360 photos with RET CIL and CLV previews"
maintainer = "Mattia Fiorini <https://github.com/mattcalavera>"
type = "add-on"

website = "https://github.com/mattcalavera/360PhotoLab"
tags = ["Camera", "Import-Export"]
blender_version_min = "4.2.0"
license = ["SPDX:GPL-3.0-or-later"]

[permissions]
files = "Load local 360 images and LUT files and export images"
```

Notes:

- The permission reason must not end with punctuation.
- Tags must be supported Blender Extensions add-on tags.
- Do not use unsupported tags such as `Image`.

---

## Extension ZIP structure

Recommended package:

```text
360PhotoLab-v0.36.0-beta-extension.zip
├── __init__.py
└── blender_manifest.toml
```

The `__init__.py` file contains the add-on code.

---

## Registration rules

For Blender Extensions submission, keep registration clean:

```python
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_props()


def unregister():
    unregister_props()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
```

Do not run legacy cleanup helpers during `register()`.

In particular, do not include development-only startup cleanup such as:

```python
unregister_old_classes_and_props()
cleanup_old_visual_artifacts()
```

Those helpers are useful while repeatedly reloading scripts from Blender's Scripting workspace, but they are not appropriate for a first public extension-platform release.

---

## Release assets

For `v0.36.0-beta`, attach:

```text
360PhotoLab-v0.36.0-beta-extension.zip
```

Do not tell users to install GitHub's automatically generated Source code ZIP.
