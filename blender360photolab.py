# Blender360Photolab
# Public release: v0.35.0-beta
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Based on internal script: reframe360_v033_complete.py

# ============================================================
# VERSIONE: 035 | 2026-05-03 11:41 (Europe/Rome)
# MODIFICA:
# - Baseline V035 mantenuta.
# - Fix aggiuntivo: update_callback e invalidate_callback ora escono subito durante la fase _RestrictData.
# - Questo evita accessi indiretti a bpy.data.objects/materials/images quando Blender abilita l'add-on da Preferences.
# ============================================================

bl_info = {
    "name": "Blender360Photolab V035",
    "author": "Mattia Fiorini",
    "version": (3, 5, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Foto 360",
    "description": "Reframe equirectangular 360 photos with camera view, CIL/CLV previews, rectilinear output, LUT and PNG/TIFF/JPEG export",
    "category": "Image",
}

import bpy
import math
import os
import tempfile
import struct
import zlib
from mathutils import Vector, Quaternion, Matrix
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty, EnumProperty
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper


CAMERA_NAME = "Reframe360_Camera_V035"
WORLD_NAME = "Reframe360_World_V035"
PREVIEW_CAMERA_NAME = "Reframe360_Preview_Camera_V035"
PREVIEW_COLLECTION_NAME = "Reframe360_Preview_V035"
CIL_GUIDE_OBJECT_NAME = "Reframe360_CIL_Guide_Rect_V035"
CIL_GUIDE_LABEL_NAME = "Reframe360_CIL_Guide_Label_V035"
CIL_GUIDE_MATERIAL_NAME = "Reframe360_CIL_Guide_Mat_V035"

# Cache runtime: evita di rileggere foto e LUT a ogni preview/export.
_SOURCE_ARRAY_CACHE = {}
_LUT_CACHE = {}


# ============================================================
# Pulizia / registrazione
# ============================================================

def unregister_old_classes_and_props():
    for name in [
        "REFRAME360_OT_load_image",
        "REFRAME360_OT_load_lut",
        "REFRAME360_OT_reload_color_mode",
        "REFRAME360_OT_toggle_projection",
        "REFRAME360_OT_nudge",
        "REFRAME360_OT_reset_view",
        "REFRAME360_OT_open_camera_view",
        "REFRAME360_OT_refresh_camera_guides",
        "REFRAME360_OT_toggle_view",
        "REFRAME360_OT_preview_active",
        "REFRAME360_OT_preview_both",
        "REFRAME360_OT_focus_previews",
        "REFRAME360_OT_clear_preview",
        "REFRAME360_OT_preset_4k",
        "REFRAME360_OT_preset_landscape_16_9",
        "REFRAME360_OT_preset_a3_3_2",
        "REFRAME360_OT_apply_realres",
        "REFRAME360_OT_apply_printmax",
        "REFRAME360_OT_render_save",
        "REFRAME360_PT_panel",
    ]:
        old_cls = getattr(bpy.types, name, None)
        if old_cls is not None:
            try:
                bpy.utils.unregister_class(old_cls)
            except Exception:
                pass

    for prop in dir(bpy.types.Scene):
        if prop.startswith("reframe360"):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass


def cleanup_old_visual_artifacts():
    object_prefixes = (
        "Reframe360_Mask_",
        "Reframe360_Guide_",
        "Reframe360_Preview_",
        "Reframe360_Camera_Frame_Preview_",
        "Reframe360_CIL_Guide_",
    )
    material_prefixes = (
        "Reframe360_Mask_",
        "Reframe360_Guide_",
        "Reframe360_Preview_",
        "Reframe360_Camera_Frame_Mat_",
        "Reframe360_CIL_Guide_",
    )
    image_prefixes = (
        "Reframe360_Preview_Image_",
        "Reframe360_Camera_Frame_Image_",
        "Reframe360_Camera_BG_Image_",
        "Reframe360_Output_",
    )

    for obj in list(bpy.data.objects):
        if obj.name.startswith(object_prefixes):
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

    for mat in list(bpy.data.materials):
        if mat.name.startswith(material_prefixes):
            try:
                bpy.data.materials.remove(mat)
            except Exception:
                pass

    for img in list(bpy.data.images):
        if img.name.startswith(image_prefixes):
            try:
                bpy.data.images.remove(img)
            except Exception:
                pass


def unregister_props():
    for prop in dir(bpy.types.Scene):
        if prop.startswith("reframe360"):
            try:
                delattr(bpy.types.Scene, prop)
            except Exception:
                pass


# ============================================================
# Utility viewport / scena
# ============================================================

def invalidate_preview(scene):
    try:
        scene.reframe360v33_last_preview_valid = False
    except Exception:
        pass


def force_rendered_view(context):
    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D":
                try:
                    space.shading.type = "RENDERED"
                except Exception:
                    pass
                try:
                    space.shading.use_scene_world_render = True
                except Exception:
                    pass
                try:
                    space.overlay.show_overlays = True
                    space.overlay.show_floor = True
                    space.overlay.show_axis_x = True
                    space.overlay.show_axis_y = True
                    space.overlay.show_axis_z = True
                except Exception:
                    pass


def set_preview_view_style(context):
    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        for space in area.spaces:
            if space.type == "VIEW_3D":
                try:
                    space.shading.type = "MATERIAL"
                except Exception:
                    pass
                try:
                    space.overlay.show_overlays = False
                    space.overlay.show_floor = False
                    space.overlay.show_axis_x = False
                    space.overlay.show_axis_y = False
                    space.overlay.show_axis_z = False
                except Exception:
                    pass


def jump_to_camera_view(context):
    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue

        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue

        space = next((s for s in area.spaces if s.type == "VIEW_3D"), None)
        if space is None:
            continue

        override = {
            "window": context.window,
            "screen": context.screen,
            "area": area,
            "region": region,
            "scene": context.scene,
            "space_data": space,
        }

        try:
            with context.temp_override(**override):
                bpy.ops.view3d.view_camera()
        except Exception:
            pass

        try:
            r3d = space.region_3d
            if r3d is not None:
                r3d.view_perspective = "CAMERA"
                r3d.view_camera_zoom = 0.0
                r3d.view_camera_offset = (0.0, 0.0)
        except Exception:
            pass

        break


def jump_to_preview_orthographic_view(context):
    """
    Vista anteprime senza passare dalla Camera View.
    Evita il riquadro/passepartout semitrasparente della camera e replica
    automaticamente il click manuale sulla vista -Y + centra/zoom.
    """
    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue

        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue

        space = next((s for s in area.spaces if s.type == "VIEW_3D"), None)
        if space is None:
            continue

        override = {
            "window": context.window,
            "screen": context.screen,
            "area": area,
            "region": region,
            "scene": context.scene,
            "space_data": space,
        }

        try:
            with context.temp_override(**override):
                bpy.ops.view3d.view_axis(type="FRONT", align_active=False)
                bpy.ops.view3d.view_selected(use_all_regions=False)
        except Exception:
            pass

        try:
            r3d = space.region_3d
            if r3d is not None:
                r3d.view_perspective = "ORTHO"
                # FRONT in Blender è la vista lungo -Y: è quella corretta per i piani anteprima.
                r3d.view_camera_zoom = 0.0
                r3d.view_camera_offset = (0.0, 0.0)
        except Exception:
            pass

        break


def set_basic_color_management(scene):
    try:
        scene.display_settings.display_device = "sRGB"
    except Exception:
        pass

    try:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.look = "None"
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
    except Exception:
        pass


def set_render_engine(scene):
    for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = engine
            return
        except Exception:
            continue


def projection_code(mode):
    if mode == "CYLINDRICAL_LEVEL":
        return "CLV"
    if mode == "CYLINDRICAL":
        return "CIL"
    return "RET"


def projection_label(mode):
    if mode == "CYLINDRICAL_LEVEL":
        return "cilindrica livellata"
    if mode == "CYLINDRICAL":
        return "cilindrica"
    return "rettilineare"


def format_print_size_cm(width_px, height_px, dpi):
    """Restituisce la dimensione di stampa teorica in centimetri per i DPI indicati."""
    width_cm = (max(1, int(width_px)) / float(dpi)) * 2.54
    height_cm = (max(1, int(height_px)) / float(dpi)) * 2.54
    return f"{width_cm:.1f} x {height_cm:.1f} cm"


def export_extension_for_format(fmt):
    if fmt == "TIFF16":
        return ".tif"
    if fmt == "JPEG":
        return ".jpg"
    return ".png"


def export_format_short_label(fmt):
    if fmt == "TIFF16":
        return "TIFF 16 bit"
    if fmt == "JPEG":
        return "JPEG"
    return "PNG"


def export_format_technical_note(fmt):
    if fmt == "TIFF16":
        return "Lossless, 16 bit RGB: master consigliato per stampa/editing."
    if fmt == "JPEG":
        return "Lossy: copia leggera per invio/condivisione, non master."
    return "Lossless, 8 bit RGBA: default sicuro e compatibile."


def get_suggested_export_filepath(scene):
    if scene.reframe360v33_image_path and os.path.exists(scene.reframe360v33_image_path):
        directory = os.path.dirname(scene.reframe360v33_image_path)
        base = os.path.splitext(os.path.basename(scene.reframe360v33_image_path))[0]
    else:
        directory = bpy.path.abspath("//") or os.path.expanduser("~")
        base = "reframe360"

    lut_suffix = "_Lut" if scene.reframe360v33_lut_path else ""
    ext = export_extension_for_format(scene.reframe360v33_export_format)

    filename = (
        f"{base}_"
        f"{projection_code(scene.reframe360v33_projection_mode)}"
        f"{lut_suffix}_"
        f"{scene.reframe360v33_render_width}x{scene.reframe360v33_render_height}"
        f"{ext}"
    )

    return os.path.join(directory, filename)


# ============================================================
# Camera principale e World equirettangolare
# ============================================================

def get_or_create_camera(scene):
    cam_obj = bpy.data.objects.get(CAMERA_NAME)

    if cam_obj is None:
        cam_data = bpy.data.cameras.new(CAMERA_NAME)
        cam_obj = bpy.data.objects.new(CAMERA_NAME, cam_data)
        bpy.context.collection.objects.link(cam_obj)

    cam_obj.location = (0, 0, 0)
    cam_obj.data.type = "PERSP"
    cam_obj.data.sensor_fit = "HORIZONTAL"
    cam_obj.data.clip_start = 0.001
    cam_obj.data.clip_end = 10000
    scene.camera = cam_obj

    return cam_obj


def calculate_vertical_fov_deg(scene, width=None, height=None, projection=None, fov=None):
    out_w = max(1, int(width or scene.reframe360v33_render_width))
    out_h = max(1, int(height or scene.reframe360v33_render_height))
    aspect = out_w / out_h

    h_deg = max(1.0, min(179.0, float(fov or scene.reframe360v33_fov)))
    h_rad = math.radians(h_deg)
    proj = projection or scene.reframe360v33_projection_mode

    if proj in {"CYLINDRICAL", "CYLINDRICAL_LEVEL"}:
        v_rad = 2.0 * math.atan(h_rad / (2.0 * aspect))
    else:
        v_rad = 2.0 * math.atan(math.tan(h_rad / 2.0) / aspect)

    return math.degrees(v_rad)


def update_camera(scene):
    cam = get_or_create_camera(scene)

    yaw = math.radians(scene.reframe360v33_yaw)
    pitch = math.radians(scene.reframe360v33_pitch)
    roll = math.radians(scene.reframe360v33_roll)

    # V035: la Camera View deve restare stabile quando si cambia RET/CIL/CLV.
    # In V027 la CLV azzerava il pitch della camera e usava shift_y: questo faceva
    # saltare visibilmente l'inquadratura passando da CIL a CLV. Ora la camera
    # mantiene sempre lo stesso asse ottico; la differenza CLV resta solo nella
    # reproiezione usata da anteprime/export, dove il pitch diventa shift verticale.
    direction = Vector((
        math.sin(yaw) * math.cos(pitch),
        math.cos(yaw) * math.cos(pitch),
        math.sin(pitch),
    ))

    if direction.length == 0:
        direction = Vector((0, 1, 0))

    direction.normalize()

    quat = direction.to_track_quat("-Z", "Y")

    if abs(roll) > 1e-6:
        quat = Quaternion(direction, roll) @ quat

    cam.rotation_euler = quat.to_euler()
    cam.data.angle = math.radians(max(1.0, min(179.0, scene.reframe360v33_fov)))
    cam.data.shift_x = 0.0
    cam.data.shift_y = 0.0

    scene.camera = cam


def setup_world_image(scene, filepath):
    if not filepath or not os.path.exists(filepath):
        return

    img = bpy.data.images.load(filepath, check_existing=True)

    try:
        img.reload()
    except Exception:
        pass

    try:
        img.colorspace_settings.name = "sRGB"
    except Exception:
        pass

    scene.reframe360v33_source_width = int(img.size[0])
    scene.reframe360v33_source_height = int(img.size[1])

    world = bpy.data.worlds.get(WORLD_NAME) or bpy.data.worlds.new(WORLD_NAME)
    scene.world = world
    world.use_nodes = True

    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    env = nodes.new(type="ShaderNodeTexEnvironment")
    env.name = "Foto 360 Equirettangolare V035"
    env.image = img

    try:
        env.projection = "EQUIRECTANGULAR"
    except Exception:
        pass

    bg = nodes.new(type="ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0

    out = nodes.new(type="ShaderNodeOutputWorld")

    links.new(env.outputs["Color"], bg.inputs["Color"])
    links.new(bg.outputs["Background"], out.inputs["Surface"])


def setup_scene_for_reframe(scene, filepath):
    scene.reframe360v33_image_path = filepath

    invalidate_preview(scene)
    set_render_engine(scene)
    set_basic_color_management(scene)

    scene.render.film_transparent = False
    scene.render.resolution_x = scene.reframe360v33_render_width
    scene.render.resolution_y = scene.reframe360v33_render_height
    scene.render.resolution_percentage = 100

    setup_world_image(scene, filepath)
    update_camera(scene)
    update_camera_guides(scene)

    cube = bpy.data.objects.get("Cube")
    if cube:
        try:
            bpy.data.objects.remove(cube, do_unlink=True)
        except Exception:
            pass


# ============================================================
# Guida arancione cilindrica nella vista camera
# ============================================================

def get_cil_mat():
    mat = bpy.data.materials.get(CIL_GUIDE_MATERIAL_NAME) or bpy.data.materials.new(CIL_GUIDE_MATERIAL_NAME)
    mat.diffuse_color = (1.0, 0.45, 0.02, 1.0)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    em = nodes.new(type="ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.45, 0.02, 1.0)
    em.inputs["Strength"].default_value = 1.8

    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(em.outputs["Emission"], out.inputs["Surface"])

    return mat


def get_or_create_cil_guide(scene):
    obj = bpy.data.objects.get(CIL_GUIDE_OBJECT_NAME)

    if obj is None:
        curve = bpy.data.curves.new(CIL_GUIDE_OBJECT_NAME + "_Curve", type="CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 1
        curve.fill_mode = "FULL"
        curve.bevel_depth = 0.0045
        curve.bevel_resolution = 2

        sp = curve.splines.new("POLY")
        sp.points.add(4)

        obj = bpy.data.objects.new(CIL_GUIDE_OBJECT_NAME, curve)
        bpy.context.collection.objects.link(obj)

    mat = get_cil_mat()

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    cam = get_or_create_camera(scene)
    obj.parent = cam
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.hide_render = True
    obj.hide_select = True
    obj.show_in_front = True

    return obj


def remove_cil_label_if_present():
    label = bpy.data.objects.get(CIL_GUIDE_LABEL_NAME)
    if label is not None:
        try:
            bpy.data.objects.remove(label, do_unlink=True)
        except Exception:
            pass


def build_cilindrical_boundary_points_for_camera(scene, cam):
    """
    Disegna il bordo CIL/CLV nello stesso piano della camera.

    V035: il calcolo usa il centro reale del frame camera restituito da Blender.
    La Camera View non usa più shift_y in CLV: il bordo viene quindi ridisegnato
    senza spostare il centro dell'inquadratura.
    """
    frame = cam.data.view_frame(scene=scene)
    xs = [p.x for p in frame]
    ys = [p.y for p in frame]
    z = frame[0].z
    distance = abs(z)

    center_x = (max(xs) + min(xs)) / 2.0
    center_y = (max(ys) + min(ys)) / 2.0

    h_fov = math.radians(max(1.0, min(179.0, scene.reframe360v33_fov)))
    half_h = h_fov / 2.0

    guide_projection = "CYLINDRICAL_LEVEL" if scene.reframe360v33_projection_mode == "CYLINDRICAL_LEVEL" else "CYLINDRICAL"
    v_cil = math.radians(
        calculate_vertical_fov_deg(
            scene,
            projection=guide_projection,
            fov=scene.reframe360v33_fov,
        )
    )

    tan_half_v_cil = math.tan(v_cil / 2.0)

    samples = 160
    top = []
    bottom = []

    for i in range(samples + 1):
        t = i / samples
        theta = -half_h + (2.0 * half_h * t)
        cos_t = max(math.cos(theta), 1e-6)

        x = center_x + distance * math.tan(theta)
        y = center_y + distance * (tan_half_v_cil / cos_t)

        top.append((x, y, z, 1.0))
        bottom.append((x, center_y - (y - center_y), z, 1.0))

    pts = top + list(reversed(bottom)) + [top[0]]
    return pts

def assign_poly_curve_points(obj, pts, bevel_depth):
    old_curve = obj.data

    curve = bpy.data.curves.new(obj.name + "_Curve", type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.fill_mode = "FULL"
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2

    sp = curve.splines.new("POLY")
    sp.points.add(len(pts) - 1)

    for i, p in enumerate(pts):
        sp.points[i].co = p

    curve.materials.append(get_cil_mat())
    obj.data = curve

    try:
        bpy.data.curves.remove(old_curve)
    except Exception:
        pass


def update_camera_guides(scene):
    cam = get_or_create_camera(scene)
    guide = get_or_create_cil_guide(scene)

    remove_cil_label_if_present()

    show = bool(scene.reframe360v33_show_cil_guide)

    guide.hide_set(not show)
    guide.hide_viewport = not show

    if not show:
        return

    scene.render.resolution_x = scene.reframe360v33_render_width
    scene.render.resolution_y = scene.reframe360v33_render_height

    pts = build_cilindrical_boundary_points_for_camera(scene, cam)
    bevel = 0.0065 if scene.reframe360v33_projection_mode in {"CYLINDRICAL", "CYLINDRICAL_LEVEL"} else 0.0045
    assign_poly_curve_points(guide, pts, bevel)


# ============================================================
# LUT .cube
# ============================================================

def parse_cube_lut(filepath):
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("File LUT non trovato")

    size = None
    data = []
    domain_min = (0, 0, 0)
    domain_max = (1, 1, 1)

    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()
            key = parts[0].upper()

            if key == "TITLE":
                continue

            if key == "LUT_3D_SIZE":
                size = int(parts[1])
                continue

            if key == "DOMAIN_MIN":
                domain_min = tuple(float(x) for x in parts[1:4])
                continue

            if key == "DOMAIN_MAX":
                domain_max = tuple(float(x) for x in parts[1:4])
                continue

            if len(parts) >= 3:
                try:
                    data.append(tuple(float(x) for x in parts[:3]))
                except ValueError:
                    pass

    if size is None:
        raise ValueError("LUT_3D_SIZE non trovato")

    expected = size ** 3

    if len(data) < expected:
        raise ValueError(f"LUT incompleta: trovati {len(data)}, attesi {expected}")

    return {
        "size": size,
        "domain_min": domain_min,
        "domain_max": domain_max,
        "data": data[:expected],
    }



def get_lut_cached(filepath):
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("File LUT non trovato")
    stat = os.stat(filepath)
    key = (filepath, stat.st_mtime_ns, stat.st_size)
    cached = _LUT_CACHE.get(key)
    if cached is not None:
        return cached
    lut = parse_cube_lut(filepath)
    _LUT_CACHE.clear()
    _LUT_CACHE[key] = lut
    return lut

def apply_lut_array_numpy(rgba, lut, strength, np):
    size = lut["size"]

    dmin = np.array(lut["domain_min"], dtype=np.float32)
    dmax = np.array(lut["domain_max"], dtype=np.float32)
    drange = np.maximum(dmax - dmin, 1e-6)

    lut_arr = np.array(lut["data"], dtype=np.float32).reshape((size, size, size, 3))
    flat = rgba.reshape((-1, 4))

    strength = max(0.0, min(1.0, float(strength)))

    for start in range(0, flat.shape[0], 500_000):
        end = min(start + 500_000, flat.shape[0])

        orig = flat[start:end, :3].copy()
        rgb = np.clip((orig - dmin) / drange, 0, 1)

        pos = rgb * (size - 1)
        i0 = np.floor(pos).astype(np.int32)
        i1 = np.clip(i0 + 1, 0, size - 1)
        d = pos - i0

        r0, g0, b0 = i0[:, 0], i0[:, 1], i0[:, 2]
        r1, g1, b1 = i1[:, 0], i1[:, 1], i1[:, 2]

        dr = d[:, 0:1]
        dg = d[:, 1:2]
        db = d[:, 2:3]

        c000 = lut_arr[b0, g0, r0]
        c100 = lut_arr[b0, g0, r1]
        c010 = lut_arr[b0, g1, r0]
        c110 = lut_arr[b0, g1, r1]

        c001 = lut_arr[b1, g0, r0]
        c101 = lut_arr[b1, g0, r1]
        c011 = lut_arr[b1, g1, r0]
        c111 = lut_arr[b1, g1, r1]

        c00 = c000 * (1 - dr) + c100 * dr
        c10 = c010 * (1 - dr) + c110 * dr
        c01 = c001 * (1 - dr) + c101 * dr
        c11 = c011 * (1 - dr) + c111 * dr

        c0 = c00 * (1 - dg) + c10 * dg
        c1 = c01 * (1 - dg) + c11 * dg

        out = np.clip(c0 * (1 - db) + c1 * db, 0, 1)
        flat[start:end, :3] = np.clip(orig * (1 - strength) + out * strength, 0, 1)

    return rgba


# ============================================================
# Reproject equirettangolare -> rettilineare/cilindrica
# ============================================================

def rotate_vector_np(v, axis, angle, np):
    axis = axis / max(np.linalg.norm(axis), 1e-12)

    return (
        v * math.cos(angle)
        + np.cross(axis, v) * math.sin(angle)
        + axis * np.dot(axis, v) * (1 - math.cos(angle))
    )


def get_view_basis_np(yaw_deg, pitch_deg, roll_deg, np):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)

    forward = np.array([
        math.sin(yaw) * math.cos(pitch),
        math.cos(yaw) * math.cos(pitch),
        math.sin(pitch),
    ], dtype=np.float32)

    forward = forward / max(np.linalg.norm(forward), 1e-12)

    right = np.array([
        math.cos(yaw),
        -math.sin(yaw),
        0,
    ], dtype=np.float32)

    right = right / max(np.linalg.norm(right), 1e-12)

    up = np.cross(right, forward)
    up = up / max(np.linalg.norm(up), 1e-12)

    if abs(roll) > 1e-6:
        right = rotate_vector_np(right, forward, roll, np)
        up = rotate_vector_np(up, forward, roll, np)

    return forward.astype(np.float32), right.astype(np.float32), up.astype(np.float32)


def load_source_array_np(scene, np):
    path = scene.reframe360v33_image_path
    if not path or not os.path.exists(path):
        raise RuntimeError("File sorgente non trovato")

    # Con LUT caricata il dato va letto in modo neutro per evitare doppie correzioni.
    # La vista camera/world invece resta sRGB e gradevole, perché passa da setup_world_image().
    technical_mode = bool(scene.reframe360v33_lut_path)
    stat = os.stat(path)
    key = (path, stat.st_mtime_ns, stat.st_size, technical_mode)
    cached = _SOURCE_ARRAY_CACHE.get(key)
    if cached is not None:
        src, w, h = cached
        scene.reframe360v33_source_width = int(w)
        scene.reframe360v33_source_height = int(h)
        return src, w, h

    img = bpy.data.images.load(path, check_existing=True)

    try:
        img.reload()
    except Exception:
        pass

    try:
        img.colorspace_settings.name = "Non-Color" if technical_mode else "sRGB"
    except Exception:
        pass

    w = int(img.size[0])
    h = int(img.size[1])

    if w <= 0 or h <= 0:
        raise RuntimeError("Risoluzione sorgente non valida")

    pixels = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(pixels)

    scene.reframe360v33_source_width = w
    scene.reframe360v33_source_height = h

    src = pixels.reshape((h, w, 4)).copy()
    src[..., 3] = 1

    _SOURCE_ARRAY_CACHE.clear()
    _SOURCE_ARRAY_CACHE[key] = (src, w, h)

    return src, w, h

def bilinear_sample_equirect(src, sx, sy, np):
    h, w, _ = src.shape

    # Robustezza bordo equirettangolare:
    # alcuni yaw/FOV possono produrre sx esattamente uguale a w (es. 15520),
    # che è fuori indice anche se geometricamente coincide con la cucitura 0.
    sx = np.asarray(sx, dtype=np.float32)
    sy = np.asarray(sy, dtype=np.float32)
    sx = np.nan_to_num(sx, nan=0.0, posinf=0.0, neginf=0.0)
    sy = np.nan_to_num(sy, nan=0.0, posinf=float(h - 1), neginf=0.0)

    sx_floor = np.floor(sx)
    sy_floor = np.floor(np.clip(sy, 0.0, float(h - 1)))

    x0 = np.mod(sx_floor.astype(np.int64), int(w)).astype(np.int32)
    y0 = np.clip(sy_floor.astype(np.int64), 0, int(h - 1)).astype(np.int32)

    x1 = ((x0.astype(np.int64) + 1) % int(w)).astype(np.int32)
    y1 = np.clip(y0.astype(np.int64) + 1, 0, int(h - 1)).astype(np.int32)

    tx = (sx - sx_floor)[..., None].astype(np.float32)
    ty = (np.clip(sy, 0.0, float(h - 1)) - sy_floor)[..., None].astype(np.float32)
    tx = np.clip(tx, 0.0, 1.0)
    ty = np.clip(ty, 0.0, 1.0)

    c00 = src[y0, x0]
    c10 = src[y0, x1]
    c01 = src[y1, x0]
    c11 = src[y1, x1]

    return (c00 * (1 - tx) + c10 * tx) * (1 - ty) + (c01 * (1 - tx) + c11 * tx) * ty


def reproject_360_to_view_np(
    scene,
    np,
    width=None,
    height=None,
    projection_mode=None,
    yaw=None,
    pitch=None,
    roll=None,
    fov=None,
    apply_lut=True,
):
    src, src_w, src_h = load_source_array_np(scene, np)

    out_w = max(1, int(width or scene.reframe360v33_render_width))
    out_h = max(1, int(height or scene.reframe360v33_render_height))

    projection = projection_mode or scene.reframe360v33_projection_mode

    yaw_deg = float(scene.reframe360v33_yaw if yaw is None else yaw)
    pitch_deg = float(scene.reframe360v33_pitch if pitch is None else pitch)
    roll_deg = float(scene.reframe360v33_roll if roll is None else roll)

    h_fov_deg = max(1.0, min(179.0, float(scene.reframe360v33_fov if fov is None else fov)))
    h_fov_rad = math.radians(h_fov_deg)

    v_fov_rad = math.radians(
        calculate_vertical_fov_deg(
            scene,
            width=out_w,
            height=out_h,
            projection=projection,
            fov=h_fov_deg,
        )
    )

    level_cyl = projection == "CYLINDRICAL_LEVEL"

    if level_cyl:
        yaw_rad = math.radians(yaw_deg)
        pitch_shift = math.tan(math.radians(max(-80.0, min(80.0, pitch_deg))))
        roll_rad = math.radians(roll_deg)
        cos_r = math.cos(roll_rad)
        sin_r = math.sin(roll_rad)
        forward_h = np.array([math.sin(yaw_rad), math.cos(yaw_rad), 0.0], dtype=np.float32)
        right_h = np.array([math.cos(yaw_rad), -math.sin(yaw_rad), 0.0], dtype=np.float32)
        up_h = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    else:
        forward, right, up = get_view_basis_np(yaw_deg, pitch_deg, roll_deg, np)

    dst = np.empty((out_h, out_w, 4), dtype=np.float32)

    x_norm = ((np.arange(out_w, dtype=np.float32) + 0.5) / out_w) * 2 - 1
    vertical_scale = math.tan(v_fov_rad / 2)

    if projection in {"CYLINDRICAL", "CYLINDRICAL_LEVEL"}:
        if not level_cyl:
            theta = x_norm * (h_fov_rad / 2)
            sin_base = np.sin(theta).astype(np.float32)
            cos_base = np.cos(theta).astype(np.float32)
    else:
        x_base = x_norm * math.tan(h_fov_rad / 2)

    for y_start in range(0, out_h, 128):
        y_end = min(y_start + 128, out_h)

        y_norm = ((np.arange(y_start, y_end, dtype=np.float32) + 0.5) / out_h) * 2 - 1
        y_view = y_norm * vertical_scale

        if level_cyl:
            # Cilindrica livellata: il cilindro resta verticale.
            # Pitch = shift verticale; Roll = rotazione 2D del quadro; l'orizzonte resta una linea.
            x_grid = x_norm[None, :]
            y_grid = y_norm[:, None]
            xr = x_grid * cos_r - y_grid * sin_r
            yr = x_grid * sin_r + y_grid * cos_r
            theta = xr * (h_fov_rad / 2.0)
            yy = yr * vertical_scale + pitch_shift

            sin_t = np.sin(theta).astype(np.float32)
            cos_t = np.cos(theta).astype(np.float32)

            dirs = (
                cos_t[..., None] * forward_h[None, None, :]
                + sin_t[..., None] * right_h[None, None, :]
                + yy[..., None] * up_h[None, None, :]
            )
        elif projection == "CYLINDRICAL":
            yy = y_view[:, None]
            sin_t = sin_base[None, :]
            cos_t = cos_base[None, :]

            dirs = (
                cos_t[..., None] * forward[None, None, :]
                + sin_t[..., None] * right[None, None, :]
                + yy[..., None] * up[None, None, :]
            )
        else:
            xx = x_base[None, :]
            yy = y_view[:, None]

            dirs = (
                forward[None, None, :]
                + xx[..., None] * right[None, None, :]
                + yy[..., None] * up[None, None, :]
            )

        dirs = dirs / np.maximum(np.linalg.norm(dirs, axis=2, keepdims=True), 1e-12)

        lon = np.arctan2(dirs[..., 1], dirs[..., 0])
        lat = np.arcsin(np.clip(dirs[..., 2], -1, 1))

        sx = ((-lon / (2.0 * math.pi)) + 0.5) * src_w - 0.5
        sy = ((lat / math.pi) + 0.5) * (src_h - 1)

        dst[y_start:y_end, :, :] = bilinear_sample_equirect(src, sx, sy, np)

    dst = np.clip(dst, 0, 1)
    dst[..., 3] = 1

    if apply_lut and scene.reframe360v33_lut_path:
        if not os.path.exists(scene.reframe360v33_lut_path):
            raise RuntimeError("LUT caricata ma file .cube non trovato")

        lut = get_lut_cached(scene.reframe360v33_lut_path)
        dst = apply_lut_array_numpy(dst, lut, scene.reframe360v33_lut_strength, np)
        dst[..., 3] = 1

    return dst


# ============================================================
# Writer export robusti
# ============================================================

def validate_rgba_array(rgba):
    if rgba is None or len(rgba.shape) != 3 or rgba.shape[2] != 4:
        raise RuntimeError("Array immagine non valido")

    if int((rgba[:, :, :3] * 255).max()) <= 2 and float((rgba[:, :, :3] * 255).mean()) <= 1.0:
        raise RuntimeError(
            "La reproiezione ha prodotto pixel neri: problema nella lettura della sorgente o LUT errata."
        )


def write_png_rgba8(filepath, rgba, np):
    validate_rgba_array(rgba)
    h, w, _ = rgba.shape

    arr8 = (np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8)
    arr8 = arr8[::-1, :, :]

    raw_data = b"".join((b"\x00" + arr8[y].tobytes()) for y in range(h))

    def chunk(chunk_type, data):
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw_data, 6))
        + chunk(b"IEND", b"")
    )

    with open(filepath, "wb") as f:
        f.write(png)

    return filepath


def write_tiff_rgb16_uncompressed(filepath, rgba, np, dpi=300):
    """Scrive un TIFF RGB 16 bit non compresso, lossless, senza dipendere dal renderer di Blender."""
    validate_rgba_array(rgba)
    h, w, _ = rgba.shape

    rgb16 = (np.clip(rgba[:, :, :3], 0, 1) * 65535 + 0.5).astype("<u2")
    rgb16 = rgb16[::-1, :, :]
    pixel_bytes = rgb16.tobytes(order="C")

    # TIFF little endian, baseline RGB 16 bit, strip unica.
    entries_count = 15
    ifd_offset = 8
    ifd_size = 2 + entries_count * 12 + 4
    data_offset = ifd_offset + ifd_size
    extras = []

    def add_extra(data):
        nonlocal data_offset
        off = data_offset
        extras.append(data)
        data_offset += len(data)
        if data_offset % 2:
            extras.append(b"\x00")
            data_offset += 1
        return off

    bits_offset = add_extra(struct.pack("<HHH", 16, 16, 16))
    xres_offset = add_extra(struct.pack("<II", int(dpi), 1))
    yres_offset = add_extra(struct.pack("<II", int(dpi), 1))
    software = b"Reframe360 V035\x00"
    software_offset = add_extra(software)
    sample_format_offset = add_extra(struct.pack("<HHH", 1, 1, 1))
    pixel_offset = data_offset
    byte_count = len(pixel_bytes)

    # type: 1 BYTE, 2 ASCII, 3 SHORT, 4 LONG, 5 RATIONAL.
    entries = [
        (256, 4, 1, w),
        (257, 4, 1, h),
        (258, 3, 3, bits_offset),
        (259, 3, 1, 1),
        (262, 3, 1, 2),
        (273, 4, 1, pixel_offset),
        (274, 3, 1, 1),
        (277, 3, 1, 3),
        (278, 4, 1, h),
        (279, 4, 1, byte_count),
        (282, 5, 1, xres_offset),
        (283, 5, 1, yres_offset),
        (296, 3, 1, 2),
        (305, 2, len(software), software_offset),
        (339, 3, 3, sample_format_offset),
    ]

    # SampleFormat = unsigned integer per i tre canali RGB.

    header = b"II" + struct.pack("<H", 42) + struct.pack("<I", ifd_offset)
    ifd = struct.pack("<H", len(entries))
    for tag, typ, count, value in entries:
        ifd += struct.pack("<HHII", tag, typ, count, value)
    ifd += struct.pack("<I", 0)

    with open(filepath, "wb") as f:
        f.write(header)
        f.write(ifd)
        for extra in extras:
            f.write(extra)
        f.write(pixel_bytes)

    return filepath


def write_jpeg_via_blender(filepath, rgba, np, quality=95):
    """Scrive JPEG usando il salvataggio immagine di Blender: formato lossy, utile come copia leggera."""
    validate_rgba_array(rgba)
    h, w, _ = rgba.shape

    img = bpy.data.images.new("Reframe360_Output_JPEG_TEMP_V035", width=w, height=h, alpha=True, float_buffer=False)

    old_settings = None
    scene = bpy.context.scene
    settings = scene.render.image_settings

    try:
        img.pixels.foreach_set(np.clip(rgba, 0, 1).astype(np.float32).reshape(-1))
        img.update()

        old_settings = (
            settings.file_format,
            settings.color_mode,
            settings.color_depth,
            settings.quality,
        )

        settings.file_format = "JPEG"
        settings.color_mode = "RGB"
        settings.color_depth = "8"
        settings.quality = int(max(1, min(100, quality)))

        img.save_render(filepath, scene=scene)
    finally:
        if old_settings:
            settings.file_format, settings.color_mode, settings.color_depth, settings.quality = old_settings
        try:
            bpy.data.images.remove(img, do_unlink=True)
        except Exception:
            pass

    return filepath


def export_reframed_image(scene, filepath):
    try:
        import numpy as np
    except Exception:
        raise RuntimeError("Numpy non disponibile in Blender")

    fmt = scene.reframe360v33_export_format
    ext = export_extension_for_format(fmt)
    filepath = os.path.splitext(filepath)[0] + ext
    rgba = reproject_360_to_view_np(scene, np)

    if fmt == "TIFF16":
        return write_tiff_rgb16_uncompressed(filepath, rgba, np)
    if fmt == "JPEG":
        return write_jpeg_via_blender(filepath, rgba, np, scene.reframe360v33_jpeg_quality)
    return write_png_rgba8(filepath, rgba, np)


def save_preview_png_temp(scene, rgba, projection_name, np):
    temp_dir = bpy.app.tempdir if bpy.app.tempdir else tempfile.gettempdir()

    filepath = os.path.join(
        temp_dir,
        f"reframe360_v030_preview_{projection_name}_{rgba.shape[1]}x{rgba.shape[0]}.png",
    )

    write_png_rgba8(filepath, rgba, np)

    return filepath


# ============================================================
# Anteprime
# ============================================================

def get_or_create_preview_collection():
    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)

    if col is None:
        col = bpy.data.collections.new(PREVIEW_COLLECTION_NAME)
        bpy.context.scene.collection.children.link(col)

    return col


