# Testing Checklist

Use this checklist to test Blender360Photolab before public release.

---

## Environment

- [ ] Blender version recorded.
- [ ] Operating system recorded.
- [ ] Add-on version recorded.
- [ ] Test image source recorded.

---

## Installation

- [ ] Install from `.py` file.
- [ ] Enable add-on.
- [ ] Disable add-on.
- [ ] Restart Blender.
- [ ] Re-enable add-on.

---

## Basic Workflow

- [ ] Load an equirectangular 360° image.
- [ ] Prepare the scene/setup.
- [ ] Enter camera view.
- [ ] Adjust framing.
- [ ] Generate preview layout.
- [ ] Export PNG.

---

## Preview Layout

- [ ] CIL preview appears correctly.
- [ ] CLV preview appears correctly.
- [ ] CIL and CLV are on the same upper row.
- [ ] Rectilinear preview is centered below.
- [ ] No unwanted translucent frame appears.
- [ ] Switching between preview modes does not cause unexpected view jumps.

---

## Export

- [ ] PNG export succeeds.
- [ ] Output file is readable.
- [ ] Output framing matches the preview.
- [ ] Export does not overwrite unrelated files unexpectedly.

---

## Regression Checks

- [ ] Previously fixed CIL/CLV transition behavior remains fixed.
- [ ] Camera view remains consistent.
- [ ] Preview generation remains repeatable after the first setup.
- [ ] The workflow still works after loading a new image.
