import logging
import math
import os

from enum import Enum
import bpy
from bpy.types import Operator

from .helper import (ADDON_ID, auto_offset,
                     get_projectors, get_projector, random_color)

logging.basicConfig(
    format='[Projectors Addon]: %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(name=__file__)


class Textures(Enum):
    CHECKER = 'checker_texture'
    COLOR_GRID = 'color_grid_texture'
    CUSTOM_TEXTURE = 'custom_texture'


RESOLUTIONS = [
    # 16:10 aspect ratio
    ('1280x800', 'WXGA (1280x800) 16:10', '', 1),
    ('1440x900', 'WXGA+ (1440x900) 16:10', '', 2),
    ('1920x1200', 'WUXGA (1920x1200) 16:10', '', 3),
    # 16:9 aspect ratio
    ('1280x720', '720p (1280x720) 16:9', '', 4),
    ('1920x1080', '1080p (1920x1080) 16:9', '', 5),
    ('3840x2160', '4K Ultra HD (3840x2160) 16:9', '', 6),
    # 4:3 aspect ratio
    ('800x600', 'SVGA (800x600) 4:3', '', 7),
    ('1024x768', 'XGA (1024x768) 4:3', '', 8),
    ('1400x1050', 'SXGA+ (1400x1050) 4:3', '', 9),
    ('1600x1200', 'UXGA (1600x1200) 4:3', '', 10),
    # 17:9 aspect ratio
    ('4096x2160', 'Native 4K (4096x2160) 17:9', '', 11),
    # 1:1 aspect ratio
    ('1000x1000', 'Square (1000x1000) 1:1', '', 12)
]

PROJECTED_OUTPUTS = [(Textures.CHECKER.value, 'Checker', '', 1),
                     (Textures.COLOR_GRID.value, 'Color Grid', '', 2),
                     (Textures.CUSTOM_TEXTURE.value, 'Custom Texture', '', 3)]


class PROJECTOR_OT_change_color_randomly(Operator):
    """ Randomly change the color of the projected checker texture."""
    bl_idname = 'projector.change_color'
    bl_label = 'Change color of projection checker texture'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(get_projectors(context, only_selected=True)) == 1

    def execute(self, context):
        projectors = get_projectors(context, only_selected=True)
        new_color = random_color(alpha=True)
        for projector in projectors:
            projector.proj_settings['projected_color'] = new_color[:-1]
            update_checker_color(projector.proj_settings, context)
        return {'FINISHED'}


def create_projector_textures():
    """ This function checks if the needed images exist and if not creates them. """
    name_template = '_proj.tex.{}'
    for res in RESOLUTIONS:
        img_name = name_template.format(res[0])
        w, h = res[0].split('x')
        if not bpy.data.images.get(img_name):
            log.debug(f'Create projection texture: {res}')
            bpy.ops.image.new(name=img_name,
                              width=int(w),
                              height=int(h),
                              color=(0.0, 0.0, 0.0, 1.0),
                              alpha=True,
                              generated_type='COLOR_GRID',
                              float=False)

        bpy.data.images[img_name].use_fake_user = True


def add_projector_node_tree_to_spot(spot):
    """
    This function turns a spot light into a projector.
    This is achieved through a texture on the spot light and some basic math.
    """

    spot.data.use_nodes = True
    root_tree = spot.data.node_tree
    root_tree.nodes.clear()

    node_group = bpy.data.node_groups.new('_Projector', 'ShaderNodeTree')

    # Create output sockets for the node group.
    if(bpy.app.version >= (4, 0)):
        node_group.interface.new_socket('texture vector',  in_out="OUTPUT", socket_type='NodeSocketVector')
        node_group.interface.new_socket('color', in_out="OUTPUT", socket_type='NodeSocketColor')
    else:
        output = node_group.outputs
        output.new('NodeSocketVector', 'texture vector')
        output.new('NodeSocketColor', 'color')

    # # Inside Group Node #
    # #####################

    # Hold important nodes inside a group node.
    group = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    group.node_tree = node_group
    group.label = "!! Don't touch !!"

    nodes = group.node_tree.nodes
    tree = group.node_tree

    auto_pos = auto_offset()

    tex = nodes.new('ShaderNodeTexCoord')
    tex.location = auto_pos(200)

    geo = nodes.new('ShaderNodeNewGeometry')
    geo.location = auto_pos(0, -300)
    vec_transform = nodes.new('ShaderNodeVectorTransform')
    vec_transform.location = auto_pos(200)
    vec_transform.vector_type = 'NORMAL'

    map_1 = nodes.new('ShaderNodeMapping')
    map_1.vector_type = 'TEXTURE'
    # Flip the image horizontally and vertically to display it the intended way.
    if bpy.app.version < (2, 81):
        map_1.scale[0] = -1
        map_1.scale[1] = -1
    else:
        map_1.inputs[3].default_value[0] = -1
        map_1.inputs[3].default_value[1] = -1
    map_1.location = auto_pos(200)

    sep = nodes.new('ShaderNodeSeparateXYZ')
    sep.location = auto_pos(350)

    div_1 = nodes.new('ShaderNodeMath')
    div_1.operation = 'DIVIDE'
    div_1.name = ADDON_ID + 'div_01'
    div_1.location = auto_pos(200)

    div_2 = nodes.new('ShaderNodeMath')
    div_2.operation = 'DIVIDE'
    div_2.name = ADDON_ID + 'div_02'
    div_2.location = auto_pos(y=-200)

    com = nodes.new('ShaderNodeCombineXYZ')
    com.inputs['Z'].default_value = 1.0
    com.location = auto_pos(200)

    map_2 = nodes.new('ShaderNodeMapping')
    map_2.location = auto_pos(200)
    map_2.vector_type = 'TEXTURE'

    add = nodes.new('ShaderNodeMixRGB')
    add.blend_type = 'ADD'
    add.inputs[0].default_value = 1
    add.location = auto_pos(350)

    # Texture
    # a) Image
    img = nodes.new('ShaderNodeTexImage')
    img.extension = 'CLIP'
    img.location = auto_pos(200)

    # b) Generated checker texture.
    checker_tex = nodes.new('ShaderNodeTexChecker')
    # checker_tex.inputs['Color2'].default_value = random_color(alpha=True)
    checker_tex.inputs[3].default_value = 8
    checker_tex.inputs[1].default_value = (1, 1, 1, 1)
    checker_tex.location = auto_pos(y=-300)

    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.name = 'Mix.001'
    mix_rgb.inputs[1].default_value = (0, 0, 0, 0)
    mix_rgb.location = auto_pos(200, y=-300)

    group_output_node = node_group.nodes.new('NodeGroupOutput')
    group_output_node.location = auto_pos(200)

    # # Root Nodes #
    # ##############
    auto_pos_root = auto_offset()
    # Image Texture
    user_texture = root_tree.nodes.new('ShaderNodeTexImage')
    user_texture.extension = 'CLIP'
    user_texture.label = 'Add your Image Texture or Movie here'
    user_texture.location = auto_pos_root(200, y=200)
    # Emission
    emission = root_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value = 1
    emission.location = auto_pos_root(300)
    # Material Output
    output = root_tree.nodes.new('ShaderNodeOutputLight')
    output.location = auto_pos_root(200)

    # # LINK NODES #
    # ##############

    # Link inside group node
    if(bpy.app.version >= (4, 0)):
        tree.links.new(geo.outputs['Incoming'], vec_transform.inputs['Vector'])
        tree.links.new(vec_transform.outputs['Vector'], map_1.inputs['Vector'])
    else:
        tree.links.new(tex.outputs['Normal'], map_1.inputs['Vector'])
    tree.links.new(map_1.outputs['Vector'], sep.inputs['Vector'])

    tree.links.new(sep.outputs[0], div_1.inputs[0])  # X -> value0
    tree.links.new(sep.outputs[2], div_1.inputs[1])  # Z -> value1
    tree.links.new(sep.outputs[1], div_2.inputs[0])  # Y -> value0
    tree.links.new(sep.outputs[2], div_2.inputs[1])  # Z -> value1

    tree.links.new(div_1.outputs[0], com.inputs[0])
    tree.links.new(div_2.outputs[0], com.inputs[1])

    tree.links.new(com.outputs['Vector'], map_2.inputs['Vector'])

    # Textures
    # a) generated texture
    tree.links.new(map_2.outputs['Vector'], add.inputs['Color1'])
    tree.links.new(add.outputs['Color'], img.inputs['Vector'])
    tree.links.new(add.outputs['Color'], group_output_node.inputs[0])
    # b) checker texture
    tree.links.new(add.outputs['Color'], checker_tex.inputs['Vector'])
    tree.links.new(img.outputs['Alpha'], mix_rgb.inputs[0])
    tree.links.new(checker_tex.outputs['Color'], mix_rgb.inputs[2])

    # Link in root
    root_tree.links.new(group.outputs['texture vector'], user_texture.inputs['Vector'])
    root_tree.links.new(group.outputs['color'], emission.inputs['Color'])
    root_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

    # Pixel Grid Setup
    pixel_grid_group = create_pixel_grid_node_group()
    pixel_grid_node = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    pixel_grid_node.node_tree = pixel_grid_group
    pixel_grid_node.label = "Pixel Grid"
    pixel_grid_node.name = 'pixel_grid'
    loc = root_tree.nodes['Emission'].location
    pixel_grid_node.location = (loc[0], loc[1] - 150)

    root_tree.links.new(group.outputs[0], pixel_grid_node.inputs[1])
    root_tree.links.new(emission.outputs[0], pixel_grid_node.inputs[0])

def get_resolution(proj_settings, context):
    """ Find out what resolution is currently used and return it.
    Resolution from the dropdown or the resolution from the custom texture.
    """
    if proj_settings.use_custom_texture_res and proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
        projector = get_projector(context)
        if not projector or not hasattr(projector, "children") or len(projector.children) == 0:
            return float(1920), float(1080)  # 기본값 반환
            
        root_tree = projector.children[0].data.node_tree
        if not root_tree:
            return float(1920), float(1080)  # 기본값 반환
            
        image_node = root_tree.nodes.get('Image Texture')
        if not image_node or not image_node.image:
            return float(1920), float(1080)  # 기본값 반환
            
        # 이미지 해상도 직접 접근
        w = image_node.image.size[0]
        h = image_node.image.size[1]
        
        # 유효한 해상도 확인
        if w <= 0 or h <= 0:
            return float(1920), float(1080)  # 기본값 반환
    else:
        w, h = proj_settings.resolution.split('x')

    return float(w), float(h)


def update_throw_ratio(proj_settings, context):
    """
    Adjust some settings on a camera to achieve a throw ratio
    """
    # 무한 재귀 방지 플래그 추가
    if getattr(update_throw_ratio, '_is_updating', False):
        return
    
    update_throw_ratio._is_updating = True
    
    try:
        projector = get_projector(context)
        if not projector:
            return
        
        # 렌즈 제한 확인 및 적용
        min_throw = projector.get("throw_ratio_min", None)
        max_throw = projector.get("throw_ratio_max", None)
        
        # 제한 값이 있고, 현재 값이 범위를 벗어나면 조정
        if min_throw is not None and max_throw is not None:
            if proj_settings.throw_ratio < min_throw:
                proj_settings["throw_ratio"] = min_throw  # 직접 값 설정으로 재귀 방지
            elif proj_settings.throw_ratio > max_throw:
                proj_settings["throw_ratio"] = max_throw  # 직접 값 설정으로 재귀 방지
        
        # 기존 코드 유지
        throw_ratio = proj_settings.get('throw_ratio')
        distance = 1
        alpha = math.atan((distance/throw_ratio)*.5) * 2
        projector.data.lens_unit = 'FOV'
        projector.data.angle = alpha
        projector.data.sensor_width = 10
        projector.data.display_size = 1

        # Adjust Texture to fit new camera ###
        w, h = get_resolution(proj_settings, context)
        aspect_ratio = w/h
        inverted_aspect_ratio = 1/aspect_ratio

        # Projected Texture
        # 직접 호출 대신 안전 검사 추가
        if not getattr(update_projected_texture, '_is_updating', False):
            update_projected_texture(proj_settings, context)

        # 스포트라이트 노드 업데이트
        try:
            # 자식 객체 확인 안전하게 수행
            spot = None
            if hasattr(projector, "children") and len(projector.children) > 0:
                spot = projector.children[0]
                
            if spot and hasattr(spot.data, "node_tree"):
                nodes = spot.data.node_tree.nodes.get('Group')
                if nodes and hasattr(nodes, "node_tree") and hasattr(nodes.node_tree, "nodes"):
                    mapping_node = nodes.node_tree.nodes.get('Mapping.001')
                    if mapping_node:
                        if bpy.app.version < (2, 81):
                            mapping_node.scale[0] = 1 / throw_ratio
                            mapping_node.scale[1] = 1 / throw_ratio * inverted_aspect_ratio
                        else:
                            mapping_node.inputs[3].default_value[0] = 1 / throw_ratio
                            mapping_node.inputs[3].default_value[1] = 1 / throw_ratio * inverted_aspect_ratio
        except Exception as e:
            print(f"Error updating spotlight nodes: {e}")

        # 렌즈 시프트 업데이트 (무한 재귀 방지 검사 추가)
        if not getattr(update_lens_shift, '_is_updating', False):
            update_lens_shift(proj_settings, context)
    finally:
        # 플래그 해제
        update_throw_ratio._is_updating = False

def update_lens_shift(proj_settings, context):
    """
    Apply the shift to the camera and texture.
    """
    # 무한 재귀 방지 플래그
    if getattr(update_lens_shift, '_is_updating', False):
        return
    
    update_lens_shift._is_updating = True
    
    try:
        projector = get_projector(context)
        if not projector:
            return
        
        # 렌즈 제한 확인 및 적용
        h_min = projector.get("h_shift_min", None)
        h_max = projector.get("h_shift_max", None)
        v_min = projector.get("v_shift_min", None)
        v_max = projector.get("v_shift_max", None)
        
        # 현재 시프트 값 가져오기
        h_shift = proj_settings.h_shift
        v_shift = proj_settings.v_shift
        
        # 값 변경 여부 플래그
        values_changed = False
        
        # 수평 시프트 제한 적용
        if h_min is not None and h_max is not None:
            if h_shift < h_min:
                h_shift = h_min
                # 직접 프로퍼티 값 설정 (콜백 호출 방지)
                proj_settings["h_shift"] = h_min
                values_changed = True
            elif h_shift > h_max:
                h_shift = h_max
                proj_settings["h_shift"] = h_max
                values_changed = True
        
        # 수직 시프트 제한 적용
        if v_min is not None and v_max is not None:
            if v_shift < v_min:
                v_shift = v_min
                proj_settings["v_shift"] = v_min
                values_changed = True
            elif v_shift > v_max:
                v_shift = v_max
                proj_settings["v_shift"] = v_max
                values_changed = True
        
            
        # 나머지 계산을 위해 값을 백분율로 변환 (%)
        h_shift_normalized = h_shift / 100
        v_shift_normalized = v_shift / 100
        throw_ratio = proj_settings.get('throw_ratio')

        w, h = get_resolution(proj_settings, context)
        inverted_aspect_ratio = h/w

        # 카메라 속성 업데이트
        cam = projector
        if cam and hasattr(cam, "data"):
            cam.data.shift_x = h_shift_normalized
            cam.data.shift_y = v_shift_normalized * inverted_aspect_ratio

        # 스포트라이트 노드 설정 업데이트 - 안전 검사 추가
        try:
            if hasattr(projector, "children") and len(projector.children) > 0:
                spot = projector.children[0]
                if spot and hasattr(spot.data, "node_tree"):
                    nodes = spot.data.node_tree.nodes.get('Group')
                    if nodes and hasattr(nodes, "node_tree") and hasattr(nodes.node_tree, "nodes"):
                        mapping_node = nodes.node_tree.nodes.get('Mapping.001')
                        if mapping_node:
                            if bpy.app.version < (2, 81):
                                mapping_node.translation[0] = h_shift_normalized / throw_ratio
                                mapping_node.translation[1] = v_shift_normalized / throw_ratio * inverted_aspect_ratio
                            else:
                                mapping_node.inputs[1].default_value[0] = h_shift_normalized / throw_ratio
                                mapping_node.inputs[1].default_value[1] = v_shift_normalized / throw_ratio * inverted_aspect_ratio
        except Exception as e:
            print(f"Error updating spotlight nodes for lens shift: {e}")
    finally:
        # 플래그 해제
        update_lens_shift._is_updating = False


def update_resolution(proj_settings, context):
    projector = get_projector(context)
    nodes = projector.children[0].data.node_tree.nodes['Group'].node_tree.nodes
    # Change resolution image texture
    nodes['Image Texture'].image = bpy.data.images[f'_proj.tex.{proj_settings.resolution}']
    update_throw_ratio(proj_settings, context)
    update_pixel_grid(proj_settings, context)


def update_checker_color(proj_settings, context):
    # Update checker texture color
    nodes = get_projector(
        context).children[0].data.node_tree.nodes['Group'].node_tree.nodes
    c = proj_settings.projected_color
    nodes['Checker Texture'].inputs['Color2'].default_value = [c.r, c.g, c.b, 1]


def update_power(proj_settings, context):
    # Update spotlight power
    spot = get_projector(context).children[0]
    spot.data.energy = proj_settings["power"]


def update_pixel_grid(proj_settings, context):
    """ Update the pixel grid. Meaning, make it visible by linking the right node and updating the resolution. """
    root_tree = get_projector(context).children[0].data.node_tree
    nodes = root_tree.nodes
    pixel_grid_nodes = nodes['pixel_grid'].node_tree.nodes
    width, height = get_resolution(proj_settings, context)
    pixel_grid_nodes['_width'].outputs[0].default_value = width
    pixel_grid_nodes['_height'].outputs[0].default_value = height
    if proj_settings.show_pixel_grid:
        root_tree.links.new(nodes['pixel_grid'].outputs[0], nodes['Light Output'].inputs[0])
    else:
        root_tree.links.new(nodes['Emission'].outputs[0], nodes['Light Output'].inputs[0])

    
def create_pixel_grid_node_group():
    node_group = bpy.data.node_groups.new(
        '_Projectors-Addon_PixelGrid', 'ShaderNodeTree')

    # Create input/output sockets for the node group.
    if(bpy.app.version >= (4, 0)):
        node_group.interface.new_socket('Shader', socket_type='NodeSocketShader')
        node_group.interface.new_socket('Vector', socket_type='NodeSocketVector')

        node_group.interface.new_socket('Shader', in_out='OUTPUT', socket_type='NodeSocketShader')
    else:
        inputs = node_group.inputs
        inputs.new('NodeSocketShader', 'Shader')
        inputs.new('NodeSocketVector', 'Vector')

        outputs = node_group.outputs
        outputs.new('NodeSocketShader', 'Shader')

    nodes = node_group.nodes

    auto_pos = auto_offset()

    group_input = nodes.new('NodeGroupInput')
    group_input.location = auto_pos(200)

    sepXYZ = nodes.new('ShaderNodeSeparateXYZ')
    sepXYZ.location = auto_pos(200)

    in_width = nodes.new('ShaderNodeValue')
    in_width.name = '_width'
    in_width.label = 'Width'
    in_width.location = auto_pos(100)

    in_height = nodes.new('ShaderNodeValue')
    in_height.name = '_height'
    in_height.label = 'Height'
    in_height.location = auto_pos(y=-200)

    mul1 = nodes.new('ShaderNodeMath')
    mul1.operation = 'MULTIPLY'
    mul1.location = auto_pos(100)

    mul2 = nodes.new('ShaderNodeMath')
    mul2.operation = 'MULTIPLY'
    mul2.location = auto_pos(y=-200)

    mod1 = nodes.new('ShaderNodeMath')
    mod1.operation = 'MODULO'
    mod1.inputs[1].default_value = 1
    mod1.location = auto_pos(100)

    mod2 = nodes.new('ShaderNodeMath')
    mod2.operation = 'MODULO'
    mod2.inputs[1].default_value = 1
    mod2.location = auto_pos(y=-200)

    col_ramp1 = nodes.new('ShaderNodeValToRGB')
    col_ramp1.color_ramp.elements[1].position = 0.025
    col_ramp1.color_ramp.interpolation = 'CONSTANT'
    col_ramp1.location = auto_pos(100)

    col_ramp2 = nodes.new('ShaderNodeValToRGB')
    col_ramp2.color_ramp.elements[1].position = 0.025
    col_ramp2.color_ramp.interpolation = 'CONSTANT'
    col_ramp2.location = auto_pos(y=-200)

    mix_rgb = nodes.new('ShaderNodeMixRGB')
    mix_rgb.use_clamp = True
    mix_rgb.blend_type = 'MULTIPLY'
    mix_rgb.inputs[0].default_value = 1
    mix_rgb.location = auto_pos(200)
    
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = auto_pos(y=-200)

    mix_shader = nodes.new('ShaderNodeMixShader')
    mix_shader.location = auto_pos(100)

    group_output = nodes.new('NodeGroupOutput')
    group_output.location = auto_pos(100)
    
    # Link Nodes
    links = node_group.links

    links.new(group_input.outputs[0], mix_shader.inputs[2])
    links.new(group_input.outputs[1], sepXYZ.inputs[0])

    links.new(in_width.outputs[0], mul1.inputs[1])
    links.new(in_height.outputs[0], mul2.inputs[1])

    links.new(sepXYZ.outputs[0], mul1.inputs[0])
    links.new(sepXYZ.outputs[1], mul2.inputs[0])

    links.new(mul1.outputs[0], mod1.inputs[0])
    links.new(mul2.outputs[0], mod2.inputs[0])

    links.new(mod1.outputs[0], col_ramp1.inputs[0])
    links.new(mod2.outputs[0], col_ramp2.inputs[0])

    links.new(col_ramp1.outputs[0], mix_rgb.inputs[1])
    links.new(col_ramp2.outputs[0], mix_rgb.inputs[2])

    links.new(mix_rgb.outputs[0], mix_shader.inputs[0])
    links.new(transparent.outputs[0], mix_shader.inputs[1])

    links.new(mix_shader.outputs[0], group_output.inputs[0])

    return node_group
    

def create_projector(context):
    """
    Create a new projector composed out of a camera (parent obj) and a spotlight (child not intended for user interaction).
    The camera is the object intended for the user to manipulate and custom properties are stored there.
    The spotlight with a custom nodetree is responsible for actual projection of the texture.
    """
    create_projector_textures()
    log.debug('Creating projector.')

    # Create a camera and a spotlight
    # ### Spot Light ###
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0))
    spot = context.object
    spot.name = 'Projector.Spot'
    spot.scale = (.01, .01, .01)
    spot.data.spot_size = math.pi - 0.001
    spot.data.spot_blend = 0
    spot.data.shadow_soft_size = 0.0
    spot.hide_select = True
    spot[ADDON_ID.format('spot')] = True
    spot.data.cycles.use_multiple_importance_sampling = False
    add_projector_node_tree_to_spot(spot)

    # ### Camera ###
    bpy.ops.object.camera_add(enter_editmode=False,
                              location=(0, 0, 0),
                              rotation=(0, 0, 0))
    cam = context.object
    cam.name = 'Projector'

    # Parent light to cam.
    spot.parent = cam

    # Move newly create projector (cam and spotlight) to 3D-Cursor position.
    cam.location = context.scene.cursor.location
    cam.rotation_euler = context.scene.cursor.rotation_euler
    return cam