def clear_preview_objects():
    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)

    if col:
        for obj in list(col.objects):
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass

    for img in list(bpy.data.images):
        if img.name.startswith("Reframe360_Preview_Image_"):
            try:
                bpy.data.images.remove(img)
            except Exception:
                pass

    for mat in list(bpy.data.materials):
        if mat.name.startswith("Reframe360_Preview_Mat_"):
            try:
                bpy.data.materials.remove(mat)
            except Exception:
                pass

    invalidate_preview(bpy.context.scene)


def get_or_create_preview_camera(scene):
    cam_obj = bpy.data.objects.get(PREVIEW_CAMERA_NAME)

    if cam_obj is None:
        cam_data = bpy.data.cameras.new(PREVIEW_CAMERA_NAME)
        cam_obj = bpy.data.objects.new(PREVIEW_CAMERA_NAME, cam_data)
        bpy.context.collection.objects.link(cam_obj)

    cam_obj.location = (0, -6, 0)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    cam_obj.data.type = "ORTHO"
    cam_obj.data.clip_start = 0.001
    cam_obj.data.clip_end = 1000

    return cam_obj


def make_emission_material(name, image=None, color=(1, 1, 1, 1)):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    em = nodes.new(type="ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0

    if image:
        tex = nodes.new(type="ShaderNodeTexImage")
        tex.image = image
        tex.extension = "CLIP"
        links.new(tex.outputs["Color"], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = color

    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(em.outputs["Emission"], out.inputs["Surface"])

    return mat


def make_preview_label(name, text, x, z):
    col = get_or_create_preview_collection()

    curve = bpy.data.curves.new(name + "_Curve", type="FONT")
    curve.body = text
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = 0.16

    obj = bpy.data.objects.new(name, curve)
    obj.location = (x, -0.03, z)
    obj.rotation_euler = (math.radians(90), 0, 0)

    obj.data.materials.append(
        make_emission_material("Reframe360_Preview_Mat_" + name, color=(1.0, 0.35, 0.0, 1.0))
    )

    col.objects.link(obj)


def make_preview_plane(name, png_path, x_offset, label_text, z_offset=0.0):
    col = get_or_create_preview_collection()

    image = bpy.data.images.load(png_path, check_existing=False)

    try:
        image.reload()
        image.colorspace_settings.name = "sRGB"
    except Exception:
        pass

    image.name = "Reframe360_Preview_Image_" + name

    aspect = int(image.size[0]) / max(1, int(image.size[1]))

    plane_h = 2.0
    plane_w = plane_h * aspect

    verts = [
        (-plane_w / 2 + x_offset, 0, -plane_h / 2 + z_offset),
        (plane_w / 2 + x_offset, 0, -plane_h / 2 + z_offset),
        (plane_w / 2 + x_offset, 0, plane_h / 2 + z_offset),
        (-plane_w / 2 + x_offset, 0, plane_h / 2 + z_offset),
    ]

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()

    uv = mesh.uv_layers.new(name="UVMap").data
    uv[0].uv = (0, 0)
    uv[1].uv = (1, 0)
    uv[2].uv = (1, 1)
    uv[3].uv = (0, 1)

    obj = bpy.data.objects.new(name, mesh)
    obj.display_type = "TEXTURED"

    obj.data.materials.append(
        make_emission_material(
            "Reframe360_Preview_Mat_" + name,
            image=image,
        )
    )

    col.objects.link(obj)

    make_preview_label(name + "_Label", label_text, x_offset, z_offset + plane_h / 2 + 0.24)

    return plane_w, plane_h


def make_preview_background(total_width, total_height):
    col = get_or_create_preview_collection()

    name = "Reframe360_Preview_BLACK_BACKGROUND"

    old = bpy.data.objects.get(name)
    if old:
        try:
            bpy.data.objects.remove(old, do_unlink=True)
        except Exception:
            pass

    w = total_width * 1.18
    h = total_height * 1.45

    verts = [
        (-w / 2, 0.06, -h / 2),
        (w / 2, 0.06, -h / 2),
        (w / 2, 0.06, h / 2),
        (-w / 2, 0.06, h / 2),
    ]

    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(
        make_emission_material(
            "Reframe360_Preview_Mat_BLACK_BACKGROUND",
            color=(0, 0, 0, 1),
        )
    )

    col.objects.link(obj)

    obj.hide_select = True

    return obj


def set_preview_visibility(scene, visible):
    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)
    preview_cam = bpy.data.objects.get(PREVIEW_CAMERA_NAME)

    if col:
        for obj in list(col.objects):
            obj.hide_viewport = not visible
            try:
                obj.hide_set(not visible)
            except Exception:
                pass

    # La preview camera serve solo come oggetto tecnico: in vista anteprime
    # non deve comparire né produrre il suo riquadro/passepartout.
    if preview_cam:
        preview_cam.hide_viewport = True
        preview_cam.hide_render = True
        try:
            preview_cam.hide_set(True)
        except Exception:
            pass


def set_preview_isolation(context, enabled):
    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)
    preview_names = set(col.objects.keys()) if col else set()
    preview_cam = bpy.data.objects.get(PREVIEW_CAMERA_NAME)

    if preview_cam:
        preview_cam.hide_viewport = True
        preview_cam.hide_render = True
        try:
            preview_cam.hide_set(True)
        except Exception:
            pass

    if enabled:
        set_preview_visibility(context.scene, True)

        for obj in bpy.data.objects:
            is_preview = obj.name in preview_names

            if is_preview:
                obj.hide_viewport = False
                try:
                    obj.hide_set(False)
                except Exception:
                    pass
            else:
                if not obj.get("reframe360v33_hidden_for_preview"):
                    obj["reframe360v33_prev_hide_viewport"] = bool(obj.hide_viewport)
                    try:
                        obj["reframe360v33_prev_hide_set"] = bool(obj.hide_get())
                    except Exception:
                        obj["reframe360v33_prev_hide_set"] = False

                obj["reframe360v33_hidden_for_preview"] = True
                obj.hide_viewport = True
                try:
                    obj.hide_set(True)
                except Exception:
                    pass
    else:
        for obj in bpy.data.objects:
            if obj.get("reframe360v33_hidden_for_preview"):
                obj.hide_viewport = bool(obj.get("reframe360v33_prev_hide_viewport", False))
                try:
                    obj.hide_set(bool(obj.get("reframe360v33_prev_hide_set", False)))
                except Exception:
                    pass

                for k in ["reframe360v33_hidden_for_preview", "reframe360v33_prev_hide_viewport", "reframe360v33_prev_hide_set"]:
                    try:
                        del obj[k]
                    except Exception:
                        pass

        set_preview_visibility(context.scene, False)


