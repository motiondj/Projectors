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
            res_row = box.row()
            res_row.prop(proj_settings, 'resolution',
                        text='Resolution', icon='PRESET')
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value and proj_settings.use_custom_texture_res:
                res_row.active = False
                res_row.enabled = False
            else:
                res_row.active = True
                res_row.enabled = True
                
            # Lens Shift
            col = box.column(align=True)
            
            row = col.row()
            row.prop(proj_settings, 'h_shift', text='Horizontal Shift')
            
            row = col.row()
            row.prop(proj_settings, 'v_shift', text='Vertical Shift')
                
            layout.prop(proj_settings,
                        'projected_texture', text='Project')
            # Pixel Grid
            box.prop(proj_settings, 'show_pixel_grid')

            # Custom Texture
            if proj_settings.projected_texture == Textures.CUSTOM_TEXTURE.value:
                box = layout.box()
                box.prop(proj_settings, 'use_custom_texture_res')
                node = get_projectors(context, only_selected=True)[
                    0].children[0].data.node_tree.nodes['Image Texture']
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
                    

class PROJECTOR_PT_projected_color(Panel):
    bl_label = "Projected Color"
    bl_parent_id = "OBJECT_PT_projector_n_panel"
    bl_option = {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    @classmethod
    def poll(self, context):
        """ Only show if projected texture is set to  'checker'."""
        projector = context.object
        return bool(get_projectors(context, only_selected=True)) and projector.proj_settings.projected_texture == Textures.CHECKER.value

    def draw(self, context):
        projector = context.object
        layout = self.layout
        layout.use_property_decorate = False
        col = layout.column()
        col.use_property_split = True
        col.prop(projector.proj_settings, 'projected_color', text='Color')
        col.operator('projector.change_color',
                     icon='MODIFIER_ON', text='Random Color')


def append_to_add_menu(self, context):
    self.layout.operator('projector.create',
                         text='Projector', icon='CAMERA_DATA')


def register():
    bpy.utils.register_class(PROJECTOR_PT_projector_settings)
    bpy.utils.register_class(PROJECTOR_PT_projected_color)
    # Register create  in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.append(append_to_add_menu)


def unregister():
    # Register create in the blender add menu.
    bpy.types.VIEW3D_MT_light_add.remove(append_to_add_menu)
    bpy.utils.unregister_class(PROJECTOR_PT_projected_color)
    bpy.utils.unregister_class(PROJECTOR_PT_projector_settings)
