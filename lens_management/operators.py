# lens_management/operators.py 새로 생성:

import bpy
from bpy.types import Operator

class LENS_OT_apply_settings(Operator):
    """선택한 렌즈 설정을 현재 프로젝터에 적용"""
    bl_idname = "lens.apply_settings"
    bl_label = "Apply Lens Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'CAMERA' and obj.get('is_projector', False) and hasattr(obj, "lens_manager")
    
    def execute(self, context):
        obj = context.active_object
        lens_props = obj.lens_manager
        
        if not lens_props.manufacturer or not lens_props.model:
            self.report({'ERROR'}, "Please select a lens manufacturer and model first")
            return {'CANCELLED'}
            
        # 렌즈 프로필 가져오기
        from .database import lens_db
        profile = lens_db.get_lens_profile(lens_props.manufacturer, lens_props.model)
        if not profile:
            self.report({'ERROR'}, f"Lens profile not found for {lens_props.manufacturer} {lens_props.model}")
            return {'CANCELLED'}
            
        # projector.py의 update_from_lens_profile 함수 호출
        from .. import projector
        success = projector.update_from_lens_profile(obj, profile)
        
        if success:
            self.report({'INFO'}, f"Applied {lens_props.manufacturer} {lens_props.model} settings")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to apply lens settings")
            return {'CANCELLED'}

class LENS_OT_force_within_limits(Operator):
    """렌즈 제한 범위 내로 프로젝터 설정 강제 조정"""
    bl_idname = "lens.force_within_limits"
    bl_label = "Force Within Lens Limits"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'CAMERA' and obj.get('is_projector', False)
    
    def execute(self, context):
        obj = context.active_object
        proj_settings = obj.proj_settings
        
        # 제한 값 가져오기
        throw_min = obj.get("throw_ratio_min", None)
        throw_max = obj.get("throw_ratio_max", None)
        h_min = obj.get("h_shift_min", None)
        h_max = obj.get("h_shift_max", None)
        v_min = obj.get("v_shift_min", None)
        v_max = obj.get("v_shift_max", None)
        
        changes_made = False
        
        # Throw Ratio 조정
        if throw_min is not None and throw_max is not None:
            if proj_settings.throw_ratio < throw_min:
                proj_settings.throw_ratio = throw_min
                changes_made = True
            elif proj_settings.throw_ratio > throw_max:
                proj_settings.throw_ratio = throw_max
                changes_made = True
        
        # 수평 시프트 조정
        if h_min is not None and h_max is not None:
            if proj_settings.h_shift < h_min:
                proj_settings.h_shift = h_min
                changes_made = True
            elif proj_settings.h_shift > h_max:
                proj_settings.h_shift = h_max
                changes_made = True
        
        # 수직 시프트 조정
        if v_min is not None and v_max is not None:
            if proj_settings.v_shift < v_min:
                proj_settings.v_shift = v_min
                changes_made = True
            elif proj_settings.v_shift > v_max:
                proj_settings.v_shift = v_max
                changes_made = True
        
        # 설정 업데이트
        from .. import projector
        projector.update_throw_ratio(proj_settings, context)
        projector.update_lens_shift(proj_settings, context)
        
        if changes_made:
            self.report({'INFO'}, "Settings adjusted to lens limits")
        else:
            self.report({'INFO'}, "Settings already within lens limits")
            
        return {'FINISHED'}
    
# lens_management/operators.py에 추가할 코드

class LENS_OT_add_manufacturer(Operator):
    """새 제조사 추가"""
    bl_idname = "lens.add_manufacturer"
    bl_label = "Add Manufacturer"
    bl_options = {'REGISTER', 'UNDO'}
    
    name: bpy.props.StringProperty(name="Name", description="Manufacturer name")
    
    def execute(self, context):
        if not self.name:
            self.report({'ERROR'}, "Manufacturer name cannot be empty")
            return {'CANCELLED'}
                
        from .database import lens_db
        
        # 대소문자 구분 없이 중복 체크
        existing_manufacturers = lens_db.get_manufacturers()
        is_duplicate = False
        for existing in existing_manufacturers:
            if existing.upper() == self.name.upper():
                is_duplicate = True
                break
        
        if is_duplicate:
            self.report({'ERROR'}, f"Manufacturer '{self.name}' already exists (case-insensitive). Please use a different name.")
            return {'CANCELLED'}
        
        success = lens_db.add_manufacturer(self.name)
        
        if success:
            self.report({'INFO'}, f"Added manufacturer: {self.name}")
            
            # UI 업데이트를 위해 enum 속성 갱신
            context.scene.lens_manager_manufacturer = self.name
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to add manufacturer: {self.name}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")