def select_preview_objects():
    try:
        bpy.ops.object.select_all(action="DESELECT")
    except Exception:
        pass

    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)

    if not col:
        return

    first = None

    for obj in col.objects:
        obj.select_set(True)
        if first is None:
            first = obj

    if first:
        bpy.context.view_layer.objects.active = first


def set_preview_camera_to_fit(scene, total_width, total_height):
    cam = get_or_create_preview_camera(scene)

    aspect = scene.reframe360v33_render_width / max(1, scene.reframe360v33_render_height)

    cam.data.ortho_scale = max(
        total_height * 1.35,
        (total_width / max(0.1, aspect)) * 1.15,
    )

    scene.camera = cam


def generate_preview(scene, both=False):
    try:
        import numpy as np
    except Exception:
        raise RuntimeError("Numpy non disponibile in Blender")

    if not scene.reframe360v33_image_path or not os.path.exists(scene.reframe360v33_image_path):
        raise RuntimeError("Prima carica una foto 360")

    clear_preview_objects()

    preview_w = max(320, int(scene.reframe360v33_preview_width))
    aspect = max(0.1, scene.reframe360v33_render_width / max(1, scene.reframe360v33_render_height))
    preview_h = max(180, int(round(preview_w / aspect)))

    if both:
        # Layout richiesto: le due cilindriche nella riga superiore,
        # rettilineare sotto centrata. Così il confronto CIL/CLV è immediato.
        projections = [
            ("CYLINDRICAL", "CIL / CILINDRICA"),
            ("CYLINDRICAL_LEVEL", "CLV / CIL ORIZZONTE DIRITTO"),
            ("RECTILINEAR", "RET / RETTILINEARE"),
        ]
    else:
        projections = [
            (
                scene.reframe360v33_projection_mode,
                projection_code(scene.reframe360v33_projection_mode),
            )
        ]

    gap_x = 0.35
    gap_y = 0.62
    pw = 2.0 * (preview_w / max(1, preview_h))
    ph = 2.0
    n = len(projections)

    if n == 3:
        # Due cilindriche sopra, rettilineare sotto: confronto CIL/CLV più leggibile.
        positions = [
            (-(pw / 2.0 + gap_x / 2.0), ph / 2.0 + gap_y / 2.0),
            ((pw / 2.0 + gap_x / 2.0), ph / 2.0 + gap_y / 2.0),
            (0.0, -(ph / 2.0 + gap_y / 2.0)),
        ]
        total_w = 2.0 * pw + gap_x
        total_h = 2.0 * ph + gap_y + 0.35
    elif n == 2:
        positions = [
            (-(pw / 2.0 + gap_x / 2.0), 0.0),
            ((pw / 2.0 + gap_x / 2.0), 0.0),
        ]
        total_w = 2.0 * pw + gap_x
        total_h = ph + 0.35
    else:
        positions = [(0.0, 0.0)]
        total_w = pw
        total_h = ph + 0.35

    for idx, (proj, lab) in enumerate(projections):
        rgba = reproject_360_to_view_np(
            scene,
            np,
            width=preview_w,
            height=preview_h,
            projection_mode=proj,
            apply_lut=True,
        )

        path = save_preview_png_temp(scene, rgba, proj, np)
        x_pos, z_pos = positions[idx]

        make_preview_plane(
            "Reframe360_Preview_" + proj,
            path,
            x_pos,
            lab,
            z_offset=z_pos,
        )

    make_preview_background(total_w, total_h)
    set_preview_camera_to_fit(scene, total_w, total_h)
    select_preview_objects()

    scene.reframe360v33_last_preview_valid = True


