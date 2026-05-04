# Testing Checklist

Use this checklist to test **360 PhotoLab** before public release.

---

## Environment

- [ ] Blender version recorded.
- [ ] Operating system recorded.
- [ ] Add-on version recorded.
- [ ] Test image source recorded.

---

## Installation

- [ ] Install from the release asset ZIP.
- [ ] ZIP contains `blender_manifest.toml`.
- [ ] Enable add-on.
- [ ] Disable add-on.
- [ ] Restart Blender.
- [ ] Re-enable add-on.
- [ ] Confirm no `_RestrictData` error appears.
- [ ] Confirm the add-on appears as **360 PhotoLab**.

---

## Basic workflow

- [ ] Load an equirectangular 360° image.
- [ ] Prepare the scene/setup.
- [ ] Enter Camera View.
- [ ] Adjust framing.
- [ ] Generate preview layout.
- [ ] Export PNG.

---

## Preview layout

- [ ] CIL preview appears correctly.
- [ ] CLV preview appears correctly.
- [ ] CIL and CLV are on the same upper row.
- [ ] Rectilinear preview is centered below.
- [ ] No unwanted translucent camera frame appears.
- [ ] Switching between preview modes does not cause unexpected view jumps.

---

## Export

- [ ] PNG export succeeds.
- [ ] TIFF export succeeds if enabled.
- [ ] JPEG export succeeds if enabled.
- [ ] Output file is readable.
- [ ] Output framing matches the preview.
- [ ] Export does not overwrite unrelated files unexpectedly.

---

## Regression checks

- [ ] Previously fixed CIL/CLV transition behavior remains fixed.
- [ ] Camera View remains consistent.
- [ ] Preview generation remains repeatable after the first setup.
- [ ] The workflow still works after loading a new image.
- [ ] Blender Extensions validation does not reject the manifest.
