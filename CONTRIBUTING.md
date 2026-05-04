# Contributing to 360 PhotoLab

Thank you for your interest in **360 PhotoLab**.

360 PhotoLab is an add-on for Blender focused on reframing equirectangular 360° still photos, generating RET/CIL/CLV previews and exporting photographic images for editing, sharing or print-oriented workflows.

Contributions are welcome, especially in the following areas:

- bug reports;
- Blender compatibility testing;
- documentation improvements;
- user interface improvements;
- projection or preview workflow improvements;
- export workflow improvements;
- example files and screenshots.

---

## How to report a bug

Please open a GitHub Issue and include:

- Blender version;
- operating system;
- 360 PhotoLab version;
- whether you installed the release asset ZIP or another file;
- steps to reproduce the issue;
- expected behavior;
- actual behavior;
- screenshots, if useful;
- sample image, only if it can be publicly shared.

A good bug report should make it possible to reproduce the problem.

---

## How to suggest a feature

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

## Pull requests

Before opening a pull request:

1. Test the add-on in Blender.
2. Make sure the add-on can be enabled and disabled cleanly.
3. Avoid hardcoded local file paths.
4. Avoid adding unnecessary external dependencies.
5. Keep changes focused and explain the reason for the change.
6. Do not reintroduce development-only startup cleanup behavior in `register()`.

---

## Coding guidelines

- Keep the user workflow clear and predictable.
- Prefer explicit names for operators, panels and properties.
- Avoid destructive operations unless they are clearly documented.
- Keep Blender UI labels concise.
- Preserve compatibility with current Blender Python API conventions.
- Do not include personal paths, private files or test images that cannot be redistributed.

---

## License

By contributing to this project, you agree that your contribution will be distributed under the same license as the project: **GNU GPL v3.0 or later**.
