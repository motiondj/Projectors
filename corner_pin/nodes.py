# corner_pin/nodes.py 개선 버전

import bpy
import math

def create_corner_pin_node_group():
    """4코너 보정 노드 그룹 생성 - 향상된 버전"""
    name = 'CornerPinCorrection'
    
    # 이미 존재하면 삭제
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])
    
    # 새 노드 그룹 생성
    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    
    # 입력 소켓: 텍스처 좌표 + 4개 코너 좌표
    inputs = node_group.inputs
    inputs.new('NodeSocketVector', 'UV')
    inputs.new('NodeSocketVector', 'Top Left')
    inputs.new('NodeSocketVector', 'Top Right')
    inputs.new('NodeSocketVector', 'Bottom Left')
    inputs.new('NodeSocketVector', 'Bottom Right')
    
    # 출력 소켓: 변환된 텍스처 좌표
    outputs = node_group.outputs
    outputs.new('NodeSocketVector', 'UV')
    
    # 노드 생성
    nodes = node_group.nodes
    
    # 입력/출력 노드
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)
    
    # 기본 위치 상수값 (0,0,0), (1,0,0), (0,1,0), (1,1,0)
    zero_zero = nodes.new('ShaderNodeCombineXYZ')
    zero_zero.location = (-600, -300)
    zero_zero.inputs[0].default_value = 0.0
    zero_zero.inputs[1].default_value = 0.0
    zero_zero.inputs[2].default_value = 0.0
    
    one_zero = nodes.new('ShaderNodeCombineXYZ')
    one_zero.location = (-600, -400)
    one_zero.inputs[0].default_value = 1.0
    one_zero.inputs[1].default_value = 0.0
    one_zero.inputs[2].default_value = 0.0
    
    zero_one = nodes.new('ShaderNodeCombineXYZ')
    zero_one.location = (-600, -500)
    zero_one.inputs[0].default_value = 0.0
    zero_one.inputs[1].default_value = 1.0
    zero_one.inputs[2].default_value = 0.0
    
    one_one = nodes.new('ShaderNodeCombineXYZ')
    one_one.location = (-600, -600)
    one_one.inputs[0].default_value = 1.0
    one_one.inputs[1].default_value = 1.0
    one_one.inputs[2].default_value = 0.0
    
    # 거리 계산을 위한 수학 노드들
    # 입력 UV 좌표 분리
    separate_uv = nodes.new('ShaderNodeSeparateXYZ')
    separate_uv.location = (-600, 0)
    
    # 링크 생성
    links = node_group.links
    links.new(input_node.outputs['UV'], separate_uv.inputs[0])
    
    # U, V 좌표 분리
    s = separate_uv.outputs[0]  # X 좌표
    t = separate_uv.outputs[1]  # Y 좌표
    
    # 코드 간소화를 위한 함수
    def add_math_node(operation, x, y, input1=None, input2=None):
        node = nodes.new('ShaderNodeMath')
        node.operation = operation
        node.location = (x, y)
        if input1 is not None:
            links.new(input1, node.inputs[0])
        if input2 is not None:
            links.new(input2, node.inputs[1])
        return node
    
    def add_mix_node(x, y, factor=None, input1=None, input2=None, blend_type='MIX'):
        node = nodes.new('ShaderNodeMixRGB')
        node.blend_type = blend_type
        node.location = (x, y)
        if factor is not None:
            links.new(factor, node.inputs[0])
        if input1 is not None:
            links.new(input1, node.inputs[1])
        if input2 is not None:
            links.new(input2, node.inputs[2])
        return node
    
    # 더 간단한 접근 방식: bilinear interpolation
    # S 방향 보간 (위쪽)
    mix_top = add_mix_node(-400, 200, s, 
                           input_node.outputs['Top Left'], 
                           input_node.outputs['Top Right'])
    
    # S 방향 보간 (아래쪽)
    mix_bottom = add_mix_node(-400, 0, s, 
                              input_node.outputs['Bottom Left'], 
                              input_node.outputs['Bottom Right'])
    
    # T 방향 보간 (최종)
    mix_final = add_mix_node(-100, 100, t, mix_bottom.outputs[0], mix_top.outputs[0])
    
    # UV 좌표 분리
    separate_result = nodes.new('ShaderNodeSeparateXYZ')
    separate_result.location = (100, 100)
    links.new(mix_final.outputs[0], separate_result.inputs[0])
    
    # 최종 결과 조합
    combine_result = nodes.new('ShaderNodeCombineXYZ')
    combine_result.location = (300, 100)
    combine_result.inputs[2].default_value = 0.0  # Z 값은 항상 0
    
    links.new(separate_result.outputs[0], combine_result.inputs[0])  # X
    links.new(separate_result.outputs[1], combine_result.inputs[1])  # Y
    
    # 출력 연결
    links.new(combine_result.outputs[0], output_node.inputs[0])
    
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
    """프로젝터 노드 트리에 코너 핀 노드 통합"""
    if not projector_obj or projector_obj.type != 'CAMERA':
        return False
    
    # 스팟 라이트 (프로젝터의 자식 객체) 찾기
    spot = None
    for child in projector_obj.children:
        if child.type == 'LIGHT' and child.data.type == 'SPOT':
            spot = child
            break
    
    if not spot or not spot.data.node_tree:
        print("Cannot find spotlight child or its node tree")
        return False
    
    node_tree = spot.data.node_tree
    
    # 코너 핀 노드가 이미 존재하는지 확인
    existing_corner_pin = node_tree.nodes.get('Corner Pin')
    if existing_corner_pin:
        print("Corner pin node already exists")
        return True
    
    # Group 노드, texture vector 출력, 연결된 노드 찾기
    group_node, texture_vector_output, connected_nodes = find_texture_vector_nodes(node_tree)
    
    if not group_node or not texture_vector_output or not connected_nodes:
        print("Cannot find necessary nodes or connections")
        return False
    
    # 코너 핀 노드 그룹 생성 또는 가져오기
    node_group_name = 'CornerPinCorrection'
    if node_group_name not in bpy.data.node_groups:
        try:
            create_corner_pin_node_group()
        except Exception as e:
            print(f"Error creating corner pin node group: {e}")
            return False
    
    # 코너 핀 노드 생성
    corner_pin_node = node_tree.nodes.new('ShaderNodeGroup')
    corner_pin_node.name = 'Corner Pin'
    corner_pin_node.node_tree = bpy.data.node_groups[node_group_name]
    
    # 위치 설정
    corner_pin_node.location = (group_node.location[0] + 200, group_node.location[1] - 200)
    
    # 코너 위치 기본값 설정
    corner_pin_node.inputs['Top Left'].default_value = (0.0, 1.0, 0.0)
    corner_pin_node.inputs['Top Right'].default_value = (1.0, 1.0, 0.0)
    corner_pin_node.inputs['Bottom Left'].default_value = (0.0, 0.0, 0.0)
    corner_pin_node.inputs['Bottom Right'].default_value = (1.0, 0.0, 0.0)
    
    # 기존 연결 제거 및 코너 핀 노드 연결
    for to_node, to_socket in connected_nodes:
        # 모든 기존 링크 찾기
        links_to_remove = []
        for link in node_tree.links:
            if link.from_node == group_node and link.from_socket == texture_vector_output and link.to_node == to_node and link.to_socket == to_socket:
                links_to_remove.append(link)
        
        # 링크 제거
        for link in links_to_remove:
            node_tree.links.remove(link)
        
        # 새 연결 생성
        node_tree.links.new(texture_vector_output, corner_pin_node.inputs['UV'])
        node_tree.links.new(corner_pin_node.outputs['UV'], to_socket)
    
    return True

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
    
    # 활성화 여부에 따라 코너 위치 설정
    corner_pin_node.inputs['Top Left'].default_value = (*corner_pin.top_left, 0.0)
    corner_pin_node.inputs['Top Right'].default_value = (*corner_pin.top_right, 0.0)
    corner_pin_node.inputs['Bottom Left'].default_value = (*corner_pin.bottom_left, 0.0)
    corner_pin_node.inputs['Bottom Right'].default_value = (*corner_pin.bottom_right, 0.0)
    
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