def focus_previews(context):
    col = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)

    if not col or len(col.objects) == 0:
        raise RuntimeError("Nessuna anteprima da inquadrare")

    context.scene.reframe360v33_current_view = "PREVIEW"

    set_preview_isolation(context, True)
    select_preview_objects()
    set_preview_view_style(context)
    jump_to_preview_orthographic_view(context)


# ============================================================
# Risoluzione reale stimata
# ============================================================

def calculate_real_resolution(scene):
    src_w = int(scene.reframe360v33_source_width)
    src_h = int(scene.reframe360v33_source_height)

    if src_w <= 0 or src_h <= 0:
        return None

    out_w = max(1, int(scene.reframe360v33_render_width))
    out_h = max(1, int(scene.reframe360v33_render_height))
    aspect = out_w / out_h

    h_fov = max(1, min(179, scene.reframe360v33_fov))
    v_fov = calculate_vertical_fov_deg(scene, out_w, out_h)

    raw_w = src_w * h_fov / 360.0
    raw_h = src_h * v_fov / 180.0

    useful_w = int(math.floor(min(raw_w, raw_h * aspect)))
    useful_h = int(math.floor(useful_w / aspect))

    mult = max(0.5, min(1.5, scene.reframe360v33_realres_multiplier))

    useful_w = max(1, int(useful_w * mult))
    useful_h = max(1, int(useful_h * mult))

    useful_px = useful_w * useful_h

    return {
        "useful_w": useful_w,
        "useful_h": useful_h,
        "v_fov_deg": v_fov,
        "area_oversampling": (out_w * out_h) / useful_px if useful_px else 0,
    }


