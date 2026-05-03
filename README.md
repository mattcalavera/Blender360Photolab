# Blender360Photolab

**Blender360Photolab** is a beta Blender add-on for reframing **equirectangular 360° still photos** into conventional photographic images.

It is designed for drone, panoramic and 360° photo workflows where you want to extract a controlled still image from a full equirectangular panorama while choosing the projection, field of view, framing, color LUT and export resolution directly inside Blender.

> **Status:** beta. The add-on is usable, but the interface and internal projection tools are still evolving.

---

## Main features

- Reframe **equirectangular 360° still photos** inside Blender.
- Automatic scene setup after loading a source image.
- Automatic switch to **Rendered** mode and **Camera View** for composition.
- Camera-based framing controls:
  - yaw;
  - pitch / vertical shift, depending on projection mode;
  - roll;
  - horizontal field of view.
- Fine adjustment buttons for yaw, pitch, roll and FOV.
- **Orbit / framing mode** with axis-lock options.
- Three projection modes:
  - **RET / Rectilinear**;
  - **CIL / Cylindrical**;
  - **CLV / Cylindrical Level**, a cylindrical variant intended to reduce horizon curvature by treating pitch as a vertical framing shift.
- Comparative preview layout:
  - **CIL** and **CLV** on the upper row;
  - **RET** centered below.
- Preview view is automatically switched to an orthographic layout, centered on the previews, without the semi-transparent camera frame.
- `.cube` LUT support.
- LUT is applied automatically to generated previews and final exports when a LUT is loaded.
- LUT intensity control.
- Export formats:
  - **PNG 8-bit**, lossless;
  - **TIFF 16-bit**, lossless, uncompressed RGB master;
  - **JPEG**, high quality, lossy.
- Resolution presets and manual output size control.
- Print-size readout at **150 DPI** and **300 DPI**.
- Native/useful resolution estimation tools for the selected framing.
- Robust equirectangular bilinear sampling.
- Horizontal seam handling at **±180°** to avoid out-of-bounds sampling on the equirectangular image seam.
- Runtime cache for source image and LUT data to reduce repeated loading.

---

## What it is for

Blender360Photolab is useful when you have a high-resolution 360° still image and want to create a normal-looking photographic export, for example:

- a wide landscape image from a drone 360° panorama;
- a rectilinear view with controlled perspective;
- a cylindrical panoramic crop;
- a level cylindrical view with a straighter horizon;
- a print-oriented export where the output size is chosen according to the useful source detail;
- a LUT-corrected export from footage or stills shot in a flat/log profile, such as a DJI D-Log M workflow, when an appropriate `.cube` LUT is provided.

The add-on is focused on **still photos**, not video reframing.

---

## Projection modes

### RET / Rectilinear

The **RET** mode creates a classic perspective projection, similar to a conventional camera lens.

Use it when you want:

- natural straight lines near the center of the frame;
- a normal photographic look;
- narrower or medium fields of view;
- architectural or landscape views where perspective should look familiar.

Very wide FOV values can still introduce strong perspective stretching, as expected with rectilinear projection.

### CIL / Cylindrical

The **CIL** mode creates a cylindrical projection.

Use it when you want:

- a wider panoramic view;
- less horizontal stretching than a very wide rectilinear frame;
- a classic panorama-like look.

Depending on pitch, roll and the selected view, the horizon can appear curved. This is inherent to how an inclined view is mapped through a cylindrical projection.

### CLV / Cylindrical Level

The **CLV** mode is a level cylindrical variant.

In this mode, pitch is treated more like a **vertical framing shift** rather than a full camera tilt inside the cylindrical projection. This is intended to reduce the visible curvature of the horizon in many panoramic reframes.

Use it when:

- the cylindrical projection is useful;
- the horizon curvature in CIL is visually distracting;
- you want a wide view with a more stable-looking horizon.

CLV does not magically correct every possible horizon issue. Source roll, extreme pitch, very wide fields of view and the original 360° capture geometry still matter.

---

## Interface overview

The add-on appears in the Blender 3D View sidebar under the **Foto 360** tab.

The panel is organized into the following workflow sections.

### 1. Source

Load the equirectangular 360° still image and, optionally, a `.cube` LUT.

When an image is loaded, the add-on prepares the scene and switches the viewport to **Rendered Camera View** automatically.

### 2. View

Switch between:

- the main **Camera View** used for composition;
- the comparative **Preview View** with CIL, CLV and RET previews.

Preview generation automatically centers the view and uses an orthographic preview layout.

### 3. Framing

Adjust the framing using:

- yaw;
- pitch or vertical shift;
- roll;
- horizontal FOV;
- fine adjustment buttons;
- orbit/framing controls with optional axis locks.

### 4. Projection

Choose the active projection mode:

- Rectilinear;
- Cylindrical;
- Cylindrical Level.

The projection selector and the RET/CIL/CLV toggle control the projection used for the final export.

### 5. Resolution and print

Set output resolution using presets or custom dimensions.

The panel also reports estimated print sizes at:

- **150 DPI**;
- **300 DPI**.

Additional tools estimate the useful/native output size for the current framing so that exports do not become unnecessarily oversampled.

### 6. Export

Choose the export format and save the reframed image.

The output filename is generated with useful suffixes, including:

- projection code: `_RET`, `_CIL` or `_CLV`;
- `_Lut` when a LUT is loaded;
- final pixel size, for example `_6000x3375`.

