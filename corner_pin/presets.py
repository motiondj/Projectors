# corner_pin/presets.py

import bpy
from bpy.props import StringProperty, CollectionProperty, IntProperty
from bpy.types import PropertyGroup, UIList

class CornerPinPreset(PropertyGroup):
    """코너 핀 프리셋 데이터 구조"""
    name: StringProperty(name="Name", default="Untitled")
    top_left_x: bpy.props.FloatProperty()
    top_left_y: bpy.props.FloatProperty()
    top_right_x: bpy.props.FloatProperty()
    top_right_y: bpy.props.FloatProperty()
    bottom_left_x: bpy.props.FloatProperty()
    bottom_left_y: bpy.props.FloatProperty()
    bottom_right_x: bpy.props.FloatProperty()
    bottom_right_y: bpy.props.FloatProperty()

class CORNER_PIN_UL_presets(UIList):
    """코너 핀 프리셋 목록 UI"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='FILE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='FILE')

class CORNER_PIN_OT_delete_preset(bpy.types.Operator):
    """프리셋 삭제"""
    bl_idname = "corner_pin.delete_preset"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(name="Preset Name")
    
    def execute(self, context):
        presets = context.scene.corner_pin_presets
        index = next((i for i, p in enumerate(presets) if p.name == self.preset_name), -1)
        
        if index >= 0:
            presets.remove(index)
            if context.scene.corner_pin_preset_index >= len(presets):
                context.scene.corner_pin_preset_index = max(0, len(presets) - 1)
            return {'FINISHED'}
        
        return {'CANCELLED'}

def save_preset(projector_obj, preset_name):
    """현재 코너 핀 설정을 프리셋으로 저장"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        return False
    
    corner_pin = projector_obj.corner_pin
    scene = bpy.context.scene
    
    # 같은 이름의 프리셋이 있는지 확인
    existing_index = -1
    for i, preset in enumerate(scene.corner_pin_presets):
        if preset.name == preset_name:
            existing_index = i
            break
    
    # 새 프리셋 생성 또는 기존 프리셋 업데이트
    if existing_index >= 0:
        preset = scene.corner_pin_presets[existing_index]
    else:
        preset = scene.corner_pin_presets.add()
        preset.name = preset_name
    
    # 코너 데이터 저장
    preset.top_left_x, preset.top_left_y = corner_pin.top_left
    preset.top_right_x, preset.top_right_y = corner_pin.top_right
    preset.bottom_left_x, preset.bottom_left_y = corner_pin.bottom_left
    preset.bottom_right_x, preset.bottom_right_y = corner_pin.bottom_right
    
    return True

def load_preset(projector_obj, preset_name):
    """프리셋에서 코너 핀 설정 불러오기"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        return False
    
    scene = bpy.context.scene
    corner_pin = projector_obj.corner_pin
    
    # 프리셋 찾기
    preset = None
    for p in scene.corner_pin_presets:
        if p.name == preset_name:
            preset = p
            break
    
    if not preset:
        return False
    
    # 코너 데이터 불러오기
    corner_pin.top_left = (preset.top_left_x, preset.top_left_y)
    corner_pin.top_right = (preset.top_right_x, preset.top_right_y)
    corner_pin.bottom_left = (preset.bottom_left_x, preset.bottom_left_y)
    corner_pin.bottom_right = (preset.bottom_right_x, preset.bottom_right_y)
    
    # 노드 업데이트
    from . import nodes
    nodes.update_corner_pin_nodes(projector_obj)
    
    return True

def register():
    bpy.utils.register_class(CornerPinPreset)
    bpy.utils.register_class(CORNER_PIN_UL_presets)
    bpy.utils.register_class(CORNER_PIN_OT_delete_preset)
    
    # 프리셋 컬렉션 속성 등록
    bpy.types.Scene.corner_pin_presets = CollectionProperty(type=CornerPinPreset)
    bpy.types.Scene.corner_pin_preset_index = IntProperty()
    print("Corner Pin presets registered")

def unregister():
    # 속성 제거
    del bpy.types.Scene.corner_pin_preset_index
    del bpy.types.Scene.corner_pin_presets
    
    bpy.utils.unregister_class(CORNER_PIN_OT_delete_preset)
    bpy.utils.unregister_class(CORNER_PIN_UL_presets)
    bpy.utils.unregister_class(CornerPinPreset)