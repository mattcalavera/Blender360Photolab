# Blender360Photolab

**Blender360Photolab** is a Blender add-on for reframing equirectangular 360° photos directly inside Blender.

It turns Blender into a small 360 photo laboratory: import a 360° image, adjust the view, generate cylindrical previews, compare different projection layouts and export a final rectilinear image as a lossless PNG.

The add-on was created for photographers, drone pilots, virtual tour creators, architectural visualization users and anyone who needs a practical workflow for extracting standard photographic compositions from 360° images.

---

## Overview

Working with 360° photos can be difficult when the goal is to produce a conventional image from an equirectangular source.

Blender360Photolab provides a visual workflow inside Blender for:

- loading equirectangular 360° images;
- reframing the image using Blender's camera/view system;
- generating cylindrical preview layouts;
- previewing rectilinear output;
- exporting the final reframe as a PNG image.

The goal is not to replace dedicated panorama software, but to make Blender a flexible and visual environment for experimenting with 360° photographic composition.

---

## Main Features

- Import and work with equirectangular 360° images.
- Use Blender as a visual reframing environment.
- Generate cylindrical preview views.
- Generate rectilinear preview output.
- Display CIL and CLV preview views in a compact layout.
- Show the rectilinear preview below the cylindrical previews.
- Export the final result as PNG.
- Use a repeatable workflow for 360° photo reframing.
- Suitable for drone panoramas, virtual tours, architecture, landscape and creative photography.

---

## Typical Use Cases

Blender360Photolab can be useful for:

- drone 360° panoramas;
- architectural visualization;
- virtual tour preparation;
- landscape photography;
- creative reframing of 360° images;
- extracting normal photographic views from equirectangular images;
- testing cylindrical and rectilinear projection workflows;
- preparing images for publication, documentation or presentation.

---

## Why Blender?

Blender is usually seen as a 3D creation tool, but it also provides a powerful visual environment for camera control, projection experiments and image-based workflows.

Blender360Photolab uses Blender as a flexible photographic workspace where a 360° image can be explored, reframed and exported with repeatable controls.

This makes it possible to use Blender not only for 3D scenes, but also as a practical laboratory for 360° photography.

---
## Installation

Blender360Photolab can be installed as a standard Blender add-on.

### Option 1 — Install the single Python file

Use this method if the release provides a single `.py` file.

1. Download `blender360photolab.py` from the latest release.
2. Open Blender.
3. Go to:

   `Edit > Preferences > Add-ons`

4. Click **Install from Disk**.
5. Select `blender360photolab.py`.
6. Enable **Blender360Photolab** in the add-ons list.

### Option 2 — Install the ZIP package

Use this method if the release provides an installable ZIP package.

1. Download `Blender360Photolab.zip` from the latest release.
2. Open Blender.
3. Go to:

   `Edit > Preferences > Add-ons`

4. Click **Install from Disk**.
5. Select `Blender360Photolab.zip`.
6. Enable **Blender360Photolab** in the add-ons list.

Do not use GitHub's automatically generated “Source code ZIP” unless it is explicitly marked as installable.
Use the ZIP file attached to the release.

After enabling the add-on, the Blender360Photolab panel will be available inside Blender.

---

## Basic Workflow

1. Open Blender.
2. Load an equirectangular 360° image.
3. Use the add-on tools to create the working setup.
4. Adjust the view or camera framing.
5. Generate the preview layout.
6. Compare the cylindrical and rectilinear views.
7. Export the final rectilinear result as PNG.

---

## Output Format

The preferred export format is **PNG**.

PNG is lossless, which makes it suitable for photographic reframing workflows where image quality should be preserved during export and further editing.

---

## Current Status

Blender360Photolab is currently in **beta**.

The current version is usable and based on a stable internal development baseline, but it is still being tested and improved.

Feedback, bug reports and compatibility checks are welcome.

---

## Compatibility

Tested with:

- Blender: `Blender 4.x`
- Operating system: `macOS / Windows / Linux`

Please report your Blender version and operating system when opening an issue.

---

## Screenshots

Suggested screenshots for the repository:

```text
screenshots/
├── interface.png
├── equirectangular-input.png
├── cylindrical-preview-layout.png
├── rectilinear-preview.png
└── final-output.png