def estimate_source_density_resolution(scene):
    """
    Stima la massima risoluzione nativa utile per la stampa della specifica inquadratura.

    Metodo V035: campiona il quadro corrente, lo rimappa sulla foto equirettangolare,
    misura l'impronta complessiva in pixel sorgente e poi rispetta il rapporto larghezza/altezza
    scelto per l'export. Non usa più il percentile prudenziale della versione precedente.
    """
    src_w = int(scene.reframe360v33_source_width)
    src_h = int(scene.reframe360v33_source_height)

    if src_w <= 0 or src_h <= 0:
        return None

    try:
        import numpy as np
    except Exception:
        base = calculate_real_resolution(scene)
        if not base:
            return None
        return {
            "useful_w": int(base["useful_w"]),
            "useful_h": int(base["useful_h"]),
            "source_span_w": int(base["useful_w"]),
            "source_span_h": int(base["useful_h"]),
            "area_oversampling": 0,
            "method": "fallback senza numpy",
        }

    out_w = max(1, int(scene.reframe360v33_render_width))
    out_h = max(1, int(scene.reframe360v33_render_height))
    aspect = out_w / out_h

    projection = scene.reframe360v33_projection_mode
    yaw_deg = float(scene.reframe360v33_yaw)
    pitch_deg = float(scene.reframe360v33_pitch)
    roll_deg = float(scene.reframe360v33_roll)
    h_fov_deg = max(1.0, min(179.0, float(scene.reframe360v33_fov)))
    h_fov_rad = math.radians(h_fov_deg)
    v_fov_rad = math.radians(
        calculate_vertical_fov_deg(scene, width=out_w, height=out_h, projection=projection, fov=h_fov_deg)
    )

    nx = 181
    ny = max(61, int(round(nx / max(0.1, aspect))))
    ny = min(121, ny)

    x_norm = np.linspace(-1.0, 1.0, nx, dtype=np.float32)
    y_norm = np.linspace(-1.0, 1.0, ny, dtype=np.float32)
    vertical_scale = math.tan(v_fov_rad / 2.0)

    level_cyl = projection == "CYLINDRICAL_LEVEL"

    if level_cyl:
        yaw_rad = math.radians(yaw_deg)
        pitch_shift = math.tan(math.radians(max(-80.0, min(80.0, pitch_deg))))
        roll_rad = math.radians(roll_deg)
        cos_r = math.cos(roll_rad)
        sin_r = math.sin(roll_rad)

        forward_h = np.array([math.sin(yaw_rad), math.cos(yaw_rad), 0.0], dtype=np.float32)
        right_h = np.array([math.cos(yaw_rad), -math.sin(yaw_rad), 0.0], dtype=np.float32)
        up_h = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        x_grid = x_norm[None, :]
        y_grid = y_norm[:, None]
        xr = x_grid * cos_r - y_grid * sin_r
        yr = x_grid * sin_r + y_grid * cos_r
        theta = xr * (h_fov_rad / 2.0)
        yy = yr * vertical_scale + pitch_shift

        sin_t = np.sin(theta).astype(np.float32)
        cos_t = np.cos(theta).astype(np.float32)

        dirs = (
            cos_t[..., None] * forward_h[None, None, :]
            + sin_t[..., None] * right_h[None, None, :]
            + yy[..., None] * up_h[None, None, :]
        )
    else:
        forward, right, up = get_view_basis_np(yaw_deg, pitch_deg, roll_deg, np)

        if projection == "CYLINDRICAL":
            theta = x_norm * (h_fov_rad / 2.0)
            sin_base = np.sin(theta).astype(np.float32)
            cos_base = np.cos(theta).astype(np.float32)
            yy = (y_norm * vertical_scale)[:, None]
            dirs = (
                cos_base[None, :, None] * forward[None, None, :]
                + sin_base[None, :, None] * right[None, None, :]
                + yy[..., None] * up[None, None, :]
            )
        else:
            x_base = x_norm * math.tan(h_fov_rad / 2.0)
            y_base = y_norm * vertical_scale
            xx = x_base[None, :]
            yy = y_base[:, None]
            dirs = (
                forward[None, None, :]
                + xx[..., None] * right[None, None, :]
                + yy[..., None] * up[None, None, :]
            )

    dirs = dirs / np.maximum(np.linalg.norm(dirs, axis=2, keepdims=True), 1e-12)

    lon = np.arctan2(dirs[..., 1], dirs[..., 0])
    lat = np.arcsin(np.clip(dirs[..., 2], -1.0, 1.0))

    # Evita errori quando l'inquadratura attraversa il bordo ±180° dell'equirettangolare.
    lon_unwrapped = np.unwrap(lon, axis=1)
    lon_unwrapped = np.unwrap(lon_unwrapped, axis=0)

    finite = np.isfinite(lon_unwrapped) & np.isfinite(lat)
    if not np.any(finite):
        return calculate_real_resolution(scene)

    lon_vals = lon_unwrapped[finite]
    lat_vals = lat[finite]

    lon_span = float(np.max(lon_vals) - np.min(lon_vals))
    lat_span = float(np.max(lat_vals) - np.min(lat_vals))

    lon_span = max(1e-6, min(2.0 * math.pi, lon_span))
    lat_span = max(1e-6, min(math.pi, lat_span))

    source_span_w = int(math.ceil((lon_span / (2.0 * math.pi)) * src_w))
    source_span_h = int(math.ceil((lat_span / math.pi) * (src_h - 1)))

    # Mantiene il formato export corrente. La risoluzione finale non deve superare
    # né il dettaglio orizzontale né quello verticale realmente contenuto nell'impronta sorgente.
    useful_w = int(math.floor(min(source_span_w, source_span_h * aspect)))
    useful_h = int(math.floor(useful_w / aspect))

    mode = getattr(scene, "reframe360v33_printmax_mode", "BALANCED")
    if mode == "CONSERVATIVE":
        print_factor = 1.00
        method = "nativo conservativo"
    elif mode == "LARGE":
        print_factor = 1.80
        method = "grande stampa"
    else:
        print_factor = 1.35
        method = "equilibrato stampa"

    useful_w = int(round(useful_w * print_factor))
    useful_h = int(round(useful_h * print_factor))

    useful_w = max(320, min(50000, useful_w))
    useful_h = max(180, min(50000, useful_h))

    useful_px = useful_w * useful_h
    current_px = out_w * out_h

    return {
        "useful_w": useful_w,
        "useful_h": useful_h,
        "source_span_w": source_span_w,
        "source_span_h": source_span_h,
        "area_oversampling": current_px / useful_px if useful_px else 0,
        "method": method,
        "print_factor": print_factor,
    }