class LENS_OT_edit_manufacturer(Operator):
    """제조사 편집"""
    bl_idname = "lens.edit_manufacturer"
    bl_label = "Edit Manufacturer"
    bl_options = {'REGISTER', 'UNDO'}
    
    manufacturer: bpy.props.StringProperty(name="Manufacturer")
    new_name: bpy.props.StringProperty(name="New Name")
    
    def execute(self, context):
        if not self.new_name:
            self.report({'ERROR'}, "New name cannot be empty")
            return {'CANCELLED'}
            
        from .database import lens_db
        success = lens_db.rename_manufacturer(self.manufacturer, self.new_name)
        
        if success:
            self.report({'INFO'}, f"Renamed manufacturer: {self.manufacturer} to {self.new_name}")
            
            # UI 업데이트
            if context.scene.lens_manager_manufacturer == self.manufacturer:
                context.scene.lens_manager_manufacturer = self.new_name
                
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to rename manufacturer")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        self.new_name = self.manufacturer
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

class LENS_OT_delete_manufacturer(Operator):
    """제조사 삭제"""
    bl_idname = "lens.delete_manufacturer"
    bl_label = "Delete Manufacturer"
    bl_options = {'REGISTER', 'UNDO'}
    
    manufacturer: bpy.props.StringProperty(name="Manufacturer")
    
    def execute(self, context):
        from .database import lens_db
        success = lens_db.delete_manufacturer(self.manufacturer)
        
        if success:
            self.report({'INFO'}, f"Deleted manufacturer: {self.manufacturer}")
            
            # UI 업데이트
            if context.scene.lens_manager_manufacturer == self.manufacturer:
                # 비워줌
                if len(lens_db.get_manufacturers()) > 0:
                    context.scene.lens_manager_manufacturer = lens_db.get_manufacturers()[0]
                else:
                    # enum 속성 갱신
                    context.scene.property_unset("lens_manager_manufacturer")
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to delete manufacturer")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

# lens_management/operators.py 내의 LENS_OT_add_model 클래스를 수정

