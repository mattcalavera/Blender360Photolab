# Contributing to Blender360Photolab

Thank you for your interest in **Blender360Photolab**.

Blender360Photolab is a Blender add-on for reframing equirectangular 360° photos, generating cylindrical previews and exporting rectilinear views.

Contributions are welcome, especially in the following areas:

- bug reports;
- compatibility testing;
- documentation improvements;
- user interface improvements;
- new projection or preview modes;
- export workflow improvements;
- example files and screenshots.

---

## How to Report a Bug

Please open a GitHub Issue and include:

- Blender version;
- operating system;
- Blender360Photolab version;
- steps to reproduce the issue;
- expected behavior;
- actual behavior;
- screenshots, if useful;
- sample image, only if it can be publicly shared.

A good bug report should make it possible to reproduce the problem.

---

## How to Suggest a Feature

Please open a GitHub Issue and describe:

- what the feature should do;
- why it would be useful;
- how it would fit into the Blender workflow;
- whether it relates to a specific 360° photography use case.

Examples:

- batch export of several camera angles;
- saved reframe presets;
- additional projection types;
- preview layout customization;
- improved support for drone 360 panoramas.

---

## Pull Requests

Before opening a pull request:

1. Test the add-on in Blender.
2. Make sure the add-on can still be enabled and disabled cleanly.
3. Avoid hardcoded local file paths.
4. Avoid adding unnecessary external dependencies.
5. Keep changes focused and explain the reason for the change.

---

## Coding Guidelines

- Keep the user workflow clear and predictable.
- Prefer explicit names for operators, panels and properties.
- Avoid destructive operations unless they are clearly documented.
- Keep Blender UI labels concise.
- Preserve compatibility with current Blender Python API conventions.
- Do not include personal paths, private files or test images that cannot be redistributed.

---

## License

By contributing to this project, you agree that your contribution will be distributed under the same license as the project: **GNU GPL v3.0 or later**.
