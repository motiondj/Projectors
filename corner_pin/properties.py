# corner_pin/properties.py 업데이트

import bpy
from bpy.props import FloatVectorProperty, BoolProperty, PointerProperty, StringProperty, EnumProperty

def update_corner_pin(self, context):
    """코너 핀 설정 변경 시 노드 업데이트"""
    print(f"update_corner_pin called: {self}")
    
    # 무한 재귀 방지 플래그
    if getattr(update_corner_pin, '_is_updating', False):
        return
    
    update_corner_pin._is_updating = True
    
    try:
        obj = context.active_object
        if not obj or not hasattr(obj, 'corner_pin'):
            print("No active object with corner_pin attribute")
            return
        
        print(f"Updating corner pin nodes for {obj.name}")
        
        # 현재 투사 모드 확인
        if obj.proj_settings.projected_texture == 'custom_texture':
            # 스팟 라이트 찾기
            spot = None
            for child in obj.children:
                if child.type == 'LIGHT' and child.data.type == 'SPOT':
                    spot = child
                    break
            
            if not spot or not spot.data.node_tree:
                print("No spotlight or node tree found")
                return
            
            node_tree = spot.data.node_tree
            
            # 주요 노드 찾기
            group_node = None  # "!! Don't touch !!" 노드
            image_texture_node = None
            corner_pin_node = None
            
            for node in node_tree.nodes:
                if node.name == 'Group':
                    group_node = node
                elif node.bl_idname == 'ShaderNodeTexImage':
                    image_texture_node = node
                elif node.name == 'Corner Pin':
                    corner_pin_node = node
            
            if not group_node or not image_texture_node:
                print("Required nodes not found")
                return
            
            # 소켓 찾기
            texture_vector_output = None
            for output in group_node.outputs:
                if output.name == 'texture vector':
                    texture_vector_output = output
                    break
            
            if not texture_vector_output:
                print("texture vector output not found")
                return
            
            # Vector 입력 찾기
            vector_input = None
            for input in image_texture_node.inputs:
                if input.name == 'Vector':
                    vector_input = input
                    break
            
            if not vector_input and len(image_texture_node.inputs) > 0:
                vector_input = image_texture_node.inputs[0]
            
            if not vector_input:
                print("Vector input not found")
                return
            
            # 코너 핀 활성화 시
            if self.enabled:
                # 코너 핀 노드가 없으면 생성
                if not corner_pin_node:
                    from . import nodes
                    # 노드 그룹 생성 확인
                    if 'CornerPinCorrection' not in bpy.data.node_groups:
                        nodes.create_corner_pin_node_group()
                    
                    # 코너 핀 노드 생성
                    corner_pin_node = node_tree.nodes.new('ShaderNodeGroup')
                    corner_pin_node.name = 'Corner Pin'
                    corner_pin_node.node_tree = bpy.data.node_groups['CornerPinCorrection']
                    
                    # 노드 위치 설정
                    corner_pin_node.location = (
                        (group_node.location[0] + image_texture_node.location[0]) / 2,
                        group_node.location[1] - 150
                    )
                
                # 기존 연결 찾기 - Group -> Image Texture 직접 연결만 제거
                for link in list(node_tree.links):
                    if (link.from_node == group_node and 
                        link.from_socket == texture_vector_output and 
                        link.to_node == image_texture_node):
                        node_tree.links.remove(link)
                        print("  - Removed direct link: Group -> Image Texture")
                
                # 새 연결 생성 - 기존 연결 확인 후 필요한 경우에만 생성
                # 1. Group -> Corner Pin 연결
                has_group_to_corner_pin = False
                for link in node_tree.links:
                    if (link.from_node == group_node and 
                        link.from_socket == texture_vector_output and 
                        link.to_node == corner_pin_node):
                        has_group_to_corner_pin = True
                        break
                
                if not has_group_to_corner_pin:
                    link1 = node_tree.links.new(texture_vector_output, corner_pin_node.inputs[0])
                    print(f"  - Created link: Group -> Corner Pin: {link1 is not None}")
                
                # 2. Corner Pin -> Image Texture 연결
                has_corner_pin_to_image = False
                for link in node_tree.links:
                    if (link.from_node == corner_pin_node and 
                        link.to_node == image_texture_node):
                        has_corner_pin_to_image = True
                        break
                
                if not has_corner_pin_to_image:
                    link2 = node_tree.links.new(corner_pin_node.outputs[0], vector_input)
                    print(f"  - Created link: Corner Pin -> Image Texture: {link2 is not None}")
                
                # 코너 값 설정
                try:
                    corner_pin_node.inputs[1].default_value = (self.top_left[0], self.top_left[1], 0.0)
                    corner_pin_node.inputs[2].default_value = (self.top_right[0], self.top_right[1], 0.0)
                    corner_pin_node.inputs[3].default_value = (self.bottom_left[0], self.bottom_left[1], 0.0)
                    corner_pin_node.inputs[4].default_value = (self.bottom_right[0], self.bottom_right[1], 0.0)
                    print("  - Corner values set successfully")
                except Exception as e:
                    print(f"  - Error setting corner values: {e}")
            
            else:  # 코너 핀 비활성화 시
                # 코너 핀 노드가 있는 경우
                if corner_pin_node:
                    # 기존 연결 찾기
                    group_to_corner_pin = None
                    corner_pin_to_image = None
                    
                    for link in list(node_tree.links):
                        if (link.from_node == group_node and 
                            link.from_socket == texture_vector_output and 
                            link.to_node == corner_pin_node):
                            group_to_corner_pin = link
                        
                        if (link.from_node == corner_pin_node and 
                            link.to_node == image_texture_node):
                            corner_pin_to_image = link
                    
                    # 연결 제거
                    if group_to_corner_pin:
                        node_tree.links.remove(group_to_corner_pin)
                        print("  - Removed link: Group -> Corner Pin")
                    
                    if corner_pin_to_image:
                        node_tree.links.remove(corner_pin_to_image)
                        print("  - Removed link: Corner Pin -> Image Texture")
                
                # 직접 연결 확인
                has_direct_link = False
                for link in node_tree.links:
                    if (link.from_node == group_node and 
                        link.from_socket == texture_vector_output and 
                        link.to_node == image_texture_node):
                        has_direct_link = True
                        break
                
                # 직접 연결 생성 (없는 경우)
                if not has_direct_link:
                    link = node_tree.links.new(texture_vector_output, vector_input)
                    print(f"  - Created direct link: Group -> Image Texture: {link is not None}")
        
        # custom_texture가 아닌 경우 코너 핀은 작동하지 않음
        elif self.enabled:
            # 다른 텍스처 모드에서는 코너 핀 비활성화 (무한 재귀 방지를 위해 직접 값 설정)
            self["enabled"] = False
            print("Corner pin is not available for non-custom textures")
            
            # 필요한 경우 노드 트리 정리
            spot = None
            for child in obj.children:
                if child.type == 'LIGHT' and child.data.type == 'SPOT':
                    spot = child
                    break
            
            if spot and spot.data.node_tree:
                node_tree = spot.data.node_tree
                corner_pin_node = node_tree.nodes.get('Corner Pin')
                
                if corner_pin_node:
                    # 코너 핀 노드와 관련된 모든 연결 찾아서 제거
                    links_to_remove = []
                    for link in node_tree.links:
                        if link.from_node == corner_pin_node or link.to_node == corner_pin_node:
                            links_to_remove.append(link)
                    
                    for link in links_to_remove:
                        node_tree.links.remove(link)
                        print(f"  - Removed link: {link.from_node.name} -> {link.to_node.name}")
                    
                    # 필요한 경우 직접 연결 생성
                    from . import nodes
                    nodes.bypass_corner_pin_node(node_tree, corner_pin_node)
        
        # 노드 값 업데이트
        if obj.proj_settings.projected_texture == 'custom_texture' and self.enabled:
            print("Updating corner pin node values")
            from . import nodes
            nodes.update_corner_pin_nodes(obj)
    
    finally:
        # 플래그 해제
        update_corner_pin._is_updating = False

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