def print_quality_label(current_w, current_h, native_w, native_h):
    if native_w <= 0 or native_h <= 0:
        return "Qualità: non stimabile"
    ratio = (current_w * current_h) / max(1, native_w * native_h)
    if ratio <= 1.15:
        return "Qualità: nativa / molto buona"
    if ratio <= 2.25:
        return "Qualità: leggera interpolazione"
    if ratio <= 4.0:
        return "Qualità: interpolazione visibile"
    return "Qualità: forte interpolazione"


# ============================================================
# Callback
# ============================================================

def blender_runtime_data_available():
    """
    Blender usa _RestrictData durante installazione/abilitazione degli add-on.
    In quella fase bpy.data.objects/materials/images non è accessibile: se un
    update callback parte durante la registrazione, deve uscire senza toccare
    la scena.
    """
    try:
        _ = bpy.data.objects
        _ = bpy.data.materials
        _ = bpy.data.images
        return True
    except Exception:
        return False


def update_callback(self, context):
    if not context or not context.scene:
        return
    if not blender_runtime_data_available():
        return

    invalidate_preview(context.scene)
    update_camera(context.scene)
    update_camera_guides(context.scene)


def invalidate_callback(self, context):
    if not context or not context.scene:
        return
    if not blender_runtime_data_available():
        return

    invalidate_preview(context.scene)
    update_camera_guides(context.scene)


# ============================================================
# Operatori
# ============================================================

class REFRAME360_OT_load_image(Operator, ImportHelper):
    bl_idname = "reframe360.load_image"
    bl_label = "Carica foto 360"
    filename_ext = ""

    filter_glob: StringProperty(
        default="*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.exr;*.hdr",
        options={"HIDDEN"},
    )

    def execute(self, context):
        cleanup_old_visual_artifacts()
        s = context.scene
        setup_scene_for_reframe(s, self.filepath)
        set_preview_visibility(s, False)
        s.camera = get_or_create_camera(s)
        s.reframe360v33_current_view = "CAMERA"
        force_rendered_view(context)
        jump_to_camera_view(context)
        self.report({"INFO"}, "Foto 360 caricata: vista camera renderizzata aperta automaticamente")
        return {"FINISHED"}


class REFRAME360_OT_load_lut(Operator, ImportHelper):
    bl_idname = "reframe360.load_lut"
    bl_label = "Carica LUT .cube"
    filename_ext = ".cube"

    filter_glob: StringProperty(default="*.cube", options={"HIDDEN"})

    def execute(self, context):
        context.scene.reframe360v33_lut_path = self.filepath
        try:
            context.scene.reframe360v33_apply_lut = True
        except Exception:
            pass
        invalidate_preview(context.scene)

        try:
            parse_cube_lut(self.filepath)
        except Exception as e:
            self.report({"ERROR"}, f"LUT non valida: {e}")
            return {"CANCELLED"}

        self.report({"INFO"}, "LUT caricata: sarà applicata sempre ad anteprime ed export")
        return {"FINISHED"}


class REFRAME360_OT_reload_color_mode(Operator):
    bl_idname = "reframe360.reload_color_mode"
    bl_label = "Ricarica colore sorgente"

    def execute(self, context):
        s = context.scene

        if s.reframe360v33_image_path and os.path.exists(s.reframe360v33_image_path):
            setup_world_image(s, s.reframe360v33_image_path)
            invalidate_preview(s)
            update_camera(s)
            update_camera_guides(s)
            return {"FINISHED"}

        self.report({"ERROR"}, "Nessuna foto caricata")
        return {"CANCELLED"}


class REFRAME360_OT_toggle_projection(Operator):
    bl_idname = "reframe360.toggle_projection"
    bl_label = "Cambia RET/CIL/CLV"

    def execute(self, context):
        s = context.scene
        order = ["RECTILINEAR", "CYLINDRICAL", "CYLINDRICAL_LEVEL"]

        try:
            idx = order.index(s.reframe360v33_projection_mode)
        except ValueError:
            idx = 0

        s.reframe360v33_projection_mode = order[(idx + 1) % len(order)]
        update_callback(self, context)
        return {"FINISHED"}


class REFRAME360_OT_nudge(Operator):
    bl_idname = "reframe360.nudge"
    bl_label = "Muovi inquadratura"

    target: EnumProperty(
        items=[
            ("YAW", "Yaw", ""),
            ("PITCH", "Pitch", ""),
            ("ROLL", "Roll", ""),
            ("FOV", "FOV", ""),
        ]
    )

    amount: FloatProperty(default=0.0)

    def execute(self, context):
        s = context.scene

        if self.target == "YAW":
            s.reframe360v33_yaw += self.amount
        elif self.target == "PITCH":
            s.reframe360v33_pitch = max(-89, min(89, s.reframe360v33_pitch + self.amount))
        elif self.target == "ROLL":
            s.reframe360v33_roll += self.amount
        elif self.target == "FOV":
            s.reframe360v33_fov = max(10, min(150, s.reframe360v33_fov + self.amount))

        update_callback(self, context)

        return {"FINISHED"}


class REFRAME360_OT_orbit_view(Operator):
    bl_idname = "reframe360.orbit_view"
    bl_label = "Orbit / Inquadra"
    bl_description = "Trascina il mouse per orientare la vista. Esc/Right click annulla, Enter/Left click conferma. Rotella = FOV."
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    def invoke(self, context, event):
        s = context.scene
        self.start_mouse_x = event.mouse_x
        self.start_mouse_y = event.mouse_y
        self.start_yaw = float(s.reframe360v33_yaw)
        self.start_pitch = float(s.reframe360v33_pitch)
        self.start_roll = float(s.reframe360v33_roll)
        self.start_fov = float(s.reframe360v33_fov)
        context.window_manager.modal_handler_add(self)
        self.report({"INFO"}, "Orbit: trascina. Shift=fine, Ctrl=rapido, rotella=FOV, Esc=annulla.")
        return {"RUNNING_MODAL"}

    def _restore(self, context):
        s = context.scene
        s.reframe360v33_yaw = self.start_yaw
        s.reframe360v33_pitch = self.start_pitch
        s.reframe360v33_roll = self.start_roll
        s.reframe360v33_fov = self.start_fov
        update_callback(self, context)

    def modal(self, context, event):
        s = context.scene

        if event.type in {"ESC", "RIGHTMOUSE"}:
            self._restore(context)
            self.report({"INFO"}, "Orbit annullato")
            return {"CANCELLED"}

        if event.type in {"RET", "NUMPAD_ENTER", "LEFTMOUSE"} and event.value == "PRESS":
            self.report({"INFO"}, "Orbit confermato")
            return {"FINISHED"}

        if event.type == "WHEELUPMOUSE" and not s.reframe360v33_lock_fov:
            s.reframe360v33_fov = max(10, min(150, s.reframe360v33_fov - 2.0))
            update_callback(self, context)
            return {"RUNNING_MODAL"}

        if event.type == "WHEELDOWNMOUSE" and not s.reframe360v33_lock_fov:
            s.reframe360v33_fov = max(10, min(150, s.reframe360v33_fov + 2.0))
            update_callback(self, context)
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self.start_mouse_x
            dy = event.mouse_y - self.start_mouse_y

            speed = 1.0
            if event.shift:
                speed = 0.25
            elif event.ctrl:
                speed = 2.5

            mode = s.reframe360v33_orbit_mode
            yaw_delta = dx * 0.12 * speed
            pitch_delta = -dy * 0.09 * speed
            roll_delta = dx * 0.08 * speed
            fov_delta = dy * 0.06 * speed

            if mode == "FREE":
                if not s.reframe360v33_lock_yaw:
                    s.reframe360v33_yaw = self.start_yaw + yaw_delta
                if not s.reframe360v33_lock_pitch:
                    s.reframe360v33_pitch = max(-89, min(89, self.start_pitch + pitch_delta))
            elif mode == "YAW":
                if not s.reframe360v33_lock_yaw:
                    s.reframe360v33_yaw = self.start_yaw + yaw_delta
            elif mode == "PITCH":
                if not s.reframe360v33_lock_pitch:
                    s.reframe360v33_pitch = max(-89, min(89, self.start_pitch + pitch_delta))
            elif mode == "ROLL":
                if not s.reframe360v33_lock_roll:
                    s.reframe360v33_roll = self.start_roll + roll_delta
            elif mode == "FOV":
                if not s.reframe360v33_lock_fov:
                    s.reframe360v33_fov = max(10, min(150, self.start_fov + fov_delta))

            update_callback(self, context)
            force_rendered_view(context)
            return {"RUNNING_MODAL"}

        return {"RUNNING_MODAL"}


