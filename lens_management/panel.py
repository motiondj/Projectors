import bpy
from bpy.types import Panel
from .database import lens_db
from . import properties

class LENS_PT_main_panel(Panel):
    bl_label = "Lens Management"
    bl_idname = "LENS_PT_main_panel"
    bl_space_type = 'VIEW_3D'  
    bl_region_type = 'UI'
    bl_category = "Projector"
    bl_context = "objectmode"  # 오브젝트 모드에서만 표시
    #bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        # 특정 모드나 컨텍스트에서만 활성화
        if context.mode != 'OBJECT':
            return False
            
        # active_object가 아닌 selected_objects 검사
        projectors = [obj for obj in context.selected_objects 
                    if obj.type == 'CAMERA' and obj.get('is_projector', False)]
        
        # 프로젝터가 정확히 하나만 선택되었을 때만 패널 표시
        return len(projectors) == 1
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        obj = context.active_object
        
        if not hasattr(obj, "lens_manager"):
            layout.label(text="Lens management system is not activated")
            return
            
        lens_props = obj.lens_manager
        
        # Lens Information
        box = layout.box()
        box.label(text="Lens Information", icon='CAMERA_DATA')
        
        # Manufacturer selection
        row = box.row()
        manufacturers = lens_db.get_manufacturers()
        if manufacturers:
            row.prop(lens_props, "manufacturer", text="Manufacturer")
                       
        # Model selection
        if lens_props.manufacturer:
            models = lens_db.get_models(lens_props.manufacturer)
            if models:
                row = box.row()
                row.prop(lens_props, "model", text="Model")
                          
        # Lens Specifications
        if lens_props.manufacturer and lens_props.model:
            profile = lens_db.get_lens_profile(lens_props.manufacturer, lens_props.model)
            if profile and 'specs' in profile:
                specs = profile['specs']
                box = layout.box()
                box.label(text="Lens Specifications", icon='INFO')
                
                col = box.column(align=True)
                
                # Throw Ratio
                if 'throw_ratio' in specs:
                    throw_ratio = specs['throw_ratio']
                    row = col.row()
                    if isinstance(throw_ratio, dict):
                        min_val = throw_ratio.get('min', 0)
                        max_val = throw_ratio.get('max', 0)
                        if min_val == max_val:
                            row.label(text=f"Throw Ratio: {min_val:0.2f}:1")
                        else:
                            row.label(text=f"Throw Ratio: {min_val:0.2f}:1 to {max_val:0.2f}:1")
                    elif isinstance(throw_ratio, str):
                        row.label(text=f"Throw Ratio: {throw_ratio}")
                    else:
                        row.label(text=f"Throw Ratio: {throw_ratio:0.2f}:1")
                
                # Focal Length
                if 'focal_length' in specs:
                    focal_length = specs['focal_length']
                    row = col.row()
                    if isinstance(focal_length, dict):
                        min_val = focal_length.get('min', 0)
                        max_val = focal_length.get('max', 0)
                        if min_val == max_val:
                            row.label(text=f"Focal Length: {min_val:0.1f}mm")
                        else:
                            row.label(text=f"Focal Length: {min_val:0.1f}mm to {max_val:0.1f}mm")
                
                # F-Stop
                if 'f_stop' in specs:
                    f_stop = specs['f_stop']
                    row = col.row()
                    if isinstance(f_stop, dict):
                        min_val = f_stop.get('min', 0)
                        max_val = f_stop.get('max', 0)
                        if min_val == max_val:
                            row.label(text=f"F-Stop: f/{min_val:0.1f}")
                        else:
                            row.label(text=f"F-Stop: f/{min_val:0.1f} to f/{max_val:0.1f}")
                
                # Lens Shift Range
                if 'lens_shift' in specs:
                    shift = specs['lens_shift']
                    col.separator()
                    col.label(text="Lens Shift Range:")
                    
                    if 'h_shift_range' in shift:
                        h_min, h_max = shift['h_shift_range']
                        row = col.row()
                        row.label(text=f"Horizontal: {h_min:0.1f}% to {h_max:0.1f}%")
                        
                    if 'v_shift_range' in shift:
                        v_min, v_max = shift['v_shift_range']
                        row = col.row()
                        row.label(text=f"Vertical: {v_min:0.1f}% to {v_max:0.1f}%")
                
                # Zoom
                if 'zoom' in specs:
                    col.separator()
                    row = col.row()
                    zoom = specs['zoom']
                    row.label(text=f"Zoom: {zoom:0.1f}x")
                    
                # Additional Info
                if 'notes' in specs:
                    col.separator()
                    row = col.row()
                    row.label(text=f"Notes: {specs['notes']}")
                    
        # 렌즈 컨트롤 부분 수정
        if lens_props.manufacturer and lens_props.model:
            box = layout.box()
            box.label(text="Lens Status", icon='INFO')
            box.label(text=f"Using: {lens_props.manufacturer} {lens_props.model}")
            box.label(text="Settings automatically applied", icon='CHECKMARK')

def register():
    bpy.utils.register_class(LENS_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(LENS_PT_main_panel)