def init_projector(proj_settings, context):
    """프로젝터 초기화 함수 - 코너 핀 지원 추가"""
    # # Add custom properties to store projector settings on the camera obj.
    proj_settings.throw_ratio = 0.8
    proj_settings.power = 1000.0
    proj_settings.projected_texture = Textures.CHECKER.value
    proj_settings.h_shift = 0.0
    proj_settings.v_shift = 0.0
    proj_settings.projected_color = random_color()
    proj_settings.resolution = '1920x1080'
    proj_settings.use_custom_texture_res = True

    # 프로젝터 객체에 is_projector 플래그 설정
    context.object['is_projector'] = True
    
    # Init Projector
    update_throw_ratio(proj_settings, context)
    update_projected_texture(proj_settings, context)
    update_resolution(proj_settings, context)
    update_checker_color(proj_settings, context)
    update_lens_shift(proj_settings, context)
    update_power(proj_settings, context)
    update_pixel_grid(proj_settings, context)
    
    # 렌즈 관리 초기화
    if hasattr(context.object, "lens_manager"):
        print("Initializing lens manager...")
        try:
            context.object.lens_manager.manufacturer = "none"
        except Exception as e:
            print(f"Error initializing lens manager: {e}")
    else:
        print("lens_manager attribute not found!")
    
    # 코너 핀 모듈 초기화 - 비활성화 상태로 시작
    try:
        if hasattr(context.object, "corner_pin"):
            print("Initializing corner pin settings...")
            cp = context.object.corner_pin
            cp.enabled = False  # 처음에는 비활성화 상태로 시작
            cp.top_left = (0.0, 1.0)
            cp.top_right = (1.0, 1.0)
            cp.bottom_left = (0.0, 0.0)
            cp.bottom_right = (1.0, 0.0)
            cp.preset_name = "Default"
            
            # 코너 핀 노드 초기 설치는 필요하지만 활성화하지는 않음
            try:
                from . import corner_pin
                # 노드 준비만 하고 실제 연결은 하지 않음
                corner_pin.nodes.apply_corner_pin_to_projector(context.object)
            except ImportError:
                print("Corner pin module not available")
            except Exception as e:
                print(f"Error initializing corner pin nodes: {e}")
                
            print("Corner pin settings initialized successfully")
        else:
            print("Warning: corner_pin attribute not found on projector object")
    except Exception as e:
        print(f"Error initializing corner pin: {e}")


