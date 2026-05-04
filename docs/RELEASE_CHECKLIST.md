# Release Checklist

Use this checklist before publishing a new **360 PhotoLab** release.

---

## Version

- [ ] Version number updated in the Python file.
- [ ] Version number updated in `blender_manifest.toml`.
- [ ] Changelog updated.
- [ ] Release notes prepared.
- [ ] File names include the release version.

---

## Naming and trademark review

- [ ] Public name is **360 PhotoLab**.
- [ ] The extension name does not use “Blender” as part of the product name.
- [ ] Blender is used only descriptively, for example “add-on for Blender”.
- [ ] Manifest ID is `photo360_lab`.
- [ ] README and docs use the new name consistently.

---

## Manifest

- [ ] `blender_manifest.toml` is included in the extension ZIP.
- [ ] `schema_version` is present.
- [ ] `id = "photo360_lab"`.
- [ ] `name = "360 PhotoLab"`.
- [ ] `version` matches the release.
- [ ] `tags` only uses supported Blender Extensions tags.
- [ ] Permission reasons do not end with punctuation.
- [ ] License uses `SPDX:GPL-3.0-or-later`.

---

## Code

- [ ] No private paths.
- [ ] No local test images included by mistake.
- [ ] No personal credentials.
- [ ] No temporary debug prints unless intentionally kept.
- [ ] Add-on metadata is present and correct.
- [ ] `register()` does not call legacy cleanup/versioning helpers.
- [ ] Add-on can be enabled.
- [ ] Add-on can be disabled.
- [ ] Blender restarts without add-on errors.

---

## Workflow test

- [ ] Load a 360° equirectangular image.
- [ ] Prepare the working setup.
- [ ] Enter camera/reframe view.
- [ ] Generate CIL preview.
- [ ] Generate CLV preview.
- [ ] Generate rectilinear preview.
- [ ] Export final PNG.
- [ ] Export final TIFF if available.
- [ ] Export final JPEG if available.
- [ ] Check exported image quality.
- [ ] Repeat the workflow with a second image.

---

## Documentation

- [ ] README updated.
- [ ] Installation instructions checked.
- [ ] Known limitations updated.
- [ ] Screenshots updated if UI changed.
- [ ] Release notes are clear.

---

## GitHub release

- [ ] Correct tag created.
- [ ] Release title written.
- [ ] Release notes pasted.
- [ ] Installable extension ZIP uploaded.
- [ ] Release marked as beta/pre-release if appropriate.
- [ ] Download links tested.
