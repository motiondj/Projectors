# corner_pin/operators.py 개선 버전

import bpy
from bpy.types import Operator
from bpy.props import FloatVectorProperty, StringProperty, EnumProperty

class CORNER_PIN_OT_reset(Operator):
    """모든 코너를 기본 위치로 재설정"""
    bl_idname = "corner_pin.reset"
    bl_label = "Reset Corners"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and hasattr(context.active_object, 'corner_pin')
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            return {'CANCELLED'}
            
        cp = obj.corner_pin
        cp.top_left = (0.0, 1.0)
        cp.top_right = (1.0, 1.0)
        cp.bottom_left = (0.0, 0.0)
        cp.bottom_right = (1.0, 0.0)
        
        # 노드 업데이트
        from . import nodes
        nodes.update_corner_pin_nodes(obj)
        
        return {'FINISHED'}

class CORNER_PIN_OT_adjust_corner(Operator):
    """코너 위치 조정"""
    bl_idname = "corner_pin.adjust_corner"
    bl_label = "Adjust Corner"
    bl_options = {'REGISTER', 'UNDO'}
    
    corner: EnumProperty(
        name="Corner",
        items=[
            ('top_left', "Top Left", ""),
            ('top_right', "Top Right", ""),
            ('bottom_left', "Bottom Left", ""),
            ('bottom_right', "Bottom Right", "")
        ],
        default='top_left'
    )
    
    delta: FloatVectorProperty(
        name="Delta",
        size=2,
        default=(0.0, 0.0)
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and hasattr(context.active_object, 'corner_pin')
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            return {'CANCELLED'}
        
        cp = obj.corner_pin
        
        # 현재 코너 위치 가져오기
        current_pos = getattr(cp, self.corner)
        
        # 새 위치 계산 (0-1 범위 내로 제한)
        new_x = max(0.0, min(1.0, current_pos[0] + self.delta[0]))
        new_y = max(0.0, min(1.0, current_pos[1] + self.delta[1]))
        
        # 코너 위치 업데이트
        setattr(cp, self.corner, (new_x, new_y))
        
        # 노드 업데이트
        from . import nodes
        nodes.update_corner_pin_nodes(obj)
        
        return {'FINISHED'}

class CORNER_PIN_OT_visual_edit_mode(Operator):
    """시각적 편집 모드 시작"""
    bl_idname = "corner_pin.visual_edit_mode"
    bl_label = "Edit Corner Positions"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and hasattr(context.active_object, 'corner_pin')
    
    def invoke(self, context, event):
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            return {'CANCELLED'}
        
        # 모달 모드 시작
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        # 모달 모드에서 코너 드래그 처리
        # (실제 구현은 더 복잡함 - 추후 개발)
        
        if event.type == 'ESC':
            return {'CANCELLED'}
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # 클릭한 위치에서 가장 가까운 코너 찾기
            # (여기에 코드 추가 필요)
            return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}

class CORNER_PIN_OT_save_preset(Operator):
    """현재 코너 설정을 프리셋으로 저장"""
    bl_idname = "corner_pin.save_preset"
    bl_label = "Save Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name for the preset",
        default="My Preset"
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and hasattr(context.active_object, 'corner_pin')
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            return {'CANCELLED'}
            
        # 프리셋 저장 로직
        from . import presets
        if presets.save_preset(obj, self.preset_name):
            self.report({'INFO'}, f"Preset '{self.preset_name}' saved")
        else:
            self.report({'ERROR'}, "Failed to save preset")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CORNER_PIN_OT_load_preset(Operator):
    """저장된 프리셋 불러오기"""
    bl_idname = "corner_pin.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to load"
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'CAMERA' and hasattr(context.active_object, 'corner_pin')
    
    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            return {'CANCELLED'}
            
        # 프리셋 불러오기 로직
        from . import presets
        if presets.load_preset(obj, self.preset_name):
            self.report({'INFO'}, f"Preset '{self.preset_name}' loaded")
        else:
            self.report({'ERROR'}, f"Failed to load preset '{self.preset_name}'")
        
        return {'FINISHED'}

class CORNER_PIN_OT_delete_preset(Operator):
    """프리셋 삭제"""
    bl_idname = "corner_pin.delete_preset"
    bl_label = "Delete Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: StringProperty(
        name="Preset Name",
        description="Name of the preset to delete"
    )
    
    @classmethod
    def poll(cls, context):
        return context.scene.get('corner_pin_presets') is not None
    
    def execute(self, context):
        presets = context.scene.corner_pin_presets
        index = next((i for i, p in enumerate(presets) if p.name == self.preset_name), -1)
        
        if index >= 0:
            presets.remove(index)
            if context.scene.corner_pin_preset_index >= len(presets):
                context.scene.corner_pin_preset_index = max(0, len(presets) - 1)
            
            self.report({'INFO'}, f"Preset '{self.preset_name}' deleted")
            return {'FINISHED'}
        
        self.report({'ERROR'}, f"Preset '{self.preset_name}' not found")
        return {'CANCELLED'}

def register():
    bpy.utils.register_class(CORNER_PIN_OT_reset)
    bpy.utils.register_class(CORNER_PIN_OT_adjust_corner)
    bpy.utils.register_class(CORNER_PIN_OT_visual_edit_mode)
    bpy.utils.register_class(CORNER_PIN_OT_save_preset)
    bpy.utils.register_class(CORNER_PIN_OT_load_preset)
    bpy.utils.register_class(CORNER_PIN_OT_delete_preset)
    print("Corner Pin operators registered")

def unregister():
    bpy.utils.unregister_class(CORNER_PIN_OT_delete_preset)
    bpy.utils.unregister_class(CORNER_PIN_OT_load_preset)
    bpy.utils.unregister_class(CORNER_PIN_OT_save_preset)
    bpy.utils.unregister_class(CORNER_PIN_OT_visual_edit_mode)
    bpy.utils.unregister_class(CORNER_PIN_OT_adjust_corner)
    bpy.utils.unregister_class(CORNER_PIN_OT_reset)