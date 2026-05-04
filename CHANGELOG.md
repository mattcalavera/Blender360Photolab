# Changelog

All notable changes to **360 PhotoLab** will be documented in this file.

This project follows a simple release history model. Internal development versions may be summarized only when they become relevant to a public release.

---

## [0.36.0-beta] - 2026-05-04

### Changed

- Renamed the public extension from its previous project name to **360 PhotoLab** to avoid using the Blender trademark as part of the product name.
- Updated the extension manifest identity to `photo360_lab`.
- Updated public documentation, release notes, packaging notes and templates for the new name.
- Updated installation instructions for Blender 4.2+ / 5.x extension ZIP packages.
- Simplified add-on registration for extension-platform submission: the development-only legacy cleanup helper `unregister_old_classes_and_props()` has been removed.
- Standardized registration behavior so that `register()` only registers classes and properties and does not perform legacy cleanup operations at add-on activation time.

### Fixed

- Addressed Blender Extensions review feedback about product naming and startup-time legacy cleanup.
- Removed unsupported manifest tag values from the extension metadata.
- Ensured the file-permission reason in `blender_manifest.toml` does not end with punctuation.

### Notes

- This is still a beta release.
- The add-on remains focused on still equirectangular 360° photos, not video reframing.
- The project is independent and not affiliated with, endorsed by or sponsored by the Blender Foundation.

---

## [0.35.1-beta] - 2026-05-03

### Fixed

- Packaging hotfix for Blender Extensions validation.
- Removed unsupported manifest tag value `Image`.
- Updated the file permission reason so it does not end with punctuation.

---

## [0.35.0-beta] - 2026-05-03

### Fixed

- Added a safer registration/update flow to avoid restricted data access during add-on activation.
- Addressed errors such as `_RestrictData object has no attribute objects` when enabling the add-on.

### Added

- Extension ZIP package for Blender 4.2+ / 5.x workflows.

---

## [0.34.0-beta] - 2026-05-03

### Fixed

- Avoided direct cleanup access to Blender data during add-on registration.
- Moved legacy cleanup behavior away from add-on activation.

---

## [0.33.0-beta] - 2026-05-03

### Added

- Export support for PNG, TIFF and JPEG.
- `.cube` LUT support with intensity control.
- Runtime cache for source image and LUT data.
- Print-size readout at 150 DPI and 300 DPI.
- Native/useful resolution estimation tools.
- RET, CIL and CLV projection workflow.
- Comparative preview layout with CIL and CLV on the upper row and RET centered below.

### Fixed

- Improved equirectangular seam handling at ±180°.
- Made bilinear sampling more robust around image borders and seam positions.

---

## Earlier internal versions

Earlier versions were internal development builds and are not intended for public release.
