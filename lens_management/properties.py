import bpy
from bpy.props import EnumProperty, PointerProperty, BoolProperty, StringProperty
from .database import lens_db

# 캐싱을 위한 전역 변수
_cached_manufacturers = None
_cached_models = {}
_last_update_time = 0

def update_lens_settings(self, context):
    """렌즈 선택시 프로젝터 설정 자동 업데이트"""
    from .database import lens_db
    
    # 렌즈가 선택되지 않은 경우
    if not self.manufacturer or self.manufacturer == "NONE" or not self.model or self.model == "NONE":
        # 기존 렌즈 제한 초기화 (선택적)
        obj = context.active_object
        if obj and hasattr(obj, "proj_settings"):
            # 렌즈 제한 초기화
            for attr in ["throw_ratio_min", "throw_ratio_max", "h_shift_min", "h_shift_max", "v_shift_min", "v_shift_max"]:
                if attr in obj:
                    del obj[attr]
            # 선택 상태 업데이트
            self.has_lens_selected = False
            # 저장된 렌즈 정보 제거
            if "lens_manufacturer" in obj: del obj["lens_manufacturer"]
            if "lens_model" in obj: del obj["lens_model"]
        return
        
    # 렌즈 프로필 가져오기
    profile = lens_db.get_lens_profile(self.manufacturer, self.model)
    if not profile:
        return
        
    obj = context.active_object
    if not obj or not hasattr(obj, "proj_settings"):
        return
    
    # 기존 제한값 초기화 
    for attr in ["throw_ratio_min", "throw_ratio_max", "h_shift_min", "h_shift_max", "v_shift_min", "v_shift_max"]:
        if attr in obj:
            del obj[attr]
    
    # 렌즈가 선택되었음을 기록
    self.has_lens_selected = True
    
    # 렌즈 정보를 프로젝터 객체에 저장 (추적용)
    obj["lens_manufacturer"] = self.manufacturer
    obj["lens_model"] = self.model
    
    # Throw Ratio를 최소값으로 명시적 설정
    if 'specs' in profile and 'throw_ratio' in profile['specs']:
        throw_ratio = profile['specs']['throw_ratio']
        if isinstance(throw_ratio, dict) and 'min' in throw_ratio:
            min_val = throw_ratio['min']
            obj.proj_settings.throw_ratio = min_val
            print(f"Setting throw ratio to minimum value: {min_val}")
    
    # Lens Shift 초기화 (중간값 또는 0으로)
    if 'specs' in profile and 'lens_shift' in profile['specs']:
        lens_shift = profile['specs']['lens_shift']
        # 수평 시프트
        if 'h_shift_range' in lens_shift:
            h_min, h_max = lens_shift['h_shift_range']
            h_center = 0.0 if (h_min <= 0 <= h_max) else (h_min + h_max) / 2
            obj.proj_settings.h_shift = h_center
            print(f"Setting h_shift to: {h_center}")
        
        # 수직 시프트
        if 'v_shift_range' in lens_shift:
            v_min, v_max = lens_shift['v_shift_range']
            v_center = 0.0 if (v_min <= 0 <= v_max) else (v_min + v_max) / 2
            obj.proj_settings.v_shift = v_center
            print(f"Setting v_shift to: {v_center}")
    
    # 그 다음 프로필 적용
    from .. import projector
    projector.update_from_lens_profile(obj, profile)

def update_manufacturer(self, context):
    """제조사 선택 시 첫 번째 렌즈 자동 선택 및 적용"""
    from .database import lens_db
    
    if not self.manufacturer or self.manufacturer == "none":
        # 제조사가 선택되지 않은 경우 모델 목록을 비움
        self.model = "NONE"  # 빈 문자열("") 대신 "NONE" 사용
        self.has_lens_selected = False
        return
        
    # 선택된 제조사의 모델 목록 가져오기
    models = lens_db.get_models(self.manufacturer)
    if models:
        # 첫 번째 모델 선택 (현재 모델 저장)
        current_model = self.model  # 현재 모델 저장
        self.model = models[0]  # 새 모델 설정 (이렇게 하면 update_lens_settings가 호출됨)
        
        # 렌즈 설정 직접 업데이트 - 중복 호출 방지를 위해 조건 추가
        if current_model != models[0]:
            obj = context.active_object
            if obj and hasattr(obj, "proj_settings"):
                # 프로필 가져오기
                profile = lens_db.get_lens_profile(self.manufacturer, models[0])
                if profile and 'specs' in profile and 'throw_ratio' in profile['specs']:
                    throw_ratio = profile['specs']['throw_ratio']
                    if isinstance(throw_ratio, dict) and 'min' in throw_ratio:
                        # throw_ratio 값을 최소값으로 직접 설정
                        obj.proj_settings.throw_ratio = throw_ratio['min']
                        print(f"Set throw ratio to minimum: {throw_ratio['min']}")
    else:
        # 모델이 없으면 빈 값으로 설정
        self.model = ""
        self.has_lens_selected = False

