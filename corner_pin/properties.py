# corner_pin/properties.py 업데이트

import bpy
from bpy.props import FloatVectorProperty, BoolProperty, PointerProperty, StringProperty, EnumProperty

def update_corner_pin(self, context):
    """코너 핀 설정 변경 시 노드 업데이트"""
    print(f"update_corner_pin called: {self}")
    obj = context.active_object
    if not obj or not hasattr(obj, 'corner_pin'):
        print("No active object with corner_pin attribute")
        return
    
    print(f"Updating corner pin nodes for {obj.name}")
    
    # 현재 투사 모드 확인
    if obj.proj_settings.projected_texture == 'custom_texture':
        if self.enabled:
            # 코너 핀 활성화 시 노드 연결 설정
            from . import nodes
            nodes.apply_corner_pin_to_projector(obj)
        else:
            # 코너 핀 비활성화 시 노드 우회
            # 스팟 라이트 찾기
            spot = None
            for child in obj.children:
                if child.type == 'LIGHT' and child.data.type == 'SPOT':
                    spot = child
                    break
            
            if spot and spot.data.node_tree:
                node_tree = spot.data.node_tree
                corner_pin_node = node_tree.nodes.get('Corner Pin')
                
                if corner_pin_node:
                    # 코너 핀 노드 우회 함수 호출
                    from . import nodes
                    nodes.bypass_corner_pin_node(node_tree, corner_pin_node)
    
    # custom_texture가 아닌 경우 코너 핀은 작동하지 않음
    elif self.enabled:
        # 다른 텍스처 모드에서는 코너 핀 비활성화
        self.enabled = False
        print("Corner pin is not available for non-custom textures")

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
    print("corner_pin.properties.register() called")
    try:
        # 이미 등록된 경우 먼저 등록 해제
        if hasattr(bpy.types, 'CornerPinProperties'):
            print("CornerPinProperties already registered, unregistering first")
            try:
                bpy.utils.unregister_class(CornerPinProperties)
                print("Successfully unregistered CornerPinProperties")
            except Exception as e:
                print(f"Failed to unregister CornerPinProperties: {e}")
        
        # 등록
        bpy.utils.register_class(CornerPinProperties)
        print("Successfully registered CornerPinProperties")
        
        # 프로퍼티 등록
        if not hasattr(bpy.types.Object, 'corner_pin'):
            print("Registering corner_pin property on Object")
            bpy.types.Object.corner_pin = PointerProperty(type=CornerPinProperties)
            print("Successfully registered corner_pin property")
        else:
            print("corner_pin property already registered on Object")
    except Exception as e:
        print(f"Error registering Corner Pin properties: {e}")

def unregister():
    print("corner_pin.properties.unregister() called")
    try:
        if hasattr(bpy.types.Object, 'corner_pin'):
            print("Unregistering corner_pin property")
            del bpy.types.Object.corner_pin
            print("Successfully unregistered corner_pin property")
        else:
            print("corner_pin property not found on Object")
        
        if hasattr(bpy.types, 'CornerPinProperties'):
            print("Unregistering CornerPinProperties")
            bpy.utils.unregister_class(CornerPinProperties)
            print("Successfully unregistered CornerPinProperties")
        else:
            print("CornerPinProperties not registered")
    except Exception as e:
        print(f"Error unregistering Corner Pin properties: {e}")