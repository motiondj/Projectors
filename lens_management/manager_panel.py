# lens_management/manager_panel.py
import bpy
from bpy.types import Panel, UIList, Operator
from .database import lens_db

class LENS_PT_management_panel(Panel):
    bl_label = "Lens Management"
    bl_idname = "LENS_PT_management_panel"
    bl_space_type = 'VIEW_3D'  
    bl_region_type = 'UI'
    bl_category = "Lens Manager"  # 새로운 탭 이름
    bl_context = "objectmode"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # 통합된 렌즈 모델 섹션
        box = layout.box()
        box.label(text="Lens Models", icon='CAMERA_DATA')
        
        # 제조사 선택 드롭다운 (필터링 용도)
        row = box.row()
        row.prop(context.scene, "lens_manager_manufacturer", text="Filter by Manufacturer")
        
        # 제조사별 모델 목록 표시
        if context.scene.lens_manager_manufacturer:
            models = lens_db.get_models(context.scene.lens_manager_manufacturer)
            col = box.column()
            
            for model in models:
                row = col.row()
                row.label(text=f"{context.scene.lens_manager_manufacturer}: {model}")
                
                # 모델 편집/삭제 버튼
                op = row.operator("lens.edit_model", text="", icon='MODIFIER')
                op.manufacturer = context.scene.lens_manager_manufacturer
                op.model = model
                
                op = row.operator("lens.delete_model", text="", icon='X')
                op.manufacturer = context.scene.lens_manager_manufacturer
                op.model = model
        else:
            # 모든 제조사의 모델 표시
            col = box.column()
            for manufacturer in lens_db.get_manufacturers():
                models = lens_db.get_models(manufacturer)
                if models:  # 모델이 있는 제조사만 표시
                    box.label(text=f"{manufacturer}:", icon='OUTLINER_OB_CAMERA')
                    for model in models:
                        row = col.row()
                        row.label(text=f"    {model}")
                        
                        # 모델 편집/삭제 버튼
                        op = row.operator("lens.edit_model", text="", icon='MODIFIER')
                        op.manufacturer = manufacturer
                        op.model = model
                        
                        op = row.operator("lens.delete_model", text="", icon='X')
                        op.manufacturer = manufacturer
                        op.model = model
        
        # 새 모델 추가 버튼
        box.operator("lens.add_model", icon='ADD')
        
        # 데이터 관리 섹션
        box = layout.box()
        box.label(text="Database Operations", icon='FILE')
        row = box.row(align=True)
        row.operator("lens.import_database", icon='IMPORT')
        row.operator("lens.export_database", icon='EXPORT')
        row.operator("lens.refresh_database", icon='FILE_REFRESH')

# 제조사 선택용 Enum 속성을 위한 함수
def get_manufacturer_items(self, context):
    items = []
    manufacturers = lens_db.get_manufacturers()
    for i, manufacturer in enumerate(manufacturers):
        items.append((manufacturer, manufacturer, "", i))
    return items if items else [("", "No Manufacturers", "", 0)]

def register():
    bpy.utils.register_class(LENS_PT_management_panel)
    bpy.types.Scene.lens_manager_manufacturer = bpy.props.EnumProperty(
        name="Manufacturer",
        items=get_manufacturer_items
    )

def unregister():
    del bpy.types.Scene.lens_manager_manufacturer
    bpy.utils.unregister_class(LENS_PT_management_panel)