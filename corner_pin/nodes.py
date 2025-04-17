# corner_pin/nodes.py 개선 버전

import bpy
import math

def create_corner_pin_node_group():
    """4코너 보정 노드 그룹 생성"""
    name = 'CornerPinCorrection'
    
    # 이미 존재하면 삭제
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])
    
    # 새 노드 그룹 생성
    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    
    # 입력/출력 소켓 생성 (블렌더 4.3 방식)
    if hasattr(node_group, 'interface'):
        # 블렌더 4.0 이상
        node_group.interface.new_socket(name='UV', in_out='INPUT', socket_type='NodeSocketVector')
        node_group.interface.new_socket(name='Top Left', in_out='INPUT', socket_type='NodeSocketVector')
        node_group.interface.new_socket(name='Top Right', in_out='INPUT', socket_type='NodeSocketVector')
        node_group.interface.new_socket(name='Bottom Left', in_out='INPUT', socket_type='NodeSocketVector')
        node_group.interface.new_socket(name='Bottom Right', in_out='INPUT', socket_type='NodeSocketVector')
        
        node_group.interface.new_socket(name='UV', in_out='OUTPUT', socket_type='NodeSocketVector')
    else:
        # 이전 블렌더 버전
        inputs = node_group.inputs
        inputs.new('NodeSocketVector', 'UV')
        inputs.new('NodeSocketVector', 'Top Left')
        inputs.new('NodeSocketVector', 'Top Right')
        inputs.new('NodeSocketVector', 'Bottom Left')
        inputs.new('NodeSocketVector', 'Bottom Right')
        
        outputs = node_group.outputs
        outputs.new('NodeSocketVector', 'UV')
    
    # 노드 생성
    nodes = node_group.nodes
    
    # 입력/출력 노드
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)
    
    # 간단한 통과 로직 (테스트용)
    # 실제 구현에서는 4코너 변환 로직 추가 필요
    node_group.links.new(input_node.outputs[0], output_node.inputs[0])
    
    return node_group

def find_texture_vector_nodes(spot_node_tree):
    """텍스처 벡터 출력을 가진 노드와 연결된 노드들 찾기"""
    group_node = None
    texture_vector_output = None
    connected_nodes = []
    
    # Group 노드 찾기
    for node in spot_node_tree.nodes:
        if node.name == 'Group':
            group_node = node
            break
    
    if not group_node:
        print("Cannot find Group node in projector node tree")
        return None, None, []
    
    # texture vector 출력 찾기
    for output in group_node.outputs:
        if output.name == 'texture vector':
            texture_vector_output = output
            break
    
    if not texture_vector_output:
        print("Cannot find 'texture vector' output in Group node")
        return group_node, None, []
    
    # 연결된 노드 찾기
    for link in spot_node_tree.links:
        if link.from_node == group_node and link.from_socket == texture_vector_output:
            connected_nodes.append((link.to_node, link.to_socket))
    
    return group_node, texture_vector_output, connected_nodes

def integrate_corner_pin_with_projector_node_tree(projector_obj):
    """프로젝터 노드 트리에 코너 핀 노드 통합 - 디버깅 포함"""
    if not projector_obj or projector_obj.type != 'CAMERA':
        print("Not a camera object")
        return False
    
    # 스팟 라이트 찾기
    spot = None
    for child in projector_obj.children:
        if child.type == 'LIGHT' and child.data.type == 'SPOT':
            spot = child
            break
    
    if not spot:
        print("Spotlight child not found")
        return False
    
    if not spot.data.node_tree:
        print("No node tree in spotlight")
        return False
    
    node_tree = spot.data.node_tree
    
    # 디버깅: 모든 노드 출력
    print("Nodes in node tree:", [node.name for node in node_tree.nodes])
    
    # 코너 핀 노드 생성
    corner_pin_node = node_tree.nodes.new('ShaderNodeGroup')
    corner_pin_node.name = 'Corner Pin'
    
    # 노드 그룹 생성 또는 가져오기
    node_group_name = 'CornerPinCorrection'
    if node_group_name not in bpy.data.node_groups:
        create_corner_pin_node_group()
    
    corner_pin_node.node_tree = bpy.data.node_groups[node_group_name]
    
    # Image Texture 노드 찾기
    image_texture_node = None
    for node in node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            image_texture_node = node
            break
    
    if not image_texture_node:
        print("Image Texture node not found")
        # Group 노드의 출력을 찾아보기
        group_node = None
        texture_vector_output = None
        for node in node_tree.nodes:
            if node.name == 'Group':
                group_node = node
                # 출력 확인
                for output in node.outputs:
                    print(f"Group output: {output.name}")
                    if output.name == 'texture vector':
                        texture_vector_output = output
                break
        
        if group_node and texture_vector_output:
            # 연결된 노드 찾기
            connected_nodes = []
            for link in node_tree.links:
                if link.from_node == group_node and link.from_socket == texture_vector_output:
                    connected_nodes.append((link.to_node, link.to_socket))
                    print(f"Connected to: {link.to_node.name}, socket: {link.to_socket.name}")
            
            if connected_nodes:
                # 첫 번째 연결된 노드 사용
                to_node, to_socket = connected_nodes[0]
                
                # 연결 삭제
                for link in list(node_tree.links):
                    if link.from_node == group_node and link.from_socket == texture_vector_output and link.to_node == to_node:
                        node_tree.links.remove(link)
                
                # 코너 핀 노드 위치 설정
                corner_pin_node.location = (
                    (group_node.location[0] + to_node.location[0]) / 2,
                    (group_node.location[1] + to_node.location[1]) / 2 - 200
                )
                
                # 새 연결 생성
                node_tree.links.new(texture_vector_output, corner_pin_node.inputs[0])
                node_tree.links.new(corner_pin_node.outputs[0], to_socket)
                print("Successfully connected corner pin node")
                return True
            else:
                print("No connections found for texture vector output")
    else:
        # Image Texture 노드를 사용하는 경우
        print("Found Image Texture node, connecting...")
        # 나머지 구현...
    
    return False