class REFRAME360_OT_reset_view(Operator):
    bl_idname = "reframe360.reset_view"
    bl_label = "Reset inquadratura"

    def execute(self, context):
        s = context.scene

        s.reframe360v33_yaw = 0
        s.reframe360v33_pitch = 0
        s.reframe360v33_roll = 0
        s.reframe360v33_fov = 75

        update_callback(self, context)

        return {"FINISHED"}


class REFRAME360_OT_open_camera_view(Operator):
    bl_idname = "reframe360.open_camera_view"
    bl_label = "Vista camera Rendered"

    def execute(self, context):
        set_preview_isolation(context, False)

        update_camera(context.scene)
        update_camera_guides(context.scene)

        context.scene.camera = get_or_create_camera(context.scene)
        context.scene.reframe360v33_current_view = "CAMERA"

        force_rendered_view(context)
        jump_to_camera_view(context)

        return {"FINISHED"}


class REFRAME360_OT_refresh_camera_guides(Operator):
    bl_idname = "reframe360.refresh_camera_guides"
    bl_label = "Aggiorna bordo CIL"

    def execute(self, context):
        update_camera(context.scene)
        update_camera_guides(context.scene)
        force_rendered_view(context)

        return {"FINISHED"}


class REFRAME360_OT_toggle_view(Operator):
    bl_idname = "reframe360.toggle_view"
    bl_label = "Cambia vista Camera / Anteprime"

    def execute(self, context):
        s = context.scene

        if s.reframe360v33_current_view != "PREVIEW":
            try:
                if not s.reframe360v33_last_preview_valid:
                    generate_preview(s, both=True)

                focus_previews(context)

            except Exception as e:
                self.report({"ERROR"}, f"Errore vista anteprime: {e}")
                return {"CANCELLED"}

        else:
            set_preview_isolation(context, False)

            update_camera(s)
            update_camera_guides(s)

            s.camera = get_or_create_camera(s)
            s.reframe360v33_current_view = "CAMERA"

            force_rendered_view(context)
            jump_to_camera_view(context)

        return {"FINISHED"}


