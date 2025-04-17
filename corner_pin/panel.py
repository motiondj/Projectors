# corner_pin/panel.py 개선 버전

import bpy
from bpy.types import Panel

class CORNER_PIN_PT_panel(Panel):
    """4코너 보정 기능 UI 패널"""
    bl_label = "4-Corner Pin"
    bl_idname = "CORNER_PIN_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Projector"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'CAMERA' and hasattr(obj, 'corner_pin')
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            layout.label(text="No projector selected")
            return
        
        corner_pin = obj.corner_pin
        
        # 활성화 토글
        layout.prop(corner_pin, "enabled", text="Enable Corner Pin")
        
        if not corner_pin.enabled:
            return
        
        # 코너 위치 컨트롤
        box = layout.box()
        box.label(text="Corner Positions", icon='MESH_GRID')
        
        # 시각적 편집 모드 버튼
        box.operator("corner_pin.interactive_edit", text="Interactive Edit Mode", icon='RESTRICT_SELECT_OFF')
        
        # 코너 좌표 숫자 입력
        col = box.column(align=True)
        row = col.row(align=True)
        
        # 왼쪽 열: 왼쪽 코너들
        left_col = row.column(align=True)
        left_col.prop(corner_pin, "top_left", text="Top Left")
        left_col.prop(corner_pin, "bottom_left", text="Bottom Left")
        
        # 오른쪽 열: 오른쪽 코너들
        right_col = row.column(align=True)
        right_col.prop(corner_pin, "top_right", text="Top Right")
        right_col.prop(corner_pin, "bottom_right", text="Bottom Right")
        
        # 미세 조정 버튼
        box.label(text="Fine Adjustment", icon='ARROW_LEFTRIGHT')
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True)
        
        for corner in ['top_left', 'top_right', 'bottom_left', 'bottom_right']:
            col = grid.column(align=True)
            col.label(text=corner.replace('_', ' ').title())
            
            row = col.row(align=True)
            # X 축 조정
            op = row.operator("corner_pin.adjust_corner", text="X-")
            op.corner = corner
            op.delta = (-0.01, 0.0)
            
            op = row.operator("corner_pin.adjust_corner", text="X+")
            op.corner = corner
            op.delta = (0.01, 0.0)
            
            row = col.row(align=True)
            # Y 축 조정
            op = row.operator("corner_pin.adjust_corner", text="Y-")
            op.corner = corner
            op.delta = (0.0, -0.01)
            
            op = row.operator("corner_pin.adjust_corner", text="Y+")
            op.corner = corner
            op.delta = (0.0, 0.01)
        
        # 리셋 버튼
        row = box.row()
        row.operator("corner_pin.reset", text="Reset Corners", icon='LOOP_BACK')
        
        # 프리셋 섹션
        box = layout.box()
        box.label(text="Presets", icon='PRESET')
        
        # 프리셋 저장
        row = box.row(align=True)
        row.prop(corner_pin, "preset_name", text="")
        row.operator("corner_pin.save_preset", text="Save", icon='DUPLICATE')
        
        # 프리셋 목록
        if hasattr(context.scene, "corner_pin_presets") and len(context.scene.corner_pin_presets) > 0:
            box.template_list("CORNER_PIN_UL_presets", "", context.scene, "corner_pin_presets", 
                             context.scene, "corner_pin_preset_index", rows=3)
            
            if len(context.scene.corner_pin_presets) > 0 and context.scene.corner_pin_preset_index >= 0:
                preset = context.scene.corner_pin_presets[context.scene.corner_pin_preset_index]
                row = box.row(align=True)
                row.operator("corner_pin.load_preset", text="Load", icon='IMPORT').preset_name = preset.name
                row.operator("corner_pin.delete_preset", text="Delete", icon='X').preset_name = preset.name
        else:
            box.label(text="No presets saved yet")

def register():
    try:
        # 이미 등록된 경우 먼저 등록 해제
        if hasattr(bpy.types, 'CORNER_PIN_PT_panel'):
            unregister()
        
        bpy.utils.register_class(CORNER_PIN_PT_panel)
        print("Corner Pin panel registered")
    except Exception as e:
        print(f"Error registering Corner Pin panel: {e}")

def unregister():
    try:
        bpy.utils.unregister_class(CORNER_PIN_PT_panel)
    except Exception as e:
        print(f"Error unregistering Corner Pin panel: {e}")