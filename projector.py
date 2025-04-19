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

PROJECTED_OUTPUTS = [(Textures.CUSTOM_TEXTURE.value, 'Select Texture', '', 1)]


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


def create_projector_node_group():
    """Create projector node group"""
    # Check if it already exists
    node_group_name = '_Projectors-Addon_NodeGroup'
    node_group = bpy.data.node_groups.get(node_group_name)
    
    if not node_group:
        # Create new node group
        node_group = bpy.data.node_groups.new(node_group_name, 'ShaderNodeTree')
    
    return node_group

def add_projector_node_tree_to_spot(spot):
    """
    This function turns a spot light into a projector.
    This is achieved through a texture on the spot light and some basic math.
    """
    # helper.py에서 import하지 않고 직접 함수 정의
    def is_blender_40_or_newer():
        return bpy.app.version >= (4, 0, 0)
    
    def is_blender_43_or_newer():
        return bpy.app.version >= (4, 3, 0)

    spot.data.use_nodes = True
    root_tree = spot.data.node_tree
    root_tree.nodes.clear()
    
    # Get node group
    node_group = create_projector_node_group()

    # Create node group node
    group = spot.data.node_tree.nodes.new('ShaderNodeGroup')
    group.node_tree = node_group
    group.label = "!! Don't touch !!"
    
    # Add nodes and connection logic (reuse existing code)
    nodes = group.node_tree.nodes
    tree = group.node_tree

    # Create output socket in node group
    if is_blender_40_or_newer():
        # Interface for Blender 4.0+ version
        node_group.interface.new_socket('texture vector',  in_out="OUTPUT", socket_type='NodeSocketVector')
        node_group.interface.new_socket('color', in_out="OUTPUT", socket_type='NodeSocketColor')
    else:
        # Interface for previous versions
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
    
    # Blender 4.3 specific settings
    if is_blender_43_or_newer():
        # Handle changed node API in 4.3
        pass

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
    """해상도 변경 시 호출되는 함수"""
    projector = get_projector(context)
    if not projector or not projector.children or len(projector.children) == 0:
        return
        
    spot = projector.children[0]
    if not spot or not spot.data or not spot.data.node_tree:
        return
        
    # 이미지 텍스처 노드 찾기
    image_texture_node = None
    for node in spot.data.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeTexImage':
            image_texture_node = node
            break
            
    if not image_texture_node:
        return
        
    # 선택된 해상도에 맞는 기본 텍스처 이미지로 변경
    default_texture_name = f'_proj.tex.{proj_settings.resolution}'
    if default_texture_name in bpy.data.images:
        # 이전 이미지 저장
        old_image = image_texture_node.image
        
        # 새 이미지 설정
        image_texture_node.image = bpy.data.images[default_texture_name]
        print(f"텍스처 이미지를 {default_texture_name}으로 변경")
        
        # 커스텀 이미지가 아닌 경우에만 이전 이미지 해제
        if old_image and old_image.name.startswith('_proj.tex.'):
            old_image.user_clear()
    
    # 픽셀 그리드 설정 업데이트
    update_pixel_grid(proj_settings, context)
    
    # 노드 연결 업데이트 확인
    update_projected_texture(proj_settings, context)
    
    # throw ratio 업데이트 (해상도에 맞게 투사 비율 조정)
    update_throw_ratio(proj_settings, context)


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
    # 기본 속성 설정
    proj_settings.throw_ratio = 0.8
    proj_settings.power = 1000.0
    proj_settings.projected_texture = Textures.CUSTOM_TEXTURE.value  # 항상 Custom Texture로 설정
    proj_settings.h_shift = 0.0
    proj_settings.v_shift = 0.0
    proj_settings.resolution = '1920x1080'
    proj_settings.use_custom_texture_res = True

    # 프로젝터 객체에 is_projector 플래그 설정
    context.object['is_projector'] = True
    
    # 프로젝터 초기화
    update_throw_ratio(proj_settings, context)
    update_projected_texture(proj_settings, context)
    update_resolution(proj_settings, context)
    update_lens_shift(proj_settings, context)
    update_power(proj_settings, context)
    update_pixel_grid(proj_settings, context)
    
    # 기본 이미지 텍스처 설정 - 기본 테스트 패턴 이미지 설정
    projector = get_projector(context)
    if projector and hasattr(projector, "children") and len(projector.children) > 0:
        spot = projector.children[0]
        if spot and hasattr(spot.data, "node_tree"):
            image_node = spot.data.node_tree.nodes.get('Image Texture')
            if image_node:
                # 기본 텍스처 이름 형식: '_proj.tex.1920x1080'
                default_texture_name = f'_proj.tex.{proj_settings.resolution}'
                if default_texture_name in bpy.data.images:
                    image_node.image = bpy.data.images[default_texture_name]
    
    # 렌즈 관리 초기화
    if hasattr(context.object, "lens_manager"):
        print("Initializing lens manager...")
        try:
            context.object.lens_manager.manufacturer = "none"
        except Exception as e:
            print(f"Error initializing lens manager: {e}")
    else:
        print("lens_manager attribute not found!")
    
    # 코너 핀 모듈 초기화 추가
    try:
        if hasattr(context.object, "corner_pin"):
            print("Initializing corner pin settings...")
            cp = context.object.corner_pin
            cp.enabled = False
            cp.top_left = (0.0, 1.0)
            cp.top_right = (1.0, 1.0)
            cp.bottom_left = (0.0, 0.0)
            cp.bottom_right = (1.0, 0.0)
            cp.preset_name = "Default"
            
            # 코너 핀 노드 초기화
            try:
                from . import corner_pin
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
        
        return {'FINISHED'}