Example:

```text
DJI_20260426_0008_CLV_Lut_6000x3375.tif
```

---

## Export formats

### PNG 8-bit lossless

PNG is the default safe export format.

Use it when you want:

- a clean lossless file;
- broad compatibility;
- no JPEG artifacts;
- a practical final export.

PNG export is lossless, but the current PNG writer is 8-bit per channel.

### TIFF 16-bit lossless

TIFF 16-bit is the recommended master format for large prints or further editing.

Use it when you want:

- a higher-quality master file;
- 16-bit RGB output;
- a lossless uncompressed file for printing or post-processing.

The TIFF writer is internal and does not rely on Blender's normal render output pipeline.

### JPEG high quality

JPEG is useful for lightweight copies, previews or quick sharing.

Use it when:

- file size matters more than maximum quality;
- the image is a delivery copy rather than a master;
- the target platform expects JPEG.

JPEG is lossy and can introduce compression artifacts, especially in skies, clouds and smooth gradients.

---

## LUT workflow

The add-on supports `.cube` LUT files.

When a LUT is loaded:

- it is applied to generated previews;
- it is applied to final exports;
- `_Lut` is added to the suggested output filename;
- LUT intensity can be adjusted from the panel.

This is especially useful for workflows where the source image is visually flat or log-like and needs a conversion LUT, for example a DJI D-Log M to Rec.709 style workflow.

The add-on does not include a built-in DJI LUT. Users must provide their own `.cube` file.

---

## Installation: Blender 4.2+ / 5.x extension ZIP

For Blender 4.2+ and 5.x, install the add-on using the **extension ZIP attached as a release asset**.

Do **not** install GitHub's automatic **Source code (zip)** archive. That archive is generated by GitHub and may not contain the packaged extension structure required by Blender.

### Correct installation steps

1. Open the project's **Releases** page.
2. Download the release asset named like:

   ```text
   Blender360Photolab-vXXX.zip
   ```

   or the explicitly packaged extension ZIP provided with the release.

3. Do **not** download:

   ```text
   Source code (zip)
   Source code (tar.gz)
   ```

4. In Blender, open:

   ```text
   Edit > Preferences > Extensions
   ```

5. Use Blender's option to install an extension from a local ZIP file.
6. Select the downloaded **release asset ZIP**.
7. Enable the extension.
8. Open the 3D View sidebar and look for the **Foto 360** tab.

The extension package should include a `blender_manifest.toml` file. This file is part of Blender's extension packaging system and is expected in the release ZIP.

---

## Basic workflow

1. Open Blender.
2. Install and enable the extension.
3. Open the 3D View sidebar.
4. Go to **Foto 360**.
5. Click **Carica foto 360** and select an equirectangular image.
6. Blender360Photolab automatically switches to Rendered Camera View.
7. Adjust yaw, pitch/shift, roll and FOV.
8. Choose the projection mode: RET, CIL or CLV.
9. Generate previews to compare the projection modes.
10. Choose output resolution and export format.
11. Export the final reframed image.

---

## Recommended workflow for print

For print-oriented output:

1. Load the 360° image.
2. Load a `.cube` LUT if the source needs color conversion.
3. Compose the frame in Camera View.
4. Compare RET, CIL and CLV using the preview view.
5. Use the useful/native resolution tools to avoid excessive oversampling.
6. Check the 150 DPI and 300 DPI print-size readouts.
7. Export a **TIFF 16-bit** master.
8. Create JPEG copies only for sharing or lightweight delivery.

---

## Known limitations

- This is a **beta** project.
- The add-on is designed for **still equirectangular photos**, not video reframing.
- CLV helps reduce horizon curvature in many cases, but it is not a universal horizon-correction system.
- Extreme FOV values can still produce visible geometric stretching.
- The add-on does not add real detail beyond what exists in the source 360° image.
- PNG output is lossless but currently 8-bit per channel.
- TIFF 16-bit export is better as a master format, but it does not create additional source dynamic range if the input data is already limited.
- LUT support requires a valid `.cube` LUT file supplied by the user.
- Color management is workflow-dependent; for log/flat sources, use an appropriate conversion LUT.
- Very large exports can require significant RAM and processing time.
- The project currently focuses on practical photographic reframing rather than a full panoramic stitching or video-editing pipeline.

---

## Version notes

The README describes the current analyzed add-on line based on the latest available script in this project history.

Current confirmed script features include:

- automatic Rendered Camera View after loading a 360° image;
- RET, CIL and CLV projection modes;
- CIL and CLV previews on the upper row;
- RET preview centered below;
- orthographic preview view without the camera-view overlay frame;
- PNG, TIFF and JPEG export;
- `.cube` LUT support;
- seam-safe equirectangular bilinear sampling.

---

## License

Blender360Photolab is released under:

```text
GPL-3.0-or-later
```

## Short community post

Blender360Photolab is a beta Blender add-on for reframing equirectangular 360° still photos into conventional photographic exports.

It provides a camera-based workflow with automatic Rendered Camera View setup, rectilinear and cylindrical projection modes, a level cylindrical mode for straighter horizons, comparative previews, `.cube` LUT support, print-size estimation and direct PNG/TIFF/JPEG export.

The project is aimed at photographers, drone users and panoramic-image workflows where a 360° still image needs to become a controlled, printable final photograph.
