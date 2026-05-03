# Installation Guide

Blender360Photolab can be installed as a standard Blender add-on.

There are two possible installation methods, depending on how the release is packaged.

---

## Option 1 — Install the Single Python File

Use this method if the release provides a single file such as:

```text
blender360photolab.py
```

Steps:

1. Download `blender360photolab.py` from the latest GitHub release.
2. Open Blender.
3. Go to:

   `Edit > Preferences > Add-ons`

4. Click **Install from Disk**.
5. Select `blender360photolab.py`.
6. Enable **Blender360Photolab** in the add-ons list.

This is the recommended method for the first beta release if the add-on is still distributed as a single Python file.

---

## Option 2 — Install an Add-on ZIP Package

Use this method only if the release provides an explicitly installable ZIP package, for example:

```text
Blender360Photolab-v0.29.0-beta.zip
```

Steps:

1. Download the ZIP file from the GitHub release assets.
2. Open Blender.
3. Go to:

   `Edit > Preferences > Add-ons`

4. Click **Install from Disk**.
5. Select the ZIP file.
6. Enable **Blender360Photolab** in the add-ons list.

Important: do not use GitHub's automatically generated “Source code ZIP” unless it is explicitly marked as installable.

---

## Troubleshooting

If the add-on does not appear after installation:

- check that you downloaded the correct file from the release assets;
- restart Blender;
- open the system console and check for Python errors;
- verify that the file contains valid Blender add-on metadata;
- report the issue on GitHub with Blender version, operating system and screenshots.