def update_projected_texture(proj_settings, context):
    """투사 출력 소스 업데이트"""
    projector = get_projector(context)
    if not projector:
        return
        
    # 스팟라이트 확인
    if not hasattr(projector, "children") or len(projector.children) == 0:
        return
        
    spot = projector.children[0]
    if not spot or not hasattr(spot.data, "node_tree"):
        return
        
    root_tree = spot.data.node_tree
    
    # 주요 노드 찾기
    group_node = root_tree.nodes.get('Group')
    emission_node = root_tree.nodes.get('Emission')
    light_output_node = None
    for node in root_tree.nodes:
        if node.bl_idname == 'ShaderNodeOutputLight':
            light_output_node = node
            break
    
    # 이미지 텍스처 노드 찾기
    custom_tex_node = root_tree.nodes.get('Image Texture')
    
    if not all([group_node, emission_node, light_output_node, custom_tex_node]):
        print("필수 노드를 찾을 수 없음")
        return
    
    # 기존 연결 제거 (Emission 입력과 Light Output 입력만)
    links_to_remove = []
    for link in root_tree.links:
        if link.to_node == emission_node and link.to_socket == emission_node.inputs[0]:
            links_to_remove.append(link)
        elif link.to_node == light_output_node:
            links_to_remove.append(link)
    
    for link in links_to_remove:
        root_tree.links.remove(link)
    
    # 그룹 노드 트리와 출력 확인
    texture_vector_output = None
    for output in group_node.outputs:
        if output.name == 'texture vector':
            texture_vector_output = output
            break
    
    if not texture_vector_output:
        print("texture vector 출력을 찾을 수 없음")
        return
    
    # Custom Texture 모드: Image Texture -> Emission
    # Image Texture -> Emission
    root_tree.links.new(custom_tex_node.outputs[0], emission_node.inputs[0])
    print("Image Texture -> Emission 연결 생성됨")
    
    # 항상 Emission -> Light Output 연결
    root_tree.links.new(emission_node.outputs[0], light_output_node.inputs[0])
    print("Emission -> Light Output 연결 생성됨")
    
    # 코너 핀이 활성화된 경우 처리
    if hasattr(projector, 'corner_pin') and projector.corner_pin.enabled:
        try:
            from . import corner_pin
            corner_pin.nodes.update_corner_pin_nodes(projector)
            print("코너 핀 노드 업데이트됨")
        except Exception as e:
            print(f"코너 핀 업데이트 오류: {e}")
    else:
        # 코너 핀이 비활성화된 경우 직접 Group -> Image Texture 연결
        vector_input = None
        for input in custom_tex_node.inputs:
            if input.name == 'Vector':
                vector_input = input
                break
        
        if not vector_input and len(custom_tex_node.inputs) > 0:
            vector_input = custom_tex_node.inputs[0]
        
        if vector_input:
            # 기존 연결 제거
            for link in list(root_tree.links):
                if link.to_node == custom_tex_node and link.to_socket == vector_input:
                    root_tree.links.remove(link)
            
            # Group -> Image Texture 연결
            root_tree.links.new(texture_vector_output, vector_input)
            print("Group -> Image Texture 연결 생성됨")
    
    # 픽셀 그리드 적용 여부에 따라 출력 연결 업데이트
    if proj_settings.show_pixel_grid:
        pixel_grid_node = root_tree.nodes.get('pixel_grid')
        if pixel_grid_node:
            # 기존 Light Output 연결 제거
            for link in list(root_tree.links):
                if link.to_node == light_output_node:
                    root_tree.links.remove(link)
            
            # Pixel Grid -> Light Output 연결
            root_tree.links.new(pixel_grid_node.outputs[0], light_output_node.inputs[0])
            print("픽셀 그리드 활성화: Pixel Grid -> Light Output 연결 생성됨")


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
        soft_min=0.4, soft_max=3,
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
        name="Use Image Resolution",
        default=True,
        description="Use the resolution from the image as the projector resolution. When loading a new image, toggle this to update.",
        update=update_throw_ratio)
    h_shift: bpy.props.FloatProperty(
        name="Horizontal Shift",
        description="Horizontal Lens Shift",
        soft_min=-20, soft_max=20,
        update=update_lens_shift,
        subtype='PERCENTAGE')
    v_shift: bpy.props.FloatProperty(
        name="Vertical Shift",
        description="Vertical Lens Shift",
        soft_min=-20, soft_max=20,
        update=update_lens_shift,
        subtype='PERCENTAGE')
    # projected_color 속성 제거 - Custom Texture만 사용하므로 필요 없음
    # 기본값을 CUSTOM_TEXTURE로 고정
    projected_texture: bpy.props.EnumProperty(
        items=[(Textures.CUSTOM_TEXTURE.value, 'Custom Texture', '', 1)],
        default=Textures.CUSTOM_TEXTURE.value,
        description="Texture to project",
        update=update_throw_ratio)
    show_pixel_grid: bpy.props.BoolProperty(
        name="Show Pixel Grid",
        description="When checked the image is divided into a pixel grid with the dimensions of the image resolution.",
        default=False,
        update=update_pixel_grid)


