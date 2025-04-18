from .helper import get_projectors
from .projector import RESOLUTIONS, Textures

import bpy
from bpy.types import Panel, PropertyGroup, UIList, Operator


class PROJECTOR_PT_projector_settings(Panel):
    bl_idname = 'OBJECT_PT_projector_n_panel'
    bl_label = 'Projector'
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Projector"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row(align=True)
        row.operator('projector.create',
                    icon='ADD', text="New")
        row.operator('projector.delete',
                    text='Remove', icon='REMOVE')

        if context.scene.render.engine == 'BLENDER_EEVEE':
            box = layout.box()
            box.label(text='Image Projection only works in Cycles.', icon='ERROR')
            box.operator('projector.switch_to_cycles')

        selected_projectors = get_projectors(context, only_selected=True)
        if len(selected_projectors) == 1:
            projector = selected_projectors[0]
            proj_settings = projector.proj_settings

            layout.separator()

            layout.label(text='Projector Settings:')
            box = layout.box()
            
            # 렌즈 제한 확인
            throw_min = projector.get("throw_ratio_min", None)
            throw_max = projector.get("throw_ratio_max", None)
            h_min = projector.get("h_shift_min", None)
            h_max = projector.get("h_shift_max", None)
            v_min = projector.get("v_shift_min", None)
            v_max = projector.get("v_shift_max", None)
            
            # 범위 초과 확인
            throw_ratio_valid = True
            h_shift_valid = True
            v_shift_valid = True
            
            if throw_min is not None and throw_max is not None:
                throw_ratio_valid = throw_min <= proj_settings.throw_ratio <= throw_max
            
            if h_min is not None and h_max is not None:
                h_shift_valid = h_min <= proj_settings.h_shift <= h_max
                
            if v_min is not None and v_max is not None:
                v_shift_valid = v_min <= proj_settings.v_shift <= v_max
            
            # Throw Ratio 슬라이더
            row = box.row()
            row.prop(proj_settings, 'throw_ratio')
            
            box.prop(proj_settings, 'power', text='Power')
            
            # 해상도 설정
            res_row = box.row()
            res_row.prop(proj_settings, 'resolution',
                        text='Resolution', icon='PRESET')
            
            # 해상도 자동 감지 옵션
            box.prop(proj_settings, 'use_custom_texture_res', 
                     text='Use Image Resolution')
                
            # Lens Shift
            col = box.column(align=True)
            
            row = col.row()
            row.prop(proj_settings, 'h_shift', text='Horizontal Shift')
            
            row = col.row()
            row.prop(proj_settings, 'v_shift', text='Vertical Shift')
                
            # 픽셀 그리드 옵션
            box.prop(proj_settings, 'show_pixel_grid')

            # 텍스처 설정 섹션
            box = layout.box()
            box.label(text="Texture Settings")
            # 이미지 텍스처 선택
            node = projector.children[0].data.node_tree.nodes['Image Texture']
            box.template_image(node, 'image', node.image_user, compact=False)

            # 렌즈 정보 표시
            if hasattr(projector, "lens_manager") and projector.lens_manager.has_lens_selected:
                lens_props = projector.lens_manager
                box = layout.box()
                box.label(text=f"Using Lens: {lens_props.manufacturer} {lens_props.model}", icon='CAMERA_DATA')
                
                # 범위를 벗어난 값이 있으면 경고 표시
                if not all([throw_ratio_valid, h_shift_valid, v_shift_valid]):
                    row = box.row()
                    row.alert = True
                    row.label(text="Some values exceed lens limits", icon='ERROR')
                    # 허용 범위 표시
                    if not throw_ratio_valid and throw_min is not None and throw_max is not None:
                        row = box.row()
                        row.alert = True
                        row.label(text=f"Throw Ratio limits: {throw_min:.2f} - {throw_max:.2f}")
                    
                    if not h_shift_valid and h_min is not None and h_max is not None:
                        row = box.row()
                        row.alert = True
                        row.label(text=f"H-Shift limits: {h_min:.1f}% - {h_max:.1f}%")
                    
                    if not v_shift_valid and v_min is not None and v_max is not None:
                        row = box.row()
                        row.alert = True
                        row.label(text=f"V-Shift limits: {v_min:.1f}% - {v_max:.1f}%")


def append_to_add_menu(self, context):
    self.layout.operator('projector.create',
                         text='Projector', icon='CAMERA_DATA')


def register():
    bpy.utils.register_class(PROJECTOR_PT_projector_settings)
    # Register create in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.append(append_to_add_menu)
    
    # 코너 핀 UI 연결
    try:
        from . import corner_pin
        print("Corner Pin UI connected")
    except ImportError:
        print("Corner Pin module not found")
    except Exception as e:
        print(f"Error connecting corner pin UI: {e}")


def unregister():
    # Register create in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.remove(append_to_add_menu)
    bpy.utils.unregister_class(PROJECTOR_PT_projector_settings)