def apply_corner_pin_to_projector(projector_obj):
    """프로젝터 객체에 4코너 보정 노드 적용"""
    if not projector_obj or projector_obj.type != 'CAMERA':
        return False
    
    if not hasattr(projector_obj, 'corner_pin'):
        return False
    
    # 코너 핀 노드 그룹 통합
    return integrate_corner_pin_with_projector_node_tree(projector_obj)

def update_corner_pin_nodes(projector_obj):
    """코너 핀 노드의 입력값 업데이트"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        return False
    
    corner_pin = projector_obj.corner_pin
    
    # 스팟 라이트 찾기
    spot = None
    for child in projector_obj.children:
        if child.type == 'LIGHT' and child.data.type == 'SPOT':
            spot = child
            break
    
    if not spot or not spot.data.node_tree:
        return False
    
    node_tree = spot.data.node_tree
    corner_pin_node = node_tree.nodes.get('Corner Pin')
    
    if not corner_pin_node:
        if corner_pin.enabled:
            # 노드가 없고 기능이 활성화되어 있으면 새로 적용
            return apply_corner_pin_to_projector(projector_obj)
        else:
            return False
    
    # 입력 소켓 업데이트 (블렌더 버전 호환성 고려)
    try:
        # 인덱스로 접근 (이름 대신)
        corner_pin_node.inputs[1].default_value = (*corner_pin.top_left, 0.0)
        corner_pin_node.inputs[2].default_value = (*corner_pin.top_right, 0.0)
        corner_pin_node.inputs[3].default_value = (*corner_pin.bottom_left, 0.0)
        corner_pin_node.inputs[4].default_value = (*corner_pin.bottom_right, 0.0)
    except Exception as e:
        print(f"Error updating corner pin inputs: {e}")
        # 소켓 이름으로도 시도
        try:
            for i, socket in enumerate(corner_pin_node.inputs):
                if i == 0:  # UV 입력은 건너뜀
                    continue
                if 'top left' in socket.name.lower():
                    socket.default_value = (*corner_pin.top_left, 0.0)
                elif 'top right' in socket.name.lower():
                    socket.default_value = (*corner_pin.top_right, 0.0)
                elif 'bottom left' in socket.name.lower():
                    socket.default_value = (*corner_pin.bottom_left, 0.0)
                elif 'bottom right' in socket.name.lower():
                    socket.default_value = (*corner_pin.bottom_right, 0.0)
        except Exception as e2:
            print(f"Second attempt failed: {e2}")
            return False
    
    return True

def register():
    # 노드 그룹 생성 코드 제거
    # create_corner_pin_node_group() - 이 줄 제거
    print("Corner Pin nodes registered")

def unregister():
    # 노드 그룹 삭제 확인 코드 추가
    try:
        if 'CornerPinCorrection' in bpy.data.node_groups:
            bpy.data.node_groups.remove(bpy.data.node_groups['CornerPinCorrection'])
    except:
        pass
    print("Corner Pin nodes unregistered")