def get_manufacturers(self, context):
    """제조사 목록을 가져오는 함수 (캐싱 기능 포함)"""
    global _cached_manufacturers, _last_update_time
    
    import time
    current_time = time.time()
    
    # 캐시 업데이트 간격 (1초)
    if _cached_manufacturers is None or current_time - _last_update_time > 1.0:
        manufacturers = lens_db.get_manufacturers()
        
        # "None" 옵션을 첫번째로 추가
        result = [("none", "None", "No lens selected", 0)]
        
        # 실제 제조사 목록 추가 (1부터 시작하는 인덱스 부여)
        for i, m in enumerate(manufacturers):
            result.append((m, m, "", i+1))
        
        _cached_manufacturers = result
        _last_update_time = current_time
        
    return _cached_manufacturers

def get_models(self, context):
    """선택된 제조사의 모델 목록을 가져오는 함수 (캐싱 기능 포함)"""
    global _cached_models
    
    manufacturer = self.manufacturer
    
    # 제조사 선택되지 않았을 때 기본 항목 제공
    if not manufacturer or manufacturer == "none":
        return [("NONE", "None", "No lens selected", 0)]
    
    # 캐시에 없거나 캐시 업데이트가 필요한 경우
    if manufacturer not in _cached_models:
        models = lens_db.get_models(manufacturer)
        
        if not models:
            result = [("NONE", "No models available", "", 0)]
        else:
            # 항목에 인덱스 부여 (0부터 시작)
            result = [(m, m, "", i) for i, m in enumerate(models)]
        
        _cached_models[manufacturer] = result
    
    return _cached_models[manufacturer]

def clear_cache():
    """캐시 초기화 함수 - 데이터베이스 갱신 시 호출"""
    global _cached_manufacturers, _cached_models, _last_update_time
    _cached_manufacturers = None
    _cached_models = {}
    _last_update_time = 0

class LensManagerProperties(bpy.types.PropertyGroup):
    manufacturer: EnumProperty(
        name="Manufacturer",
        description="Lens manufacturer",
        items=get_manufacturers,
        update=update_manufacturer,
        default=0  # 인덱스 0(첫 번째 항목)을 기본값으로 설정
    )
    
    model: EnumProperty(
        name="Model",
        description="Lens model",
        items=get_models,
        update=update_lens_settings,
        default=0  # 인덱스 0(첫 번째 항목)을 기본값으로 설정
    )
    
    has_lens_selected: BoolProperty(
        name="Has Lens Selected",
        description="Whether a lens has been selected",
        default=False
    )
    
    # 에러 메시지를 저장하기 위한 속성 추가
    error_message: StringProperty(
        name="Error Message",
        description="Error message if any",
        default=""
    )
    
    def restore_lens_selection(self, context):
        """프로젝터 객체에 저장된 렌즈 정보 복원"""
        obj = context.active_object
        if not obj:
            return False
            
        saved_manufacturer = obj.get("lens_manufacturer", "")
        saved_model = obj.get("lens_model", "")
        
        if saved_manufacturer and saved_model:
            # 캐시 초기화 (복원 시 최신 데이터 사용)
            clear_cache()
            
            # 제조사 목록 먼저 업데이트
            manufacturers = get_manufacturers(self, context)
            valid_manufacturers = [m[0] for m in manufacturers if m[0] != "NONE"]
            
            if saved_manufacturer in valid_manufacturers:
                self.manufacturer = saved_manufacturer
                
                # 모델 목록 업데이트
                models = get_models(self, context)
                valid_models = [m[0] for m in models if m[0] != "NONE"]
                
                if saved_model in valid_models:
                    self.model = saved_model
                    self.has_lens_selected = True
                    return True
            
            # 저장된 값이 유효하지 않은 경우는 기본값으로 설정
            self.manufacturer = "NONE"
            self.model = "NONE"
            self.error_message = f"Saved lens {saved_manufacturer} {saved_model} not found in database"
                    
        return False
    
    def init(self, context):
        """EnumProperty 초기화 및 유효성 검증"""
        # 기본값으로 강제 설정
        self.manufacturer = 0  # 첫 번째 항목 선택
        self.model = 0  # 첫 번째 항목 선택
        self.has_lens_selected = False
        
        # 캐시 초기화
        clear_cache()

def register():
    try:
        print("Attempting to register LensManagerProperties...")
        bpy.utils.register_class(LensManagerProperties)
        bpy.types.Object.lens_manager = PointerProperty(type=LensManagerProperties)
        print("Successfully registered LensManagerProperties")
    except Exception as e:
        print(f"Failed to register LensManagerProperties: {str(e)}")

def unregister():
    try:
        if hasattr(bpy.types.Object, "lens_manager"):
            del bpy.types.Object.lens_manager
        bpy.utils.unregister_class(LensManagerProperties)
    except Exception as e:
        print(f"Failed to unregister LensManagerProperties: {str(e)}")