class REFRAME360_OT_preview_active(Operator):
    bl_idname = "reframe360.preview_active"
    bl_label = "Anteprima proiezione attiva"

    def execute(self, context):
        try:
            generate_preview(context.scene, both=False)
            focus_previews(context)
        except Exception as e:
            self.report({"ERROR"}, f"Errore anteprima: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


class REFRAME360_OT_preview_both(Operator):
    bl_idname = "reframe360.preview_both"
    bl_label = "Anteprima RET + CIL"

    def execute(self, context):
        try:
            generate_preview(context.scene, both=True)
            focus_previews(context)
        except Exception as e:
            self.report({"ERROR"}, f"Errore anteprima: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


class REFRAME360_OT_focus_previews(Operator):
    bl_idname = "reframe360.focus_previews"
    bl_label = "Inquadra anteprime"

    def execute(self, context):
        try:
            focus_previews(context)
        except Exception as e:
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        return {"FINISHED"}


class REFRAME360_OT_clear_preview(Operator):
    bl_idname = "reframe360.clear_preview"
    bl_label = "Pulisci anteprime"

    def execute(self, context):
        clear_preview_objects()
        return {"FINISHED"}


class REFRAME360_OT_preset_4k(Operator):
    bl_idname = "reframe360.preset_4k"
    bl_label = "Preset 4K"

    def execute(self, context):
        s = context.scene

        s.reframe360v33_render_width = 3840
        s.reframe360v33_render_height = 2160

        invalidate_callback(self, context)

        return {"FINISHED"}


class REFRAME360_OT_preset_landscape_16_9(Operator):
    bl_idname = "reframe360.preset_landscape_16_9"
    bl_label = "Preset 6000 16:9"

    def execute(self, context):
        s = context.scene

        s.reframe360v33_render_width = 6000
        s.reframe360v33_render_height = 3375

        invalidate_callback(self, context)

        return {"FINISHED"}


class REFRAME360_OT_preset_a3_3_2(Operator):
    bl_idname = "reframe360.preset_a3_3_2"
    bl_label = "Preset 5400 3:2"

    def execute(self, context):
        s = context.scene

        s.reframe360v33_render_width = 5400
        s.reframe360v33_render_height = 3600

        invalidate_callback(self, context)

        return {"FINISHED"}


class REFRAME360_OT_apply_realres(Operator):
    bl_idname = "reframe360.apply_realres"
    bl_label = "Applica max reale"

    def execute(self, context):
        s = context.scene
        est = calculate_real_resolution(s)

        if est is None:
            self.report({"ERROR"}, "Carica prima una foto 360")
            return {"CANCELLED"}

        s.reframe360v33_render_width = int(est["useful_w"])
        s.reframe360v33_render_height = int(est["useful_h"])

        s.render.resolution_x = s.reframe360v33_render_width
        s.render.resolution_y = s.reframe360v33_render_height

        s.reframe360v33_last_preview_valid = False

        update_camera(s)
        update_camera_guides(s)

        if s.reframe360v33_current_view == "PREVIEW":
            try:
                generate_preview(s, both=True)
                focus_previews(context)
            except Exception as e:
                self.report({"WARNING"}, f"Risoluzione aggiornata, ma anteprime non rigenerate: {e}")
        else:
            force_rendered_view(context)

        self.report(
            {"INFO"},
            f"Risoluzione aggiornata: {s.reframe360v33_render_width} x {s.reframe360v33_render_height}",
        )

        return {"FINISHED"}


class REFRAME360_OT_apply_printmax(Operator):
    bl_idname = "reframe360.apply_printmax"
    bl_label = "Applica max stampa inquadratura"

    def execute(self, context):
        s = context.scene
        est = estimate_source_density_resolution(s)

        if est is None:
            self.report({"ERROR"}, "Carica prima una foto 360")
            return {"CANCELLED"}

        s.reframe360v33_render_width = int(est["useful_w"])
        s.reframe360v33_render_height = int(est["useful_h"])

        s.render.resolution_x = s.reframe360v33_render_width
        s.render.resolution_y = s.reframe360v33_render_height

        s.reframe360v33_last_preview_valid = False

        update_camera(s)
        update_camera_guides(s)

        if s.reframe360v33_current_view == "PREVIEW":
            try:
                generate_preview(s, both=True)
                focus_previews(context)
            except Exception as e:
                self.report({"WARNING"}, f"Risoluzione aggiornata, ma anteprime non rigenerate: {e}")
        else:
            force_rendered_view(context)

        self.report(
            {"INFO"},
            f"Max stampa applicato: {s.reframe360v33_render_width} x {s.reframe360v33_render_height} px",
        )

        return {"FINISHED"}


class REFRAME360_OT_render_save(Operator, ExportHelper):
    bl_idname = "reframe360.render_save"
    bl_label = "Export + salva"
    filename_ext = ""

    filter_glob: StringProperty(default="*.png;*.tif;*.tiff;*.jpg;*.jpeg", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = get_suggested_export_filepath(context.scene)
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}

    def execute(self, context):
        s = context.scene

        if not s.reframe360v33_image_path or not os.path.exists(s.reframe360v33_image_path):
            self.report({"ERROR"}, "Prima carica una foto 360")
            return {"CANCELLED"}

        setup_world_image(s, s.reframe360v33_image_path)
        update_camera(s)
        update_camera_guides(s)

        try:
            saved_path = export_reframed_image(s, self.filepath)
        except Exception as e:
            self.report({"ERROR"}, f"Errore export: {e}")
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"Export salvato: {saved_path}",
        )

        return {"FINISHED"}


# ============================================================
# Interfaccia
# ============================================================

class REFRAME360_PT_panel(Panel):
    bl_label = "Blender360Photolab V035"
    bl_idname = "REFRAME360_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Foto 360"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # 1. Sorgente
        box = layout.box()
        box.label(text="1. Sorgente")
        box.operator("reframe360.load_image", text="Carica foto 360")
        box.operator("reframe360.load_lut", text="Carica LUT .cube")

        if s.reframe360v33_image_path:
            box.label(text=os.path.basename(s.reframe360v33_image_path))
        if s.reframe360v33_lut_path:
            box.label(text=os.path.basename(s.reframe360v33_lut_path))
        if s.reframe360v33_source_width > 0:
            row = box.row()
            row.scale_y = 0.65
            row.label(text=f"{s.reframe360v33_source_width} x {s.reframe360v33_source_height} px")

        # 2. Vista
        box = layout.box()
        box.label(text="2. Vista")
        box.operator("reframe360.toggle_view", text="Cambia vista Camera / Anteprime")
        box.label(text=f"Vista corrente: {s.reframe360v33_current_view}")
        row = box.row(align=True)
        row.operator("reframe360.preview_both", text="Rigenera anteprime")
        row.operator("reframe360.clear_preview", text="Pulisci")

        # 3. Inquadratura
        box = layout.box()
        box.label(text="3. Inquadratura")
        box.operator("reframe360.orbit_view", text="ORBIT / INQUADRA")
        box.prop(s, "reframe360v33_orbit_mode", text="Modalità")

        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(s, "reframe360v33_lock_yaw", text="Blocca yaw")
        row.prop(s, "reframe360v33_lock_pitch", text="Blocca pitch")
        row = col.row(align=True)
        row.prop(s, "reframe360v33_lock_roll", text="Blocca roll")
        row.prop(s, "reframe360v33_lock_fov", text="Blocca FOV")

        box.separator()
        box.label(text="Regolazioni fini")
        for a, b, t in [
            (-15, 15, "YAW"),
            (-1, 1, "YAW"),
            (-10, 10, "PITCH"),
            (-1, 1, "ROLL"),
            (-5, 5, "FOV"),
        ]:
            row = box.row(align=True)
            op = row.operator("reframe360.nudge", text=f"{t} {a:+g}")
            op.target = t
            op.amount = a
            op = row.operator("reframe360.nudge", text=f"{t} {b:+g}")
            op.target = t
            op.amount = b

        box.prop(s, "reframe360v33_yaw")
        pitch_label = "Shift verticale" if s.reframe360v33_projection_mode == "CYLINDRICAL_LEVEL" else "Pitch"
        box.prop(s, "reframe360v33_pitch", text=pitch_label)
        box.prop(s, "reframe360v33_roll")
        box.prop(s, "reframe360v33_fov")
        box.operator("reframe360.reset_view", text="Reset inquadratura")

        # 4. Proiezione
        box = layout.box()
        box.label(text="4. Proiezione")
        box.prop(s, "reframe360v33_projection_mode", text="")
        box.operator("reframe360.toggle_projection", text="Cambia RET/CIL/CLV")
        box.prop(s, "reframe360v33_show_cil_guide", text="Mostra bordo CIL/CLV")
        box.label(text=f"{projection_code(s.reframe360v33_projection_mode)} / {projection_label(s.reframe360v33_projection_mode)}")

        # 5. Risoluzione e stampa
        box = layout.box()
        box.label(text="5. Risoluzione e stampa")
        row = box.row(align=True)
        row.operator("reframe360.preset_4k", text="4K")
        row.operator("reframe360.preset_landscape_16_9", text="6000 16:9")
        row.operator("reframe360.preset_a3_3_2", text="5400 3:2")
        box.prop(s, "reframe360v33_render_width")
        box.prop(s, "reframe360v33_render_height")

        box.separator()
        box.label(text="Stampa teorica export corrente:")
        box.label(text=f"150 DPI: {format_print_size_cm(s.reframe360v33_render_width, s.reframe360v33_render_height, 150)}")
        box.label(text=f"300 DPI: {format_print_size_cm(s.reframe360v33_render_width, s.reframe360v33_render_height, 300)}")

        est = calculate_real_resolution(s)
        print_est = estimate_source_density_resolution(s)
        if est:
            box.separator()
            box.label(text=f"Max nativo base: {est['useful_w']} x {est['useful_h']} px")
        else:
            box.separator()
            box.label(text="Carica una foto 360 per stimare.")
        box.operator("reframe360.apply_realres", text="Usa risoluzione max reale")

        box.separator()
        box.prop(s, "reframe360v33_printmax_mode", text="Metodo stampa")
        if print_est:
            box.label(text=f"Max stampa inquadratura: {print_est['useful_w']} x {print_est['useful_h']} px")
            box.label(text=print_quality_label(s.reframe360v33_render_width, s.reframe360v33_render_height, print_est['useful_w'], print_est['useful_h']))
            box.label(text=f"150 DPI: {format_print_size_cm(print_est['useful_w'], print_est['useful_h'], 150)}")
            box.label(text=f"300 DPI: {format_print_size_cm(print_est['useful_w'], print_est['useful_h'], 300)}")
        box.operator("reframe360.apply_printmax", text="Usa max stampa da inquadratura")

        # 6. Export finale
        box = layout.box()
        box.label(text="6. Export")
        box.prop(s, "reframe360v33_export_format", text="Formato")
        box.label(text=export_format_technical_note(s.reframe360v33_export_format))
        if s.reframe360v33_export_format == "JPEG":
            box.prop(s, "reframe360v33_jpeg_quality", text="Qualità JPEG")
        box.prop(s, "reframe360v33_lut_strength", slider=True)
        box.operator("reframe360.render_save", text=f"Export {export_format_short_label(s.reframe360v33_export_format)} + salva")



# ============================================================
# Register
# ============================================================

classes = (
    REFRAME360_OT_load_image,
    REFRAME360_OT_load_lut,
    REFRAME360_OT_reload_color_mode,
    REFRAME360_OT_toggle_projection,
    REFRAME360_OT_nudge,
    REFRAME360_OT_orbit_view,
    REFRAME360_OT_reset_view,
    REFRAME360_OT_open_camera_view,
    REFRAME360_OT_refresh_camera_guides,
    REFRAME360_OT_toggle_view,
    REFRAME360_OT_preview_active,
    REFRAME360_OT_preview_both,
    REFRAME360_OT_focus_previews,
    REFRAME360_OT_clear_preview,
    REFRAME360_OT_preset_4k,
    REFRAME360_OT_preset_landscape_16_9,
    REFRAME360_OT_preset_a3_3_2,
    REFRAME360_OT_apply_realres,
    REFRAME360_OT_apply_printmax,
    REFRAME360_OT_render_save,
    REFRAME360_PT_panel,
)


def register_props():
    bpy.types.Scene.reframe360v33_image_path = StringProperty(
        name="Foto 360",
        default="",
    )

    bpy.types.Scene.reframe360v33_lut_path = StringProperty(
        name="LUT .cube",
        default="",
    )

    bpy.types.Scene.reframe360v33_source_width = IntProperty(default=0)
    bpy.types.Scene.reframe360v33_source_height = IntProperty(default=0)

    bpy.types.Scene.reframe360v33_source_is_log = BoolProperty(
        default=False,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_projection_mode = EnumProperty(
        items=[
            ("RECTILINEAR", "Rettilineare", ""),
            ("CYLINDRICAL", "Cilindrica", ""),
            ("CYLINDRICAL_LEVEL", "Cilindrica orizzonte diritto", "Pitch come shift verticale: riduce la curvatura dell'orizzonte"),
        ],
        default="RECTILINEAR",
        update=update_callback,
    )

    bpy.types.Scene.reframe360v33_show_cil_guide = BoolProperty(
        default=True,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_yaw = FloatProperty(
        name="Yaw",
        default=0,
        update=update_callback,
    )

    bpy.types.Scene.reframe360v33_pitch = FloatProperty(
        name="Pitch",
        default=0,
        min=-89,
        max=89,
        update=update_callback,
    )

    bpy.types.Scene.reframe360v33_roll = FloatProperty(
        name="Roll",
        default=0,
        update=update_callback,
    )

    bpy.types.Scene.reframe360v33_fov = FloatProperty(
        name="FOV orizzontale",
        default=75,
        min=10,
        max=150,
        update=update_callback,
    )

    bpy.types.Scene.reframe360v33_render_width = IntProperty(
        name="Larghezza px",
        default=6000,
        min=320,
        max=50000,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_render_height = IntProperty(
        name="Altezza px",
        default=3375,
        min=240,
        max=50000,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_realres_multiplier = FloatProperty(
        default=1.0,
        min=0.5,
        max=1.5,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_apply_lut = BoolProperty(
        default=False,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_lut_strength = FloatProperty(
        default=1.0,
        min=0,
        max=1,
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_preview_width = IntProperty(
        default=1200,
        min=320,
        max=4000,
    )

    bpy.types.Scene.reframe360v33_orbit_mode = EnumProperty(
        name="Orbit",
        items=[
            ("FREE", "Libero", "Yaw + Pitch"),
            ("YAW", "Solo orizzontale", "Modifica solo yaw"),
            ("PITCH", "Solo verticale", "Modifica solo pitch/shift verticale"),
            ("ROLL", "Solo roll", "Livella o inclina l'orizzonte"),
            ("FOV", "Solo zoom/FOV", "Modifica solo FOV"),
        ],
        default="FREE",
    )

    bpy.types.Scene.reframe360v33_lock_yaw = BoolProperty(default=False)
    bpy.types.Scene.reframe360v33_lock_pitch = BoolProperty(default=False)
    bpy.types.Scene.reframe360v33_lock_roll = BoolProperty(default=False)
    bpy.types.Scene.reframe360v33_lock_fov = BoolProperty(default=False)

    bpy.types.Scene.reframe360v33_printmax_mode = EnumProperty(
        name="Max stampa",
        items=[
            ("CONSERVATIVE", "Conservativa", "Nessuna interpolazione significativa"),
            ("BALANCED", "Equilibrata", "Stampa grande con interpolazione moderata"),
            ("LARGE", "Grande stampa", "Massimizza la stampa accettando upscaling più forte"),
        ],
        default="BALANCED",
        update=invalidate_callback,
    )

    bpy.types.Scene.reframe360v33_export_format = EnumProperty(
        name="Formato export",
        items=[
            ("PNG8", "PNG 8 bit lossless", "Formato default: senza perdita, molto compatibile"),
            ("TIFF16", "TIFF 16 bit lossless", "Master stampa/editing: senza perdita, non compresso"),
            ("JPEG", "JPEG qualità alta", "Formato lossy per file leggeri e condivisione"),
        ],
        default="PNG8",
    )

    bpy.types.Scene.reframe360v33_jpeg_quality = IntProperty(
        name="Qualità JPEG",
        default=95,
        min=1,
        max=100,
    )

    bpy.types.Scene.reframe360v33_last_preview_valid = BoolProperty(
        default=False,
    )

    bpy.types.Scene.reframe360v33_current_view = EnumProperty(
        items=[
            ("CAMERA", "Camera", ""),
            ("PREVIEW", "Anteprime", ""),
        ],
        default="CAMERA",
    )


def register():
    unregister_old_classes_and_props()

    # V035: non chiamare cleanup_old_visual_artifacts() durante register().
    # Quando Blender abilita un add-on da Preferences usa _RestrictData:
    # in quella fase bpy.data.objects/materials/images non è accessibile.
    # La pulizia degli artefatti viene eseguita dalle operazioni normali
    # dell'add-on, quando il contesto Blender è pienamente disponibile.

    for cls in classes:
        bpy.utils.register_class(cls)

    register_props()


def unregister():
    unregister_props()

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    unregister_props()


if __name__ == "__main__":
    register()
