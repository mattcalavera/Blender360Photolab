# Release Checklist

Use this checklist before publishing a new Blender360Photolab release.

---

## Version

- [ ] Version number updated.
- [ ] Changelog updated.
- [ ] Release notes prepared.
- [ ] File names include the release version.

---

## Code

- [ ] No private paths.
- [ ] No local test images included by mistake.
- [ ] No personal credentials.
- [ ] No temporary debug prints unless intentionally kept.
- [ ] Add-on metadata is present and correct.
- [ ] Add-on can be enabled.
- [ ] Add-on can be disabled.
- [ ] Blender restarts without add-on errors.

---

## Workflow Test

- [ ] Load a 360° equirectangular image.
- [ ] Prepare the working setup.
- [ ] Enter camera/reframe view.
- [ ] Generate CIL preview.
- [ ] Generate CLV preview.
- [ ] Generate rectilinear preview.
- [ ] Export final PNG.
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

## GitHub Release

- [ ] Correct tag created.
- [ ] Release title written.
- [ ] Release notes pasted.
- [ ] Installable assets uploaded.
- [ ] Release marked as beta/pre-release if appropriate.
- [ ] Download links tested.