class PROJECTOR_OT_create_projector(Operator):
    """Create Projector"""
    bl_idname = 'projector.create'
    bl_label = 'Create a new Projector'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        projector = create_projector(context)
        init_projector(projector.proj_settings, context)
        
        # 코너 핀 노드 초기화 (코드 중복을 방지하기 위해 init_projector 내에서 처리)
        
        self.report({'INFO'}, "Created new projector")
        return {'FINISHED'}


def update_projected_texture(proj_settings, context):
    """투사 모드 변경 시 호출되는 함수 - 모드에 맞게 노드 연결을 업데이트"""
    # 무한 재귀 방지 플래그
    if getattr(update_projected_texture, '_is_updating', False):
        return
    
    update_projected_texture._is_updating = True
    
    try:
        projector = get_projector(context)
        if not projector:
            return
            
        # 모드 변경 시 코너 핀 처리
        case = proj_settings.projected_texture
        
        # 코너 핀이 있는 경우
        if hasattr(projector, 'corner_pin'):
            # Custom Texture가 아닐 때는 코너 핀 비활성화
            if case != Textures.CUSTOM_TEXTURE.value and projector.corner_pin.enabled:
                # 코너 핀 비활성화 (무한 재귀 방지를 위해 직접 값 설정)
                projector.corner_pin["enabled"] = False
                print(f"Corner pin disabled due to mode change to {case}")
                
        # 자식 객체 확인
        if not hasattr(projector, "children") or len(projector.children) == 0:
            return
            
        # 스팟라이트 노드 트리 확인
        spot = projector.children[0]
        if not spot or not hasattr(spot.data, "node_tree"):
            return
            
        node_tree = spot.data.node_tree
        
        # 주요 노드 찾기
        group_node = None  # "!! Don't touch !!" 노드
        emission_node = None
        image_texture_node = None
        corner_pin_node = None
        pixel_grid_node = None
        light_output_node = None
        
        for node in node_tree.nodes:
            if node.name == 'Group':
                group_node = node
            elif node.bl_idname == 'ShaderNodeEmission':
                emission_node = node
            elif node.bl_idname == 'ShaderNodeTexImage':
                image_texture_node = node
            elif node.name == 'Corner Pin':
                corner_pin_node = node
            elif node.name == 'pixel_grid':
                pixel_grid_node = node
            elif node.name == 'Light Output' or node.bl_idname == 'ShaderNodeOutputLight':
                light_output_node = node
        
        if not group_node or not emission_node or not light_output_node:
            return
        
        # 소켓 찾기
        texture_vector_output = None
        color_output = None
        
        for output in group_node.outputs:
            if output.name == 'texture vector':
                texture_vector_output = output
            elif output.name == 'color':
                color_output = output
        
        if not texture_vector_output or not color_output:
            print("Required outputs not found")
            return
            
        # 모든 관련 연결 제거
        links_to_remove = []
        
        # 색상 관련 연결 제거
        for link in node_tree.links:
            # Emission의 Color 입력에 연결된 모든 링크 제거
            for input in emission_node.inputs:
                if input.name == 'Color' and link.to_socket == input:
                    links_to_remove.append(link)
            
            # Light Output 입력에 연결된 모든 링크 제거
            if link.to_node == light_output_node:
                links_to_remove.append(link)
        
        # 연결 제거
        for link in links_to_remove:
            node_tree.links.remove(link)
        
        # Emission 노드의 Color 입력 찾기
        emission_color_input = None
        for input in emission_node.inputs:
            if input.name == 'Color':
                emission_color_input = input
                break
        
        if not emission_color_input:
            print("Emission Color input not found")
            return
        
        # 모드별 처리
        case = proj_settings.projected_texture
        
        # 1. Custom Texture 모드
        if case == Textures.CUSTOM_TEXTURE.value:
            if image_texture_node:
                # Vector 입력 찾기
                vector_input = None
                for input in image_texture_node.inputs:
                    if input.name == 'Vector':
                        vector_input = input
                        break
                
                if not vector_input and len(image_texture_node.inputs) > 0:
                    vector_input = image_texture_node.inputs[0]
                
                # 코너 핀 활성화 여부에 따른 연결
                if hasattr(projector, 'corner_pin') and projector.corner_pin.enabled and corner_pin_node:
                    # 코너 핀 노드 연결
                    node_tree.links.new(texture_vector_output, corner_pin_node.inputs[0])
                    if vector_input:
                        node_tree.links.new(corner_pin_node.outputs[0], vector_input)
                else:
                    # 직접 연결
                    if vector_input:
                        node_tree.links.new(texture_vector_output, vector_input)
                
                # Image Texture -> Emission 연결
                image_color_output = None
                for output in image_texture_node.outputs:
                    if output.name == 'Color':
                        image_color_output = output
                        break
                
                if image_color_output and emission_color_input:
                    node_tree.links.new(image_color_output, emission_color_input)
        
        # 2. Checker 또는 Color Grid 모드
        elif case == Textures.CHECKER.value or case == Textures.COLOR_GRID.value:
            # Group color -> Emission 연결 (중요!)
            if color_output and emission_color_input:
                node_tree.links.new(color_output, emission_color_input)
                print(f"Created link: Group color -> Emission for {case} mode")
            
            # Group texture vector -> Pixel Grid 연결 (필요시)
            if pixel_grid_node:
                pixel_grid_vector_input = None
                for i, input in enumerate(pixel_grid_node.inputs):
                    if input.name == 'Vector' or i == 1:  # 두 번째 입력이 Vector인 경우
                        pixel_grid_vector_input = input
                        break
                
                if pixel_grid_vector_input:
                    node_tree.links.new(texture_vector_output, pixel_grid_vector_input)
        
        # Emission -> Light Output 또는 Pixel Grid -> Light Output 연결 (항상 필요)
        if proj_settings.show_pixel_grid and pixel_grid_node:
            node_tree.links.new(pixel_grid_node.outputs[0], light_output_node.inputs[0])
        else:
            # 항상 Emission -> Light Output 연결
            node_tree.links.new(emission_node.outputs[0], light_output_node.inputs[0])
            print(f"Created link: Emission -> Light Output for {case} mode")
        
        # 화면 갱신을 위해 이미지 업데이트
        if case == Textures.CHECKER.value or case == Textures.COLOR_GRID.value:
            update_checker_color(proj_settings, context)
        
        print(f"Updated projected texture to {case}")
        
    finally:
        # 플래그 해제
        update_projected_texture._is_updating = False