def safe_set_node_input(node, input_name, value, fallback_names=None):
    """
    노드 입력값을 안전하게 설정합니다. 입력 이름이 변경되었을 경우 대체 이름을 시도합니다.
    
    Args:
        node: 대상 노드
        input_name: 기본 입력 이름
        value: 설정할 값
        fallback_names: 대체 입력 이름 목록
    
    Returns:
        성공 여부 (bool)
    """
    if input_name in node.inputs:
        node.inputs[input_name].default_value = value
        return True
    
    # 기본 이름이 없을 경우 대체 이름 시도
    if fallback_names:
        for name in fallback_names:
            if name in node.inputs:
                node.inputs[name].default_value = value
                return True
    
    # 모든 시도 실패
    print(f"Warning: Could not set input '{input_name}' on node '{node.name}'")
    return False


@bpy.app.handlers.persistent
def check_projector_updates(scene):
    """씬 업데이트 시 프로젝터 업데이트 확인"""
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA' and obj.name.startswith('Projector'):
            # 특정 속성이 업데이트 필요 표시가 있는지 확인
            if hasattr(obj, "distance_settings") and obj.get("_needs_update", False):
                # 업데이트 수행
                from .distance_display import update_distance_display
                update_distance_display(obj)
                # 업데이트 완료 표시
                obj["_needs_update"] = False


def register():
    bpy.utils.register_class(ProjectorSettings)
    bpy.utils.register_class(PROJECTOR_OT_create_projector)
    bpy.utils.register_class(PROJECTOR_OT_delete_projector)
    # PROJECTOR_OT_change_color_randomly 클래스 제거 - Custom Texture만 사용하므로 필요 없음
    bpy.types.Object.proj_settings = bpy.props.PointerProperty(
        type=ProjectorSettings)


def unregister():
    # PROJECTOR_OT_change_color_randomly 클래스 제거
    bpy.utils.unregister_class(PROJECTOR_OT_delete_projector)
    bpy.utils.unregister_class(PROJECTOR_OT_create_projector)
    bpy.utils.unregister_class(ProjectorSettings)