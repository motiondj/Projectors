# corner_pin/panel.py UI 개선

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
        
        # 기본 조건: 객체가 카메라이고 corner_pin 속성을 가지고 있어야 함
        basic_condition = obj and obj.type == 'CAMERA' and hasattr(obj, 'corner_pin')
        
        if not basic_condition:
            return False
        
        # Custom Texture가 선택된 경우만 패널 표시
        if hasattr(obj, 'proj_settings') and obj.proj_settings.projected_texture == 'custom_texture':
            return True
        
        return False
    
    def draw(self, context):
        print("CORNER_PIN_PT_panel.draw() called")
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            layout.label(text="No projector selected")
            print("  - No projector with corner_pin attribute")
            return
        
        print(f"  - Drawing for object: {obj.name}")
        corner_pin = obj.corner_pin
        
        # 활성화 토글
        row = layout.row()
        row.prop(corner_pin, "enabled", text="Enable Corner Pin")
        
        if not corner_pin.enabled:
            print("  - Corner pin is disabled")
            # 테스트 버튼은 항상 표시
            layout.operator("corner_pin.test_effect", text="Test Corner Pin", icon='NODE_MATERIAL')
            return
        
        print("  - Corner pin is enabled, drawing controls")
        
        # 테스트 버튼 (항상 맨 위에 표시)
        box = layout.box()
        box.alert = True  # 눈에 띄게 강조
        box.operator("corner_pin.test_effect", text="Test Corner Pin Effect", icon='NODE_MATERIAL')
        
        # 코너 위치 컨트롤
        box = layout.box()
        box.label(text="Corner Positions", icon='MESH_GRID')
        
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
        
        # 리셋 버튼
        row = box.row()
        row.operator("corner_pin.reset", text="Reset to Default", icon='LOOP_BACK')
        
        # 미세 조정 섹션
        box = layout.box()
        box.label(text="Fine Adjustment", icon='ARROW_LEFTRIGHT')
        
        # 코너 선택 및 미세 조정 UI
        row = box.row()
        col = row.column(align=True)
        
        # 각 코너에 대한 미세 조정 버튼
        for corner_name, corner_label in [
            ('top_left', 'Top Left'), 
            ('top_right', 'Top Right'), 
            ('bottom_left', 'Bottom Left'), 
            ('bottom_right', 'Bottom Right')
        ]:
            box.label(text=corner_label)
            row = box.row(align=True)
            
            # X축 조정
            op = row.operator("corner_pin.adjust_corner", text="X -", icon='TRIA_LEFT')
            op.corner = corner_name
            op.delta = (-0.01, 0.0)
            
            op = row.operator("corner_pin.adjust_corner", text="X +", icon='TRIA_RIGHT')
            op.corner = corner_name
            op.delta = (0.01, 0.0)
            
            # Y축 조정
            op = row.operator("corner_pin.adjust_corner", text="Y -", icon='TRIA_DOWN')
            op.corner = corner_name
            op.delta = (0.0, -0.01)
            
            op = row.operator("corner_pin.adjust_corner", text="Y +", icon='TRIA_UP')
            op.corner = corner_name
            op.delta = (0.0, 0.01)
        
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
        
        # 시각적 편집 모드 버튼 (하단에 배치)
        layout.separator()
        layout.operator("corner_pin.interactive_edit", text="Interactive Edit Mode", icon='RESTRICT_SELECT_OFF')

def register():
    print("corner_pin.panel.register() called")
    try:
        # 이미 등록된 경우 먼저 등록 해제 시도
        if hasattr(bpy.types, 'CORNER_PIN_PT_panel'):
            print("CORNER_PIN_PT_panel already registered, unregistering first")
            try:
                bpy.utils.unregister_class(CORNER_PIN_PT_panel)
                print("Successfully unregistered CORNER_PIN_PT_panel")
            except Exception as e:
                print(f"Failed to unregister CORNER_PIN_PT_panel: {e}")
        
        # 등록
        bpy.utils.register_class(CORNER_PIN_PT_panel)
        print("Successfully registered CORNER_PIN_PT_panel")
    except Exception as e:
        print(f"Error registering Corner Pin panel: {e}")

def unregister():
    print("corner_pin.panel.unregister() called")
    try:
        if hasattr(bpy.types, 'CORNER_PIN_PT_panel'):
            bpy.utils.unregister_class(CORNER_PIN_PT_panel)
            print("Successfully unregistered CORNER_PIN_PT_panel")
        else:
            print("CORNER_PIN_PT_panel not registered, nothing to unregister")
    except Exception as e:
        print(f"Error unregistering Corner Pin panel: {e}")