class PROJECTOR_OT_delete_projector(Operator):
    """Delete Projector"""
    bl_idname = 'projector.delete'
    bl_label = 'Delete Projector'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(get_projectors(context, only_selected=True))

    def execute(self, context):
        selected_projectors = get_projectors(context, only_selected=True)
        for projector in selected_projectors:
            for child in projector.children:
                bpy.data.objects.remove(child, do_unlink=True)
            else:
                bpy.data.objects.remove(projector, do_unlink=True)
        return {'FINISHED'}


class ProjectorSettings(bpy.types.PropertyGroup):
    throw_ratio: bpy.props.FloatProperty(
        name="Throw Ratio",
        min=0.1, max=10.0,  # 매우 넓은 하드 제한
        soft_min=0.1, soft_max=10.0,  # 매우 넓은 소프트 제한
        update=update_throw_ratio,
        subtype='FACTOR')
    power: bpy.props.FloatProperty(
        name="Projector Power",
        soft_min=0, soft_max=999999,
        update=update_power,
        unit='POWER')
    resolution: bpy.props.EnumProperty(
        items=RESOLUTIONS,
        default='1920x1080',
        description="Select a Resolution for your Projector",
        update=update_resolution)
    use_custom_texture_res: bpy.props.BoolProperty(
        name="Let Image Define Projector Resolution",
        default=True,
        description="Use the resolution from the image as the projector resolution. Warning: After selecting a new image toggle this checkbox to update",
        update=update_throw_ratio)
    h_shift: bpy.props.FloatProperty(
        name="Horizontal Shift",
        description="Horizontal Lens Shift",
        min=-150, max=150,  # 넓은 하드 제한
        soft_min=-150, soft_max=150,  # 넓은 소프트 제한
        update=update_lens_shift,
        subtype='PERCENTAGE')
    v_shift: bpy.props.FloatProperty(
        name="Vertical Shift",
        description="Vertical Lens Shift",
        min=-150, max=150,  # 넓은 하드 제한
        soft_min=-150, soft_max=150,  # 넓은 소프트 제한
        update=update_lens_shift,
        subtype='PERCENTAGE')
    projected_color: bpy.props.FloatVectorProperty(
        subtype='COLOR',
        update=update_checker_color)
    projected_texture: bpy.props.EnumProperty(
        items=PROJECTED_OUTPUTS,
        default=Textures.CHECKER.value,
        description="What do you to project?",
        update=update_throw_ratio)
    show_pixel_grid: bpy.props.BoolProperty(
        name="Show Pixel Grid",
        description="When checked the image is divided into a pixel grid with the dimensions of the image resolution.",
        default=False,
        update=update_pixel_grid)