class LENS_OT_add_model(Operator):
    """새 렌즈 모델 추가"""
    bl_idname = "lens.add_model"
    bl_label = "Add Lens Model"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 제조사 사용자 입력/선택 옵션
    use_existing_manufacturer: bpy.props.BoolProperty(
        name="Use Existing Manufacturer",
        default=True,
        description="기존 제조사 선택 또는 새 제조사 입력"
    )
    
    # 제조사를 EnumProperty로 구현
    def get_manufacturer_items(self, context):
        from .database import lens_db
        items = []
        manufacturers = lens_db.get_manufacturers()
        for i, manufacturer in enumerate(manufacturers):
            items.append((manufacturer, manufacturer, "", i))
        return items if items else [("", "No Manufacturers", "", 0)]
    
    manufacturer: bpy.props.EnumProperty(
        name="Manufacturer",
        description="Select lens manufacturer",
        items=get_manufacturer_items
    )
    
    # 새 제조사 이름 입력 필드
    new_manufacturer: bpy.props.StringProperty(
        name="New Manufacturer",
        description="Enter new manufacturer name"
    )
    
    model: bpy.props.StringProperty(name="Model ID", description="Lens model identifier")
    
    # 기본 렌즈 속성
    throw_min: bpy.props.FloatProperty(name="Min Throw Ratio", default=0.8, min=0.1, max=10.0)
    throw_max: bpy.props.FloatProperty(name="Max Throw Ratio", default=1.0, min=0.1, max=10.0)
    
    h_shift_min: bpy.props.FloatProperty(name="Min H-Shift (%)", default=-30.0, min=-100.0, max=100.0)
    h_shift_max: bpy.props.FloatProperty(name="Max H-Shift (%)", default=30.0, min=-100.0, max=100.0)
    v_shift_min: bpy.props.FloatProperty(name="Min V-Shift (%)", default=-50.0, min=-100.0, max=100.0)
    v_shift_max: bpy.props.FloatProperty(name="Max V-Shift (%)", default=50.0, min=-100.0, max=100.0)
    
    # 추가 정보
    notes: bpy.props.StringProperty(name="Notes", default="")
    
    def execute(self, context):
        if not self.model:
            self.report({'ERROR'}, "Model ID cannot be empty")
            return {'CANCELLED'}
        
        # 제조사 결정 (기존 또는 새로운 제조사)
        from .database import lens_db
        
        active_manufacturer = ""
        if self.use_existing_manufacturer:
            active_manufacturer = self.manufacturer
            if not active_manufacturer:
                self.report({'ERROR'}, "Please select a manufacturer")
                return {'CANCELLED'}
        else:
            # 새 제조사 유효성 검사
            if not self.new_manufacturer:
                self.report({'ERROR'}, "New manufacturer name cannot be empty")
                return {'CANCELLED'}
            
            # 대소문자 구분 없이 중복 체크
            existing_manufacturers = lens_db.get_manufacturers()
            is_duplicate = False
            for existing in existing_manufacturers:
                if existing.upper() == self.new_manufacturer.upper():
                    is_duplicate = True
                    break
            
            if is_duplicate:
                self.report({'ERROR'}, f"Manufacturer '{self.new_manufacturer}' already exists (case-insensitive)")
                return {'CANCELLED'}
            
            # 새 제조사 추가
            success = lens_db.add_manufacturer(self.new_manufacturer)
            if not success:
                self.report({'ERROR'}, f"Failed to add manufacturer: {self.new_manufacturer}")
                return {'CANCELLED'}
            
            active_manufacturer = self.new_manufacturer
        
        # 값 유효성 검사
        if self.throw_min > self.throw_max:
            self.report({'ERROR'}, "Throw ratio minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
            
        if self.h_shift_min > self.h_shift_max:
            self.report({'ERROR'}, "Horizontal shift minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
            
        if self.v_shift_min > self.v_shift_max:
            self.report({'ERROR'}, "Vertical shift minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
            
        # 모델 ID를 대문자로 변환
        model_id = self.model.upper()
        
        # 중복 확인 로직
        current_models = lens_db.get_models(active_manufacturer)
        
        if model_id in current_models:
            self.report({'ERROR'}, f"Model ID '{model_id}' already exists for {active_manufacturer}")
            return {'CANCELLED'}
        
        # 사양 데이터 모으기
        specs = {
            # Throw Ratio
            "throw_min": self.throw_min,
            "throw_max": self.throw_max,
            
            # 렌즈 시프트
            "h_shift_min": self.h_shift_min,
            "h_shift_max": self.h_shift_max,
            "v_shift_min": self.v_shift_min,
            "v_shift_max": self.v_shift_max,
            
            # 추가 정보
            "notes": self.notes
        }
        
        # 렌즈 모델 추가
        success = lens_db.add_lens_model(active_manufacturer, model_id, specs)
        
        if success:
            # UI 업데이트
            if not self.use_existing_manufacturer:
                try:
                    # 제조사 목록 갱신을 위해 Scene 속성 업데이트
                    context.scene.lens_manager_manufacturer = active_manufacturer
                except:
                    pass
            
            self.report({'INFO'}, f"Added model: {model_id} to {active_manufacturer}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to add model")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        from .database import lens_db
        
        # 제조사 목록 체크
        manufacturers = lens_db.get_manufacturers()
        if not manufacturers:
            # 제조사가 없으면 자동으로 새 제조사 입력 모드로 설정
            self.use_existing_manufacturer = False
        else:
            # 현재 선택된 제조사 확인
            try:
                if context.scene.lens_manager_manufacturer:
                    # 실제로 존재하는 제조사인지 확인
                    if context.scene.lens_manager_manufacturer in manufacturers:
                        # 선택된 제조사 설정
                        self.manufacturer = context.scene.lens_manager_manufacturer
            except:
                # 오류 발생 시 무시하고 계속 진행
                pass

        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        
        # 제조사 선택/입력 부분
        box = layout.box()
        box.label(text="Manufacturer")
        row = box.row()
        
        # 제조사 선택 방식 토글
        row.prop(self, "use_existing_manufacturer", text="Use Existing")
        
        if self.use_existing_manufacturer:
            # 기존 제조사 선택
            box.prop(self, "manufacturer", text="Select")
        else:
            # 새 제조사 이름 입력
            box.prop(self, "new_manufacturer", text="New Name")
        
        # 모델 ID 입력 필드
        layout.separator()
        box = layout.box()
        box.label(text="Model Information")
        box.prop(self, "model", text="Model ID")
        
        # 현재 입력된 모델 ID 검증 (기존 제조사 사용 시에만)
        if self.model and self.use_existing_manufacturer and self.manufacturer:
            from .database import lens_db
            model_id = self.model.upper()
            if model_id in lens_db.get_models(self.manufacturer):
                # 경고 메시지 표시
                row = box.row()
                row.alert = True
                row.label(text=f"Model ID '{model_id}' already exists!", icon='ERROR')
        
        # Throw Ratio
        layout.separator()
        box = layout.box()
        box.label(text="Throw Ratio")
        row = box.row()
        row.prop(self, "throw_min")
        row.prop(self, "throw_max")
        
        # Lens Shift Range
        layout.separator()
        box = layout.box()
        box.label(text="Lens Shift Range")
        row = box.row()
        row.prop(self, "h_shift_min")
        row.prop(self, "h_shift_max")
        row = box.row()
        row.prop(self, "v_shift_min")
        row.prop(self, "v_shift_max")
        
        # Additional Info
        layout.separator()
        box = layout.box()
        box.label(text="Additional Info")
        box.prop(self, "notes")

class LENS_OT_edit_model(Operator):
    """렌즈 모델 편집"""
    bl_idname = "lens.edit_model"
    bl_label = "Edit Lens Model"
    bl_options = {'REGISTER', 'UNDO'}
    
    manufacturer: bpy.props.StringProperty(name="Manufacturer")
    model: bpy.props.StringProperty(name="Model")
    new_model_id: bpy.props.StringProperty(name="Model ID", description="Change model identifier")
    
    # 기본 렌즈 속성 (최소값을 양수로도 설정 가능하도록 수정)
    throw_min: bpy.props.FloatProperty(name="Min Throw Ratio", default=0.8, min=0.1, max=10.0)
    throw_max: bpy.props.FloatProperty(name="Max Throw Ratio", default=1.0, min=0.1, max=10.0)
    
    h_shift_min: bpy.props.FloatProperty(name="Min H-Shift (%)", default=-30.0, min=-100.0, max=100.0)
    h_shift_max: bpy.props.FloatProperty(name="Max H-Shift (%)", default=30.0, min=-100.0, max=100.0)
    v_shift_min: bpy.props.FloatProperty(name="Min V-Shift (%)", default=-50.0, min=-100.0, max=100.0)
    v_shift_max: bpy.props.FloatProperty(name="Max V-Shift (%)", default=50.0, min=-100.0, max=100.0)
    
    # 추가 정보
    notes: bpy.props.StringProperty(name="Notes", default="")
    
    def execute(self, context):
        from .database import lens_db
        
        # 값 유효성 검사 추가
        if self.throw_min > self.throw_max:
            self.report({'ERROR'}, "Throw ratio minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
            
        if self.h_shift_min > self.h_shift_max:
            self.report({'ERROR'}, "Horizontal shift minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
            
        if self.v_shift_min > self.v_shift_max:
            self.report({'ERROR'}, "Vertical shift minimum value cannot be greater than maximum value")
            return {'CANCELLED'}
        
        # 모델명 변경 확인
        if self.new_model_id and self.new_model_id != self.model:
            # 새 모델명을 대문자로 변환
            new_model_id = self.new_model_id.upper()
            
            # 중복 체크
            if new_model_id in lens_db.get_models(self.manufacturer):
                self.report({'ERROR'}, f"Model ID '{new_model_id}' already exists")
                return {'CANCELLED'}
            
            # 모델명 변경 함수 호출 (database.py에 추가 필요)
            success = lens_db.rename_lens_model(self.manufacturer, self.model, new_model_id)
            if success:
                self.report({'INFO'}, f"Renamed model: {self.model} to {new_model_id}")
                # 모델 ID 업데이트
                old_model = self.model
                self.model = new_model_id
            else:
                self.report({'ERROR'}, f"Failed to rename model")
                return {'CANCELLED'}
        
        # 사양 데이터 모으기
        specs = {
            # Throw Ratio
            "throw_min": self.throw_min,
            "throw_max": self.throw_max,
            
            # 렌즈 시프트
            "h_shift_min": self.h_shift_min,
            "h_shift_max": self.h_shift_max,
            "v_shift_min": self.v_shift_min,
            "v_shift_max": self.v_shift_max,
            
            # 추가 정보
            "notes": self.notes
        }
        
        success = lens_db.update_lens_model(self.manufacturer, self.model, specs)
        
        if success:
            self.report({'INFO'}, f"Updated model: {self.model}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to update model")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        # 기존 값 로드
        from .database import lens_db
        
        # 현재 모델 ID를 new_model_id에도 설정
        self.new_model_id = self.model
        
        profile = lens_db.get_lens_profile(self.manufacturer, self.model)
        if profile and 'specs' in profile:
            specs = profile['specs']
            
            # Throw Ratio 로드
            if 'throw_ratio' in specs:
                throw_ratio = specs['throw_ratio']
                if isinstance(throw_ratio, dict):
                    self.throw_min = throw_ratio.get('min', 0.8)
                    self.throw_max = throw_ratio.get('max', 1.0)
            
            # Lens Shift 로드
            if 'lens_shift' in specs:
                lens_shift = specs['lens_shift']
                if 'h_shift_range' in lens_shift:
                    self.h_shift_min, self.h_shift_max = lens_shift['h_shift_range']
                if 'v_shift_range' in lens_shift:
                    self.v_shift_min, self.v_shift_max = lens_shift['v_shift_range']
            
            # 메모 로드
            if 'notes' in specs:
                self.notes = specs['notes']
            
            # Optical Properties 로드 부분 제거
        
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def draw(self, context):
        layout = self.layout
        
        # 모델 ID 수정 필드 추가
        box = layout.box()
        box.label(text="Model Information")
        box.prop(self, "new_model_id", text="Model ID")
        
        # 현재 입력된 모델 ID 검증
        if self.new_model_id and self.new_model_id != self.model:
            from .database import lens_db
            new_id = self.new_model_id.upper()
            if new_id in lens_db.get_models(self.manufacturer):
                # 경고 메시지 표시
                row = box.row()
                row.alert = True
                row.label(text=f"Model ID '{new_id}' already exists!", icon='ERROR')
        
        # Throw Ratio
        box = layout.box()
        box.label(text="Throw Ratio")
        row = box.row()
        row.prop(self, "throw_min")
        row.prop(self, "throw_max")
        
        # Lens Shift Range
        box = layout.box()
        box.label(text="Lens Shift Range")
        row = box.row()
        row.prop(self, "h_shift_min")
        row.prop(self, "h_shift_max")
        row = box.row()
        row.prop(self, "v_shift_min")
        row.prop(self, "v_shift_max")
        
        # Additional Info
        box = layout.box()
        box.label(text="Additional Info")
        box.prop(self, "notes")

class LENS_OT_delete_model(Operator):
    """렌즈 모델 삭제"""
    bl_idname = "lens.delete_model"
    bl_label = "Delete Lens Model"
    bl_options = {'REGISTER', 'UNDO'}
    
    manufacturer: bpy.props.StringProperty(name="Manufacturer")
    model: bpy.props.StringProperty(name="Model")
    
    def execute(self, context):
        from .database import lens_db
        success = lens_db.delete_lens_model(self.manufacturer, self.model)
        
        if success:
            self.report({'INFO'}, f"Deleted model: {self.model}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Failed to delete model")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

class LENS_OT_import_database(Operator):
    """JSON 파일에서 렌즈 데이터 가져오기"""
    bl_idname = "lens.import_database"
    bl_label = "Import Lens Database"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="JSON 파일 경로",
        default="",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def execute(self, context):
        from .database import lens_db
        
        success, message = lens_db.import_database(self.filepath)
        
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
class LENS_OT_export_database(Operator):
    """렌즈 데이터를 JSON 파일로 내보내기"""
    bl_idname = "lens.export_database"
    bl_label = "Export Lens Database"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="JSON 파일 경로",
        default="",
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    export_all: bpy.props.BoolProperty(
        name="Export All Manufacturers",
        description="현재 선택된 제조사만 내보내지 않고 모든 제조사 데이터 내보내기",
        default=False
    )
    
    def execute(self, context):
        from .database import lens_db
        
        # 현재 선택된 제조사가 있고 모든 제조사 내보내기가 아니면 선택된 것만 내보내기
        manufacturer = None
        if not self.export_all and context.scene.lens_manager_manufacturer:
            manufacturer = context.scene.lens_manager_manufacturer
        
        success, message = lens_db.export_database(self.filepath, manufacturer)
        
        if success:
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        # 기본 파일명 설정
        if context.scene.lens_manager_manufacturer and not self.export_all:
            self.filepath = f"{context.scene.lens_manager_manufacturer.lower()}.json"
        else:
            self.filepath = "lens_database.json"
            
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
        
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "export_all")
        
class LENS_OT_refresh_database(Operator):
    """렌즈 데이터베이스 새로고침"""
    bl_idname = "lens.refresh_database"
    bl_label = "Refresh Lens Database"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from .database import lens_db
        success = lens_db.refresh_database()
        
        if success:
            self.report({'INFO'}, "Lens database refreshed successfully")
        else:
            self.report({'ERROR'}, "Failed to refresh lens database")
        
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(LENS_OT_apply_settings)
    bpy.utils.register_class(LENS_OT_force_within_limits)  # 이 줄을 추가해야 함
    
    # 새 오퍼레이터들 등록
    bpy.utils.register_class(LENS_OT_add_manufacturer)
    bpy.utils.register_class(LENS_OT_edit_manufacturer)
    bpy.utils.register_class(LENS_OT_delete_manufacturer)
    bpy.utils.register_class(LENS_OT_add_model)
    bpy.utils.register_class(LENS_OT_edit_model)
    bpy.utils.register_class(LENS_OT_delete_model)
    bpy.utils.register_class(LENS_OT_import_database)
    bpy.utils.register_class(LENS_OT_export_database)
    bpy.utils.register_class(LENS_OT_refresh_database)

def unregister():
    # 새 오퍼레이터들 등록 해제
    bpy.utils.unregister_class(LENS_OT_refresh_database)
    bpy.utils.unregister_class(LENS_OT_export_database)
    bpy.utils.unregister_class(LENS_OT_import_database)
    bpy.utils.unregister_class(LENS_OT_delete_model)
    bpy.utils.unregister_class(LENS_OT_edit_model)
    bpy.utils.unregister_class(LENS_OT_add_model)
    bpy.utils.unregister_class(LENS_OT_delete_manufacturer)
    bpy.utils.unregister_class(LENS_OT_edit_manufacturer)
    bpy.utils.unregister_class(LENS_OT_add_manufacturer)
    bpy.utils.unregister_class(LENS_OT_force_within_limits)  # 이 줄을 추가해야 함
    bpy.utils.unregister_class(LENS_OT_apply_settings)