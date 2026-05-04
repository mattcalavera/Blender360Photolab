# Installation Guide

360 PhotoLab can be installed as a Blender extension package.

For Blender 4.2+ and 5.x, use the extension ZIP attached to a GitHub release.

---

## Recommended method — install the extension ZIP

Use this method for public releases.

Download the asset named like:

```text
360PhotoLab-v0.36.0-beta-extension.zip
```

Then install it in Blender:

1. Open Blender.
2. Go to:

   ```text
   Edit > Preferences > Extensions
   ```

3. Choose the option to install an extension from a local ZIP file.
4. Select the downloaded release asset ZIP.
5. Enable **360 PhotoLab**.
6. Open the 3D View sidebar and look for the **360 PhotoLab** tab.

---

## Important: do not use GitHub source archives

Do not install GitHub's automatically generated archives:

```text
Source code (zip)
Source code (tar.gz)
```

Those files are repository archives. They are not guaranteed to have the extension package structure expected by Blender.

Use only the ZIP file attached as a release asset.

---

## Expected extension ZIP structure

The installable ZIP should contain:

```text
__init__.py
blender_manifest.toml
```

The manifest should identify the extension as:

```toml
id = "photo360_lab"
name = "360 PhotoLab"
```

---

## Troubleshooting

If the add-on does not appear after installation:

- check that you downloaded the correct ZIP from the release assets;
- check that the ZIP contains `blender_manifest.toml`;
- restart Blender;
- open the system console and check for Python errors;
- report the issue on GitHub with Blender version, operating system and screenshots.