def apply_lens_data_to_projector(projector_obj, manufacturer, model):
    """렌즈 데이터를 프로젝터 설정에 적용"""
    from .lens_management.database import lens_db
    
    if not manufacturer or not model or not projector_obj:
        return False
    
    # 렌즈 프로필 가져오기
    profile = lens_db.get_lens_profile(manufacturer, model)
    if not profile or 'specs' not in profile:
        return False
    
    specs = profile['specs']
    proj_settings = projector_obj.proj_settings
    
    # Throw Ratio 적용
    if 'throw_ratio' in specs:
        throw_ratio = specs['throw_ratio']
        if isinstance(throw_ratio, dict) and 'default' in throw_ratio:
            proj_settings.throw_ratio = throw_ratio['default']
    
    # 렌즈 시프트 적용
    if 'lens_shift' in specs:
        lens_shift = specs['lens_shift']
        if 'h_shift_range' in lens_shift:
            # 시프트 범위의 중간값 또는 0에 가까운 값으로 설정
            h_min, h_max = lens_shift['h_shift_range']
            proj_settings.h_shift = 0.0 if (h_min <= 0 <= h_max) else (h_min + h_max) / 2
        
        if 'v_shift_range' in lens_shift:
            v_min, v_max = lens_shift['v_shift_range']
            proj_settings.v_shift = 0.0 if (v_min <= 0 <= v_max) else (v_min + v_max) / 2
    
    return True

