# corner_pin/properties.py 업데이트

import bpy
from bpy.props import FloatVectorProperty, BoolProperty, PointerProperty, StringProperty, EnumProperty

def update_corner_pin(self, context):
    """코너 핀 설정 변경 시 노드 업데이트"""
    obj = context.active_object
    if not obj or not hasattr(obj, 'corner_pin'):
        return
    
    from . import nodes
    nodes.update_corner_pin_nodes(obj)

class CornerPinProperties(bpy.types.PropertyGroup):
    """4코너 보정 기능에 필요한 속성들"""
    
    # 4코너 보정 활성화 여부
    enabled: BoolProperty(
        name="Enable Corner Pin",
        description="Enable 4-corner pin correction",
        default=False,
        update=update_corner_pin
    )
    
    # 각 코너의 위치 (정규화된 좌표, 0~1 범위)
    top_left: FloatVectorProperty(
        name="Top Left",
        description="Top left corner position",
        default=(0.0, 1.0),
        size=2,
        subtype='XYZ',
        update=update_corner_pin
    )
    
    top_right: FloatVectorProperty(
        name="Top Right",
        description="Top right corner position",
        default=(1.0, 1.0),
        size=2,
        subtype='XYZ',
        update=update_corner_pin
    )
    
    bottom_left: FloatVectorProperty(
        name="Bottom Left",
        description="Bottom left corner position",
        default=(0.0, 0.0),
        size=2,
        subtype='XYZ',
        update=update_corner_pin
    )
    
    bottom_right: FloatVectorProperty(
        name="Bottom Right",
        description="Bottom right corner position",
        default=(1.0, 0.0),
        size=2,
        subtype='XYZ',
        update=update_corner_pin
    )
    
    # 프리셋 관련 속성
    preset_name: StringProperty(
        name="Preset Name",
        description="Name for saving current corner pin settings as a preset",
        default=""
    )
    
    current_preset: EnumProperty(
        name="Preset",
        description="Select a saved corner pin preset",
        items=lambda self, context: []  # 동적으로 채워질 예정
    )

def register():
    bpy.utils.register_class(CornerPinProperties)
    # 프로젝터 객체에 corner_pin 속성 추가
    bpy.types.Object.corner_pin = PointerProperty(type=CornerPinProperties)
    print("Corner Pin properties registered")

def unregister():
    del bpy.types.Object.corner_pin
    bpy.utils.unregister_class(CornerPinProperties)