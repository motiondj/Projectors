import json
import os
import bpy
from pathlib import Path
import time

class LensDatabase:
    def __init__(self):
        self.manufacturers = {}
        self.cache = {}  # 캐싱을 위한 딕셔너리
        self.last_load_time = {}  # 각 파일별 마지막 로드 시간
        self.load_all_databases()
    
    def load_all_databases(self):
        """모든 제조사의 렌즈 데이터베이스를 로드"""
        database_dir = Path(__file__).parent / "database"
        if not database_dir.exists():
            database_dir.mkdir(exist_ok=True)
            
        for json_file in database_dir.glob("*.json"):
            self.load_manufacturer_database(json_file)
    
    def load_manufacturer_database(self, json_file):
        """특정 제조사의 렌즈 데이터베이스를 로드"""
        manufacturer = json_file.stem.capitalize()
        file_mtime = os.path.getmtime(json_file)
        
        # 파일이 수정되지 않았고 캐시에 있으면 캐시 사용
        if manufacturer in self.last_load_time and file_mtime <= self.last_load_time[manufacturer]:
            if manufacturer in self.cache:
                self.manufacturers[manufacturer] = self.cache[manufacturer]
                print(f"Using cached data for {manufacturer}")
                return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 데이터 표준화 처리
                standardized_data = self.standardize_lens_data(data)
                self.manufacturers[manufacturer] = standardized_data
                # 캐시 업데이트
                self.cache[manufacturer] = standardized_data
                self.last_load_time[manufacturer] = file_mtime
                print(f"Loaded lens database for {manufacturer}")
        except json.JSONDecodeError as e:
            self.handle_json_error(json_file, e)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    def handle_json_error(self, json_file, error):
        """JSON 오류 처리"""
        error_msg = f"Error in {json_file.name}: {str(error)}"
        # 콘솔에 오류 메시지 출력
        print(error_msg)
        # 가능하다면 블렌더 UI에 오류 메시지 표시
        try:
            def draw(self, context):
                self.layout.label(text=error_msg)
            
            bpy.context.window_manager.popup_menu(draw, title="JSON Error", icon='ERROR')
        except:
            pass
    
    def standardize_lens_data(self, data):
        """렌즈 데이터를 표준 형식으로 변환"""
        standardized = {}
        
        for model, model_data in data.items():
            standardized[model] = model_data.copy()
            
            if 'specs' in model_data:
                specs = model_data['specs']
                
                # throw_ratio 표준화
                if 'throw_ratio' in specs:
                    throw_ratio = specs['throw_ratio']
                    # 문자열 형식인 경우 파싱
                    if isinstance(throw_ratio, str):
                        min_ratio, max_ratio = self.parse_throw_ratio(throw_ratio)
                        standardized[model]['specs']['throw_ratio'] = {
                            "min": min_ratio,
                            "max": max_ratio,
                            "default": (min_ratio + max_ratio) / 2
                        }
                    # 단일 숫자인 경우
                    elif isinstance(throw_ratio, (int, float)):
                        standardized[model]['specs']['throw_ratio'] = {
                            "min": float(throw_ratio),
                            "max": float(throw_ratio),
                            "default": float(throw_ratio)
                        }
                    # 이미 사전 형식인 경우 그대로 유지
        
        return standardized
    
    def parse_throw_ratio(self, ratio_str):
        """throw ratio 문자열을 파싱하여 (최소값, 최대값) 반환"""
        try:
            if ' to ' in ratio_str:
                min_str, max_str = ratio_str.split(' to ')
                min_ratio = float(min_str.split(':')[0].strip())
                max_ratio = float(max_str.split(':')[0].strip())
            else:
                # "1.45:1" 형식
                ratio = float(ratio_str.split(':')[0].strip())
                min_ratio = max_ratio = ratio
            return min_ratio, max_ratio
        except:
            # 파싱 실패 시 기본값 반환
            return 1.0, 1.0
    
    def refresh_database(self):
        """데이터베이스를 강제로 새로고침"""
        self.manufacturers = {}
        self.cache = {}
        self.last_load_time = {}
        self.load_all_databases()
        return len(self.manufacturers) > 0
    
    def get_manufacturers(self):
        """사용 가능한 제조사 목록 반환"""
        manufacturers = sorted(self.manufacturers.keys())
        if not manufacturers:
            # 제조사가 없는 경우 기본값 반환
            print("Warning: No manufacturers found in the database")
        return manufacturers
    
    def get_models(self, manufacturer):
        """특정 제조사의 렌즈 모델 목록 반환"""
        if manufacturer in self.manufacturers:
            return sorted(self.manufacturers[manufacturer].keys())
        return []
    
    def get_lens_profile(self, manufacturer, model):
        """특정 렌즈의 프로필 데이터 반환"""
        if manufacturer in self.manufacturers:
            if model in self.manufacturers[manufacturer]:
                return self.manufacturers[manufacturer][model]
        return None
    
    def get_throw_ratio_limits(self, manufacturer, model):
        """특정 렌즈의 throw ratio 제한값 반환"""
        profile = self.get_lens_profile(manufacturer, model)
        if profile and 'specs' in profile:
            specs = profile['specs']
            if 'throw_ratio' in specs:
                throw_ratio = specs['throw_ratio']
                if isinstance(throw_ratio, dict) and 'min' in throw_ratio and 'max' in throw_ratio:
                    return throw_ratio['min'], throw_ratio['max']
        return None
    
    def get_lens_shift_limits(self, manufacturer, model, is_horizontal=True):
        """렌즈의 시프트 제한값 반환"""
        profile = self.get_lens_profile(manufacturer, model)
        if profile and 'specs' in profile:
            specs = profile['specs']
            if 'lens_shift' in specs:
                lens_shift = specs['lens_shift']
                if is_horizontal and 'h_shift_range' in lens_shift:
                    return tuple(lens_shift['h_shift_range'])
                elif not is_horizontal and 'v_shift_range' in lens_shift:
                    return tuple(lens_shift['v_shift_range'])
        return None
    
    def validate_database(self):
        """데이터베이스의 모든 렌즈 데이터를 검증"""
        all_errors = {}
        
        for manufacturer, lens_data in self.manufacturers.items():
            errors = validate_lens_data(lens_data)
            if errors:
                all_errors[manufacturer] = errors
        
        return all_errors
    
    def add_manufacturer(self, name):
        """새 제조사 추가
        
        Args:
            name (str): 제조사 이름
            
        Returns:
            bool: 성공 여부
        """
        if not name or name in self.manufacturers:
            return False
        
        # 새 제조사 데이터 초기화
        self.manufacturers[name] = {}
        
        # JSON 파일 생성 및 저장
        self._save_manufacturer_data(name)
        
        return True

    def rename_manufacturer(self, old_name, new_name):
        """제조사 이름 변경
        
        Args:
            old_name (str): 현재 제조사 이름
            new_name (str): 새 제조사 이름
            
        Returns:
            bool: 성공 여부
        """
        if not old_name or not new_name or old_name not in self.manufacturers:
            return False
        
        if new_name in self.manufacturers:
            return False  # 이미 같은 이름의 제조사가 존재
        
        # 데이터 복사
        self.manufacturers[new_name] = self.manufacturers[old_name]
        
        # 기존 제조사 삭제
        del self.manufacturers[old_name]
        
        # 캐시 업데이트
        if old_name in self.cache:
            self.cache[new_name] = self.cache[old_name]
            del self.cache[old_name]
        
        if old_name in self.last_load_time:
            self.last_load_time[new_name] = self.last_load_time[old_name]
            del self.last_load_time[old_name]
        
        # 파일 시스템에서 업데이트
        database_dir = Path(__file__).parent / "database"
        old_file = database_dir / f"{old_name.lower()}.json"
        new_file = database_dir / f"{new_name.lower()}.json"
        
        if old_file.exists():
            # 기존 파일을 새 이름으로 저장
            with open(old_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(new_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            # 기존 파일 삭제
            old_file.unlink()
        else:
            # 기존 파일이 없으면 새로 생성
            self._save_manufacturer_data(new_name)
        
        return True

    def delete_manufacturer(self, name):
        """제조사 및 관련 데이터 삭제
        
        Args:
            name (str): 제조사 이름
            
        Returns:
            bool: 성공 여부
        """
        if not name or name not in self.manufacturers:
            return False
        
        # 메모리에서 제거
        del self.manufacturers[name]
        
        if name in self.cache:
            del self.cache[name]
        
        if name in self.last_load_time:
            del self.last_load_time[name]
        
        # 파일 삭제
        database_dir = Path(__file__).parent / "database"
        json_file = database_dir / f"{name.lower()}.json"
        
        if json_file.exists():
            json_file.unlink()
        
        return True

    def add_lens_model(self, manufacturer, model_id, specs):
        """새 렌즈 모델 추가"""
        if not manufacturer or not model_id or manufacturer not in self.manufacturers:
            return False
        
        if model_id in self.manufacturers[manufacturer]:
            return False  # 이미 존재하는 모델
        
        # 기본 렌즈 데이터 구조 생성 - 필요한 필드만 유지
        lens_data = {
            "specs": {
                "throw_ratio": {
                    "min": specs.get("throw_min", 0.8),
                    "max": specs.get("throw_max", 1.0),
                    "default": specs.get("throw_min", 0.8)  # default를 min과 동일하게 설정
                },
                "lens_shift": {
                    "h_shift_range": [specs.get("h_shift_min", -30.0), specs.get("h_shift_max", 30.0)],
                    "v_shift_range": [specs.get("v_shift_min", -50.0), specs.get("v_shift_max", 50.0)]
                }
            }
        }
        
        # notes 추가 (있을 경우에만)
        if "notes" in specs and specs["notes"]:
            lens_data["specs"]["notes"] = specs["notes"]
        
        # 모델 데이터 추가
        self.manufacturers[manufacturer][model_id] = lens_data
        
        # 파일에 저장
        self._save_manufacturer_data(manufacturer)
        
        return True
    
    def rename_lens_model(self, manufacturer, old_model_id, new_model_id):
        """렌즈 모델 이름 변경
        
        Args:
            manufacturer (str): 제조사 이름
            old_model_id (str): 현재 모델 식별자
            new_model_id (str): 새 모델 식별자
            
        Returns:
            bool: 성공 여부
        """
        if not manufacturer or not old_model_id or not new_model_id:
            return False
        
        if manufacturer not in self.manufacturers:
            return False  # 제조사가 존재하지 않음
        
        if old_model_id not in self.manufacturers[manufacturer]:
            return False  # 모델이 존재하지 않음
        
        if old_model_id == new_model_id:
            return True  # 이름이 같으면 변경 필요 없음
        
        if new_model_id in self.manufacturers[manufacturer]:
            return False  # 이미 같은 이름의 모델이 존재
        
        # 데이터 복사
        self.manufacturers[manufacturer][new_model_id] = self.manufacturers[manufacturer][old_model_id]
        
        # 기존 모델 데이터 삭제
        del self.manufacturers[manufacturer][old_model_id]
        
        # 파일에 저장
        self._save_manufacturer_data(manufacturer)
        
        return True

    def update_lens_model(self, manufacturer, model_id, specs):
        """렌즈 모델 정보 업데이트
        
        Args:
            manufacturer (str): 제조사 이름
            model_id (str): 모델 식별자
            specs (dict): 업데이트할 사양 데이터
            
        Returns:
            bool: 성공 여부
        """
        if not manufacturer or not model_id or manufacturer not in self.manufacturers:
            return False
        
        if model_id not in self.manufacturers[manufacturer]:
            return False  # 모델이 존재하지 않음
        
        # 기존 데이터 가져오기
        lens_data = self.manufacturers[manufacturer][model_id]
        
        # specs가 없으면 생성
        if "specs" not in lens_data:
            lens_data["specs"] = {}
        
        # throw_ratio 업데이트
        if "throw_min" in specs or "throw_max" in specs:  # throw_default 제거
            throw_min = specs.get("throw_min", 0.8)
            throw_max = specs.get("throw_max", 1.0)
            
            lens_data["specs"]["throw_ratio"] = {
                "min": throw_min,
                "max": throw_max,
                "default": throw_min  # 항상 최소값을 기본값으로 사용
            }
        
        # lens_shift 업데이트
        lens_shift = {}
        if "h_shift_min" in specs or "h_shift_max" in specs:
            h_min = specs.get("h_shift_min", -30.0)
            h_max = specs.get("h_shift_max", 30.0)
            lens_shift["h_shift_range"] = [h_min, h_max]
        
        if "v_shift_min" in specs or "v_shift_max" in specs:
            v_min = specs.get("v_shift_min", -50.0)
            v_max = specs.get("v_shift_max", 50.0)
            lens_shift["v_shift_range"] = [v_min, v_max]
        
        if lens_shift:
            if "lens_shift" not in lens_data["specs"]:
                lens_data["specs"]["lens_shift"] = {}
            
            # 기존 설정 유지하며 업데이트
            if "h_shift_range" in lens_shift:
                lens_data["specs"]["lens_shift"]["h_shift_range"] = lens_shift["h_shift_range"]
            if "v_shift_range" in lens_shift:
                lens_data["specs"]["lens_shift"]["v_shift_range"] = lens_shift["v_shift_range"]
        
        # 메모 업데이트
        if "notes" in specs:
            lens_data["specs"]["notes"] = specs["notes"]
        
        # 파일에 저장
        self._save_manufacturer_data(manufacturer)
        
        return True

    def delete_lens_model(self, manufacturer, model_id):
        """렌즈 모델 삭제
        
        Args:
            manufacturer (str): 제조사 이름
            model_id (str): 모델 식별자
            
        Returns:
            bool: 성공 여부
        """
        if not manufacturer or not model_id or manufacturer not in self.manufacturers:
            return False
        
        if model_id not in self.manufacturers[manufacturer]:
            return False  # 모델이 존재하지 않음
        
        # 모델 삭제
        del self.manufacturers[manufacturer][model_id]
        
        # 파일에 저장
        self._save_manufacturer_data(manufacturer)
        
        return True

    def _save_manufacturer_data(self, manufacturer):
        """제조사 데이터를 JSON 파일로 저장
        
        Args:
            manufacturer (str): 제조사 이름
        """
        if manufacturer not in self.manufacturers:
            return
        
        database_dir = Path(__file__).parent / "database"
        if not database_dir.exists():
            database_dir.mkdir(parents=True, exist_ok=True)
        
        json_file = database_dir / f"{manufacturer.lower()}.json"
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.manufacturers[manufacturer], f, indent=4)
            
            # 캐시 업데이트
            self.cache[manufacturer] = self.manufacturers[manufacturer]
            self.last_load_time[manufacturer] = os.path.getmtime(json_file)
        except Exception as e:
            print(f"Error saving manufacturer data: {e}")

    def import_database(self, filepath):
        """외부 JSON 파일에서 렌즈 데이터 가져오기
        
        Args:
            filepath (str): JSON 파일 경로
            
        Returns:
            tuple: (성공 여부, 메시지)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 데이터 형식 확인
            if not isinstance(data, dict):
                return False, "Invalid data format: Root element must be a dictionary"
            
            # 제조사 이름 결정 (파일 이름에서 추출)
            file_name = Path(filepath).stem
            manufacturer = file_name.capitalize()
            
            # 기존 데이터 백업
            backup = None
            if manufacturer in self.manufacturers:
                backup = self.manufacturers[manufacturer].copy()
            
            # 데이터 추가
            self.manufacturers[manufacturer] = data
            
            # 데이터 검증
            errors = validate_lens_data(data)
            if errors:
                # 오류가 있으면 백업 복원
                if backup:
                    self.manufacturers[manufacturer] = backup
                else:
                    del self.manufacturers[manufacturer]
                
                return False, f"Data validation failed: {', '.join(errors)}"
            
            # 저장
            self._save_manufacturer_data(manufacturer)
            
            return True, f"Successfully imported {len(data)} lens models for {manufacturer}"
        
        except json.JSONDecodeError as e:
            return False, f"JSON parsing error: {str(e)}"
        except Exception as e:
            return False, f"Import failed: {str(e)}"

    def export_database(self, filepath, manufacturer=None):
        """렌즈 데이터를 JSON 파일로 내보내기
        
        Args:
            filepath (str): 저장할 JSON 파일 경로
            manufacturer (str, optional): 특정 제조사만 내보낼 경우 제조사 이름
            
        Returns:
            tuple: (성공 여부, 메시지)
        """
        try:
            if manufacturer:
                # 특정 제조사만 내보내기
                if manufacturer not in self.manufacturers:
                    return False, f"Manufacturer '{manufacturer}' not found"
                
                data = self.manufacturers[manufacturer]
            else:
                # 전체 데이터베이스 내보내기
                data = {}
                for mfr, models in self.manufacturers.items():
                    data[mfr] = models
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            if manufacturer:
                return True, f"Successfully exported data for {manufacturer}"
            else:
                return True, f"Successfully exported data for {len(self.manufacturers)} manufacturers"
        
        except Exception as e:
            return False, f"Export failed: {str(e)}"

# 렌즈 데이터 검증 유틸리티 함수
def validate_lens_data(lens_data):
    """렌즈 데이터의 유효성을 검사하고 필수 필드가 있는지 확인"""
    errors = []
    
    for model, model_data in lens_data.items():
        # 필수 필드 확인
        if 'specs' not in model_data:
            errors.append(f"Model {model}: Missing required field 'specs'")
            continue
        
        specs = model_data['specs']
        
        # throw_ratio 확인
        if 'throw_ratio' not in specs:
            errors.append(f"Model {model}: Missing required field 'throw_ratio'")
        elif isinstance(specs['throw_ratio'], dict):
            throw_ratio = specs['throw_ratio']
            if 'min' not in throw_ratio or 'max' not in throw_ratio or 'default' not in throw_ratio:
                errors.append(f"Model {model}: throw_ratio missing min, max, or default values")
        
        # lens_shift 확인
        if 'lens_shift' not in specs:
            errors.append(f"Model {model}: Missing required field 'lens_shift'")
        else:
            lens_shift = specs['lens_shift']
            if 'h_shift_range' not in lens_shift:
                errors.append(f"Model {model}: lens_shift missing h_shift_range")
            if 'v_shift_range' not in lens_shift:
                errors.append(f"Model {model}: lens_shift missing v_shift_range")
    
    return errors

# 전역 인스턴스 생성
lens_db = LensDatabase()

def percent_to_blender_shift(percent_value):
    """
    퍼센트 단위의 렌즈 시프트 값을 블렌더 카메라 시프트 값으로 변환
    예: 50% -> 0.5, -25% -> -0.25
    """
    return percent_value / 100.0

def blender_shift_to_percent(blender_value):
    """
    블렌더 카메라 시프트 값을 퍼센트 단위로 변환
    예: 0.5 -> 50%, -0.25 -> -25%
    """
    return blender_value * 100.0

def apply_lens_shift_limits(lens_db, manufacturer, model, projector_obj):
    """
    선택된 렌즈의 시프트 제한을 프로젝터 객체에 적용
    """
    if not manufacturer or not model or not projector_obj:
        return False
        
    # 렌즈 프로필 가져오기
    profile = lens_db.get_lens_profile(manufacturer, model)
    if not profile or 'specs' not in profile:
        return False
        
    specs = profile['specs']
    proj_settings = projector_obj.proj_settings
    
    # Throw ratio 제한
    if 'throw_ratio' in specs:
        throw_ratio = specs['throw_ratio']
        if isinstance(throw_ratio, dict) and 'min' in throw_ratio and 'max' in throw_ratio:
            min_throw = throw_ratio['min']
            max_throw = throw_ratio['max']
            
            # 하드 및 소프트 제한 모두 설정
            props = proj_settings.bl_rna.properties['throw_ratio']
            props.hard_min = min_throw
            props.hard_max = max_throw
            props.soft_min = min_throw
            props.soft_max = max_throw
            
            # 현재 값이 범위를 벗어나면 조정
            if proj_settings.throw_ratio < min_throw:
                proj_settings.throw_ratio = min_throw
            elif proj_settings.throw_ratio > max_throw:
                proj_settings.throw_ratio = max_throw
    
    # 수평 시프트 제한
    if 'lens_shift' in specs:
        lens_shift = specs['lens_shift']
        
        if 'h_shift_range' in lens_shift:
            h_min, h_max = lens_shift['h_shift_range']
            props = proj_settings.bl_rna.properties['h_shift']
            props.hard_min = h_min
            props.hard_max = h_max
            props.soft_min = h_min
            props.soft_max = h_max
        
        # 수직 시프트 제한
        if 'v_shift_range' in lens_shift:
            v_min, v_max = lens_shift['v_shift_range']
            props = proj_settings.bl_rna.properties['v_shift']
            props.hard_min = v_min
            props.hard_max = v_max
            props.soft_min = v_min
            props.soft_max = v_max
        
    return True

def focal_length_to_throw_ratio(focal_length, sensor_width=35.0):
    """
    초점 거리를 throw ratio로 변환
    throw_ratio = focal_length / sensor_width
    
    Parameters:
    focal_length (float): 렌즈의 초점 거리 (mm)
    sensor_width (float): 카메라 센서의 너비 (mm), 기본값은 35mm
    
    Returns:
    float: 계산된 throw ratio
    """
    if focal_length <= 0 or sensor_width <= 0:
        return 1.0  # 기본값
    return focal_length / sensor_width

def throw_ratio_to_focal_length(throw_ratio, sensor_width=35.0):
    """
    throw ratio를 초점 거리로 변환
    focal_length = throw_ratio * sensor_width
    
    Parameters:
    throw_ratio (float): 렌즈의 throw ratio
    sensor_width (float): 카메라 센서의 너비 (mm), 기본값은 35mm
    
    Returns:
    float: 계산된 초점 거리 (mm)
    """
    if throw_ratio <= 0:
        return 35.0  # 기본값
    return throw_ratio * sensor_width

def apply_optical_properties(profile, projector_obj):
    """
    렌즈 프로필의 광학 특성을 프로젝터 객체에 적용
    현재는 정보 표시만 하고 실제 시뮬레이션에는 미적용
    
    Parameters:
    profile (dict): 렌즈 프로필 데이터
    projector_obj (Object): 프로젝터 객체
    
    Returns:
    bool: 적용 성공 여부
    """
    if not profile or not projector_obj:
        return False
        
    if 'optical_properties' in profile:
        opt_props = profile['optical_properties']
        
        # 현재는 정보만 저장하고 실제 시뮬레이션에는 미적용
        # 향후 노드 기반 왜곡 시뮬레이션 등을 위한 준비
        projector_obj['lens_distortion'] = opt_props.get('distortion', 0.0)
        projector_obj['lens_chromatic_aberration'] = opt_props.get('chromatic_aberration', 0.0)
        projector_obj['lens_vignetting'] = opt_props.get('vignetting', 0.0)
        
    return True