def update_from_lens_profile(projector_obj, lens_profile):
    """
    렌즈 프로필 데이터를 기반으로 프로젝터 설정 업데이트
    """
    if not projector_obj or not lens_profile or not hasattr(projector_obj, "proj_settings"):
        return False
        
    proj_settings = projector_obj.proj_settings
    
    # 기존 제한값 초기화
    if "throw_ratio_min" in projector_obj:
        del projector_obj["throw_ratio_min"]
    if "throw_ratio_max" in projector_obj:
        del projector_obj["throw_ratio_max"]
    if "h_shift_min" in projector_obj:
        del projector_obj["h_shift_min"]
    if "h_shift_max" in projector_obj:
        del projector_obj["h_shift_max"]
    if "v_shift_min" in projector_obj:
        del projector_obj["v_shift_min"]
    if "v_shift_max" in projector_obj:
        del projector_obj["v_shift_max"]
    
    # 프로필에서 specs 정보 추출
    if 'specs' in lens_profile:
        specs = lens_profile['specs']
        
        # Throw Ratio 업데이트
        if 'throw_ratio' in specs:
            throw_ratio = specs['throw_ratio']
            if isinstance(throw_ratio, dict):
                min_val = throw_ratio.get('min', 0.4)
                max_val = throw_ratio.get('max', 3.0)
                
                # 제한 값 저장 (커스텀 속성으로)
                projector_obj["throw_ratio_min"] = min_val
                projector_obj["throw_ratio_max"] = max_val
                
                # 현재 값이 범위 내에 있는지 확인
                current_throw = proj_settings.throw_ratio
                if current_throw < min_val or current_throw > max_val:
                    # 범위를 벗어나면 최소값으로 설정
                    proj_settings.throw_ratio = min_val
            
        # 렌즈 시프트 업데이트
        if 'lens_shift' in specs:
            lens_shift = specs['lens_shift']
            
            # 수평 시프트
            if 'h_shift_range' in lens_shift:
                h_min, h_max = lens_shift['h_shift_range']
                
                # 제한 값 저장 (커스텀 속성으로)
                projector_obj["h_shift_min"] = h_min
                projector_obj["h_shift_max"] = h_max
                
                # 현재 값이 범위를 벗어나면 조정
                current_h = proj_settings.h_shift
                if current_h < h_min or current_h > h_max:
                    # 중간값 또는 0으로 설정
                    new_h = 0.0 if (h_min <= 0 <= h_max) else (h_min + h_max) / 2
                    proj_settings.h_shift = new_h
            
            # 수직 시프트
            if 'v_shift_range' in lens_shift:
                v_min, v_max = lens_shift['v_shift_range']
                
                # 제한 값 저장 (커스텀 속성으로)
                projector_obj["v_shift_min"] = v_min
                projector_obj["v_shift_max"] = v_max
                
                # 현재 값이 범위를 벗어나면 조정
                current_v = proj_settings.v_shift
                if current_v < v_min or current_v > v_max:
                    # 중간값 또는 0으로 설정
                    new_v = 0.0 if (v_min <= 0 <= v_max) else (v_min + v_max) / 2
                    proj_settings.v_shift = new_v
    
    # 설정 반영을 위해 함수 호출
    update_throw_ratio(proj_settings, bpy.context)
    update_lens_shift(proj_settings, bpy.context)
    
    return True

