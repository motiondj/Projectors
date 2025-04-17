# corner_pin/visual_tools.py - 시각적 코너 조정 도구

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.types import Operator
from bpy.props import EnumProperty, BoolProperty
from mathutils import Vector

def draw_callback_px(self, context):
    """3D 뷰포트에 코너 핸들과 가이드라인 그리기"""
    if not context.active_object or not hasattr(context.active_object, 'corner_pin'):
        return
    
    # 현재 프로젝터 객체와 코너 핀 설정 가져오기
    obj = context.active_object
    corner_pin = obj.corner_pin
    
    # 코너 핀이 비활성화되었다면 표시하지 않음
    if not corner_pin.enabled:
        return
    
    # 카메라 투영 면 중심과 크기 계산
    cam_loc = obj.matrix_world.translation
    cam_dir = obj.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    cam_up = obj.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    cam_right = obj.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    
    # 투영 거리 (임의로 설정)
    projection_distance = 5.0
    
    # 투영 면 중심
    center = cam_loc + cam_dir * projection_distance
    
    # 투영 면 크기 (렌즈 FOV에 따라 조정 필요)
    width = 2.0
    height = width / obj.data.sensor_width * obj.data.sensor_height
    
    # 코너 위치 계산
    corners = {
        'top_left': center + cam_up * height/2 - cam_right * width/2,
        'top_right': center + cam_up * height/2 + cam_right * width/2,
        'bottom_left': center - cam_up * height/2 - cam_right * width/2,
        'bottom_right': center - cam_up * height/2 + cam_right * width/2
    }
    
    # 코너 핀 설정에 따라 코너 위치 조정
    corners_adjusted = {
        'top_left': corners['bottom_left'] + (corners['top_left'] - corners['bottom_left']) * corner_pin.top_left[1] + 
                    (corners['bottom_right'] - corners['bottom_left']) * corner_pin.top_left[0],
        'top_right': corners['bottom_left'] + (corners['top_left'] - corners['bottom_left']) * corner_pin.top_right[1] + 
                     (corners['bottom_right'] - corners['bottom_left']) * corner_pin.top_right[0],
        'bottom_left': corners['bottom_left'] + (corners['top_left'] - corners['bottom_left']) * corner_pin.bottom_left[1] + 
                       (corners['bottom_right'] - corners['bottom_left']) * corner_pin.bottom_left[0],
        'bottom_right': corners['bottom_left'] + (corners['top_left'] - corners['bottom_left']) * corner_pin.bottom_right[1] + 
                        (corners['bottom_right'] - corners['bottom_left']) * corner_pin.bottom_right[0]
    }
    
    # GPU 쉐이더 설정
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    
    # 가이드라인 그리기
    gpu.state.line_width_set(1.0)
    shader.bind()
    
    # 외곽선 (핀 조정된 영역)
    vertices = [
        corners_adjusted['top_left'],
        corners_adjusted['top_right'],
        corners_adjusted['bottom_right'],
        corners_adjusted['bottom_left']
    ]
    
    indices = [(0, 1), (1, 2), (2, 3), (3, 0)]
    
    shader.uniform_float("color", (0.2, 0.8, 0.2, 1.0))  # 녹색
    batch = batch_for_shader(shader, 'LINES', {"pos": vertices}, indices=indices)
    batch.draw(shader)
    
    # 코너 핸들 그리기
    gpu.state.point_size_set(10.0)
    shader.uniform_float("color", (0.2, 0.6, 1.0, 1.0))  # 파란색
    
    # 현재 선택된 코너는 다른 색상으로 표시
    if self.selected_corner:
        for corner_name, corner_pos in corners_adjusted.items():
            if corner_name == self.selected_corner:
                shader.uniform_float("color", (1.0, 0.6, 0.2, 1.0))  # 주황색 (선택됨)
            else:
                shader.uniform_float("color", (0.2, 0.6, 1.0, 1.0))  # 파란색 (선택 안됨)
            
            batch = batch_for_shader(shader, 'POINTS', {"pos": [corner_pos]})
            batch.draw(shader)
    else:
        vertices = [pos for pos in corners_adjusted.values()]
        batch = batch_for_shader(shader, 'POINTS', {"pos": vertices})
        batch.draw(shader)
    
    # 이름 라벨 표시 (BLF 모듈 사용)
    font_id = 0  # 기본 폰트
    blf.size(font_id, 16, 72)
    
    for corner_name, corner_pos in corners_adjusted.items():
        # 3D 좌표를 2D 화면 좌표로 변환
        region = context.region
        region_3d = context.space_data.region_3d
        pos_2d = bpy_extras.view3d_utils.location_3d_to_region_2d(region, region_3d, corner_pos)
        
        if pos_2d:
            blf.position(font_id, pos_2d[0] + 10, pos_2d[1] + 10, 0)
            blf.draw(font_id, corner_name.replace('_', ' ').title())

class CORNER_PIN_OT_interactive_edit(Operator):
    """대화형 코너 핀 편집 모드"""
    bl_idname = "corner_pin.interactive_edit"
    bl_label = "Edit Corners Visually"
    bl_options = {'REGISTER', 'UNDO'}
    
    selected_corner: EnumProperty(
        name="Selected Corner",
        items=[
            ('', "None", ""),
            ('top_left', "Top Left", ""),
            ('top_right', "Top Right", ""),
            ('bottom_left', "Bottom Left", ""),
            ('bottom_right', "Bottom Right", "")
        ],
        default=''
    )
    
    show_guides: BoolProperty(
        name="Show Guides",
        description="Show guide lines between corners",
        default=True
    )
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'ESC'}:
            # 모달 모드 종료
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # 마우스 클릭 위치에서 가장 가까운 코너 선택
            self.selected_corner = self.find_closest_corner(context, event)
            return {'RUNNING_MODAL'}
        
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            # 마우스 드래그 종료
            self.selected_corner = ''
            return {'RUNNING_MODAL'}
        
        if event.type == 'MOUSEMOVE' and self.selected_corner:
            # 선택된 코너를 마우스 위치로 이동
            self.move_corner(context, event)
            return {'RUNNING_MODAL'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        if context.area.type != 'VIEW_3D':
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
        
        # 현재 객체가 프로젝터이고 코너 핀이 활성화되어 있는지 확인
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin') or not obj.corner_pin.enabled:
            self.report({'WARNING'}, "No active projector with enabled corner pin")
            return {'CANCELLED'}
        
        # 그리기 핸들러 등록
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_VIEW')
        
        # 모달 모드 시작
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def find_closest_corner(self, context, event):
        """마우스 위치에서 가장 가까운 코너 찾기"""
        # (이 함수에 위치 비교 로직 구현)
        return 'top_left'  # 임시 예제
    
    def move_corner(self, context, event):
        """선택된 코너를 마우스 위치로 이동"""
        # (이 함수에 코너 위치 계산 및 업데이트 로직 구현)
        pass

def register():
    bpy.utils.register_class(CORNER_PIN_OT_interactive_edit)

def unregister():
    bpy.utils.unregister_class(CORNER_PIN_OT_interactive_edit)