def is_within_lens_limits(projector_obj, check_throw=True, check_shift=True):
    """
    현재 프로젝터 설정이 선택된 렌즈의 제한 범위 내에 있는지 확인
    
    Parameters:
    projector_obj (Object): 프로젝터 객체
    check_throw (bool): throw ratio 확인 여부
    check_shift (bool): 렌즈 시프트 확인 여부
    
    Returns:
    dict: 각 설정별 범위 초과 여부 {'throw_ratio': bool, 'h_shift': bool, 'v_shift': bool}
    """
    result = {'throw_ratio': True, 'h_shift': True, 'v_shift': True}
    
    if not projector_obj or not hasattr(projector_obj, "proj_settings"):
        return result
        
    proj_settings = projector_obj.proj_settings
    
    # 제한 값 가져오기
    throw_min = projector_obj.get("throw_ratio_min", None)
    throw_max = projector_obj.get("throw_ratio_max", None)
    h_min = projector_obj.get("h_shift_min", None)
    h_max = projector_obj.get("h_shift_max", None)
    v_min = projector_obj.get("v_shift_min", None)
    v_max = projector_obj.get("v_shift_max", None)
    
    # 제한 값이 없으면 모두 유효한 것으로 처리
    if None in (throw_min, throw_max, h_min, h_max, v_min, v_max):
        return result
    
    # Throw Ratio 확인
    if check_throw:
        current_throw = proj_settings.throw_ratio
        if current_throw < throw_min or current_throw > throw_max:
            result['throw_ratio'] = False
    
    # 수평 시프트 확인
    if check_shift:
        if proj_settings.h_shift < h_min or proj_settings.h_shift > h_max:
            result['h_shift'] = False
            
    # 수직 시프트 확인
    if check_shift:
        if proj_settings.v_shift < v_min or proj_settings.v_shift > v_max:
            result['v_shift'] = False
    
    return result

def register():
    bpy.utils.register_class(ProjectorSettings)
    bpy.utils.register_class(PROJECTOR_OT_create_projector)
    bpy.utils.register_class(PROJECTOR_OT_delete_projector)
    bpy.utils.register_class(PROJECTOR_OT_change_color_randomly)
    bpy.types.Object.proj_settings = bpy.props.PointerProperty(
        type=ProjectorSettings)


def unregister():
    bpy.utils.unregister_class(PROJECTOR_OT_change_color_randomly)
    bpy.utils.unregister_class(PROJECTOR_OT_delete_projector)
    bpy.utils.unregister_class(PROJECTOR_OT_create_projector)
    bpy.utils.unregister_class(ProjectorSettings)
