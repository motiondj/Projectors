# corner_pin/nodes.py 기능 개선 버전

import bpy
import math

def create_corner_pin_node_group():
    """4코너 보정 노드 그룹 생성 - 단순화된 버전"""
    name = 'CornerPinCorrection'
    
    # 이미 존재하면 삭제
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])
    
    # 새 노드 그룹 생성
    node_group = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    
    # 입력/출력 소켓 생성 (블렌더 버전 호환성 처리)
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
    input_node.location = (-600, 0)
    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (400, 0)
    
    # --- 단순화된 4코너 변환 구현 ---
    
    # 입력 UV 분리
    separate_uv = nodes.new('ShaderNodeSeparateXYZ')
    separate_uv.name = "Separate UV"
    separate_uv.location = (-400, 0)
    
    # 지정된 U, V 좌표 (0-1 범위)에서 실제 위치를 계산하는 매핑 노드
    # 공식: P = P₀₀(1-u)(1-v) + P₁₀(u)(1-v) + P₀₁(1-u)(v) + P₁₁(u)(v)
    # 여기서 P는 결과 위치, Pᵢⱼ는 코너 위치, u/v는 입력 UV
    
    # 계산을 위한 U, V 값 얻기
    u_value = separate_uv.outputs[0]  # UV의 X 컴포넌트
    v_value = separate_uv.outputs[1]  # UV의 Y 컴포넌트
    
    # 1-u, 1-v 값을 계산
    one_minus_u = nodes.new('ShaderNodeMath')
    one_minus_u.operation = 'SUBTRACT'
    one_minus_u.inputs[0].default_value = 1.0
    one_minus_u.location = (-200, 100)
    
    one_minus_v = nodes.new('ShaderNodeMath')
    one_minus_v.operation = 'SUBTRACT'
    one_minus_v.inputs[0].default_value = 1.0
    one_minus_v.location = (-200, 40)
    
    # 가중치 계산
    # w00 = (1-u)(1-v) - Top Left
    w_tl = nodes.new('ShaderNodeMath')
    w_tl.operation = 'MULTIPLY'
    w_tl.location = (0, 100)
    
    # w10 = u(1-v) - Top Right
    w_tr = nodes.new('ShaderNodeMath')
    w_tr.operation = 'MULTIPLY'
    w_tr.location = (0, 40)
    
    # w01 = (1-u)v - Bottom Left
    w_bl = nodes.new('ShaderNodeMath')
    w_bl.operation = 'MULTIPLY'
    w_bl.location = (0, -20)
    
    # w11 = uv - Bottom Right
    w_br = nodes.new('ShaderNodeMath')
    w_br.operation = 'MULTIPLY'
    w_br.location = (0, -80)
    
    # 코너 위치 분리
    sep_tl = nodes.new('ShaderNodeSeparateXYZ')
    sep_tl.location = (-400, -140)
    
    sep_tr = nodes.new('ShaderNodeSeparateXYZ')
    sep_tr.location = (-400, -220)
    
    sep_bl = nodes.new('ShaderNodeSeparateXYZ')
    sep_bl.location = (-400, -300)
    
    sep_br = nodes.new('ShaderNodeSeparateXYZ')
    sep_br.location = (-400, -380)
    
    # X좌표 계산 - 각 코너의 X좌표와 가중치를 곱한 후 합산
    mul_x_tl = nodes.new('ShaderNodeMath')
    mul_x_tl.operation = 'MULTIPLY'
    mul_x_tl.location = (150, 100)
    
    mul_x_tr = nodes.new('ShaderNodeMath')
    mul_x_tr.operation = 'MULTIPLY'
    mul_x_tr.location = (150, 40)
    
    mul_x_bl = nodes.new('ShaderNodeMath')
    mul_x_bl.operation = 'MULTIPLY'
    mul_x_bl.location = (150, -20)
    
    mul_x_br = nodes.new('ShaderNodeMath')
    mul_x_br.operation = 'MULTIPLY'
    mul_x_br.location = (150, -80)
    
    # X 좌표 합
    add_x1 = nodes.new('ShaderNodeMath')
    add_x1.operation = 'ADD'
    add_x1.location = (250, 70)
    
    add_x2 = nodes.new('ShaderNodeMath')
    add_x2.operation = 'ADD'
    add_x2.location = (250, -50)
    
    add_x_final = nodes.new('ShaderNodeMath')
    add_x_final.operation = 'ADD'
    add_x_final.location = (330, 10)
    
    # Y좌표 계산 - 각 코너의 Y좌표와 가중치를 곱한 후 합산
    mul_y_tl = nodes.new('ShaderNodeMath')
    mul_y_tl.operation = 'MULTIPLY'
    mul_y_tl.location = (150, -140)
    
    mul_y_tr = nodes.new('ShaderNodeMath')
    mul_y_tr.operation = 'MULTIPLY'
    mul_y_tr.location = (150, -200)
    
    mul_y_bl = nodes.new('ShaderNodeMath')
    mul_y_bl.operation = 'MULTIPLY'
    mul_y_bl.location = (150, -260)
    
    mul_y_br = nodes.new('ShaderNodeMath')
    mul_y_br.operation = 'MULTIPLY'
    mul_y_br.location = (150, -320)
    
    # Y 좌표 합
    add_y1 = nodes.new('ShaderNodeMath')
    add_y1.operation = 'ADD'
    add_y1.location = (250, -170)
    
    add_y2 = nodes.new('ShaderNodeMath')
    add_y2.operation = 'ADD'
    add_y2.location = (250, -290)
    
    add_y_final = nodes.new('ShaderNodeMath')
    add_y_final.operation = 'ADD'
    add_y_final.location = (330, -230)
    
    # 최종 벡터 조합
    combine_xyz = nodes.new('ShaderNodeCombineXYZ')
    combine_xyz.location = (400, -100)
    
    # 노드 연결
    links = node_group.links
    
    # 입력 노드 연결
    links.new(input_node.outputs[0], separate_uv.inputs[0])  # UV
    links.new(input_node.outputs[1], sep_tl.inputs[0])       # Top Left
    links.new(input_node.outputs[2], sep_tr.inputs[0])       # Top Right
    links.new(input_node.outputs[3], sep_bl.inputs[0])       # Bottom Left
    links.new(input_node.outputs[4], sep_br.inputs[0])       # Bottom Right
    
    # UV 분리 및 1-u, 1-v 계산
    links.new(separate_uv.outputs[0], one_minus_u.inputs[1])  # u
    links.new(separate_uv.outputs[1], one_minus_v.inputs[1])  # v
    
    # 가중치 계산
    links.new(one_minus_u.outputs[0], w_tl.inputs[0])        # (1-u)
    links.new(one_minus_v.outputs[0], w_tl.inputs[1])        # (1-v)
    
    links.new(separate_uv.outputs[0], w_tr.inputs[0])         # u
    links.new(one_minus_v.outputs[0], w_tr.inputs[1])        # (1-v)
    
    links.new(one_minus_u.outputs[0], w_bl.inputs[0])        # (1-u)
    links.new(separate_uv.outputs[1], w_bl.inputs[1])         # v
    
    links.new(separate_uv.outputs[0], w_br.inputs[0])         # u
    links.new(separate_uv.outputs[1], w_br.inputs[1])         # v
    
    # X좌표 계산
    links.new(sep_tl.outputs[0], mul_x_tl.inputs[1])         # tl.x
    links.new(sep_tr.outputs[0], mul_x_tr.inputs[1])         # tr.x
    links.new(sep_bl.outputs[0], mul_x_bl.inputs[1])         # bl.x
    links.new(sep_br.outputs[0], mul_x_br.inputs[1])         # br.x
    
    links.new(w_tl.outputs[0], mul_x_tl.inputs[0])           # w_tl
    links.new(w_tr.outputs[0], mul_x_tr.inputs[0])           # w_tr
    links.new(w_bl.outputs[0], mul_x_bl.inputs[0])           # w_bl
    links.new(w_br.outputs[0], mul_x_br.inputs[0])           # w_br
    
    links.new(mul_x_tl.outputs[0], add_x1.inputs[0])         # tl.x * w_tl
    links.new(mul_x_tr.outputs[0], add_x1.inputs[1])         # tr.x * w_tr
    links.new(mul_x_bl.outputs[0], add_x2.inputs[0])         # bl.x * w_bl
    links.new(mul_x_br.outputs[0], add_x2.inputs[1])         # br.x * w_br
    
    links.new(add_x1.outputs[0], add_x_final.inputs[0])      # (tl.x * w_tl) + (tr.x * w_tr)
    links.new(add_x2.outputs[0], add_x_final.inputs[1])      # (bl.x * w_bl) + (br.x * w_br)
    
    # Y좌표 계산
    links.new(sep_tl.outputs[1], mul_y_tl.inputs[1])         # tl.y
    links.new(sep_tr.outputs[1], mul_y_tr.inputs[1])         # tr.y
    links.new(sep_bl.outputs[1], mul_y_bl.inputs[1])         # bl.y
    links.new(sep_br.outputs[1], mul_y_br.inputs[1])         # br.y
    
    links.new(w_tl.outputs[0], mul_y_tl.inputs[0])           # w_tl
    links.new(w_tr.outputs[0], mul_y_tr.inputs[0])           # w_tr
    links.new(w_bl.outputs[0], mul_y_bl.inputs[0])           # w_bl
    links.new(w_br.outputs[0], mul_y_br.inputs[0])           # w_br
    
    links.new(mul_y_tl.outputs[0], add_y1.inputs[0])         # tl.y * w_tl
    links.new(mul_y_tr.outputs[0], add_y1.inputs[1])         # tr.y * w_tr
    links.new(mul_y_bl.outputs[0], add_y2.inputs[0])         # bl.y * w_bl
    links.new(mul_y_br.outputs[0], add_y2.inputs[1])         # br.y * w_br
    
    links.new(add_y1.outputs[0], add_y_final.inputs[0])      # (tl.y * w_tl) + (tr.y * w_tr)
    links.new(add_y2.outputs[0], add_y_final.inputs[1])      # (bl.y * w_bl) + (br.y * w_br)
    
    # 최종 결과 연결
    links.new(add_x_final.outputs[0], combine_xyz.inputs[0])  # X 좌표
    links.new(add_y_final.outputs[0], combine_xyz.inputs[1])  # Y 좌표
    links.new(separate_uv.outputs[2], combine_xyz.inputs[2])  # Z 좌표 (변경 없음)
    
    links.new(combine_xyz.outputs[0], output_node.inputs[0])  # 출력
    
    print(f"Created improved corner pin node group: {name}")
    return node_group

def integrate_corner_pin_with_projector_node_tree(projector_obj):
    """프로젝터 노드 트리에 코너 핀 노드 통합"""
    print(f"Integrating corner pin to projector node tree: {projector_obj.name if projector_obj else 'None'}")
    
    if not projector_obj or projector_obj.type != 'CAMERA':
        print("  - Not a camera object")
        return False
    
    # 스팟 라이트 찾기
    spot = None
    for child in projector_obj.children:
        if child.type == 'LIGHT' and child.data.type == 'SPOT':
            spot = child
            break
    
    if not spot:
        print("  - Spotlight child not found")
        return False
    
    if not spot.data.node_tree:
        print("  - No node tree in spotlight")
        return False
    
    node_tree = spot.data.node_tree
    
    # 디버깅: 모든 노드 출력
    print(f"  - Nodes in node tree: {[node.name for node in node_tree.nodes]}")
    
    # 1. 기존 코너 핀 노드 있는지 확인 (이미 있으면 재사용)
    corner_pin_node = node_tree.nodes.get('Corner Pin')
    if corner_pin_node:
        print("  - Reusing existing Corner Pin node")
    else:
        # 코너 핀 노드 생성
        print("  - Creating new Corner Pin node")
        corner_pin_node = node_tree.nodes.new('ShaderNodeGroup')
        corner_pin_node.name = 'Corner Pin'
        
        # 노드 그룹 생성 또는 가져오기
        node_group_name = 'CornerPinCorrection'
        if node_group_name not in bpy.data.node_groups:
            print("  - Creating new corner pin node group")
            create_corner_pin_node_group()
        else:
            print("  - Using existing corner pin node group")
        
        corner_pin_node.node_tree = bpy.data.node_groups[node_group_name]
    
    # 2. 텍스처 벡터 경로 찾기 (Group 노드의 'texture vector' 출력)
    group_node = None
    texture_vector_output = None
    for node in node_tree.nodes:
        if node.name == 'Group':
            group_node = node
            for output in node.outputs:
                if output.name == 'texture vector':
                    texture_vector_output = output
                    break
            if texture_vector_output:
                break
    
    if not group_node or not texture_vector_output:
        print("  - Failed to find Group node or texture vector output")
        if group_node:
            print(f"  - Group node outputs: {[o.name for o in group_node.outputs]}")
        return False
    
    # 3. 연결된 노드 찾기 (텍스처 벡터가 어디로 연결되는지)
    connected_nodes = []
    for link in node_tree.links:
        if link.from_node == group_node and link.from_socket == texture_vector_output:
            connected_nodes.append((link.to_node, link.to_socket))
            print(f"  - Found connection: {link.to_node.name} > {link.to_socket.name}")
    
    if not connected_nodes:
        print("  - No connections found for texture vector output")
        return False
    
    # 4. 첫 번째 연결에 코너 핀 노드 삽입
    to_node, to_socket = connected_nodes[0]
    
    # 기존 연결 제거
    for link in list(node_tree.links):
        if link.from_node == group_node and link.from_socket == texture_vector_output and link.to_node == to_node:
            node_tree.links.remove(link)
            print(f"  - Removed link: {group_node.name} > {to_node.name}")
    
    # 코너 핀 노드 위치 설정
    corner_pin_node.location = (
        (group_node.location[0] + to_node.location[0]) / 2,
        (group_node.location[1] + to_node.location[1]) / 2 - 200
    )
    print(f"  - Positioned corner pin node at: {corner_pin_node.location}")
    
    # 새 연결 생성
    link1 = node_tree.links.new(texture_vector_output, corner_pin_node.inputs[0])
    link2 = node_tree.links.new(corner_pin_node.outputs[0], to_socket)
    
    print(f"  - Created links: {group_node.name} > Corner Pin > {to_node.name}")
    print(f"  - Link status: {link1 is not None}, {link2 is not None}")
    
    # 5. 초기 코너 값 설정
    corner_pin = projector_obj.corner_pin
    try:
        print("  - Setting initial corner values")
        corner_pin_node.inputs[1].default_value = (*corner_pin.top_left, 0.0)
        corner_pin_node.inputs[2].default_value = (*corner_pin.top_right, 0.0)
        corner_pin_node.inputs[3].default_value = (*corner_pin.bottom_left, 0.0)
        corner_pin_node.inputs[4].default_value = (*corner_pin.bottom_right, 0.0)
        print("  - Corner values set successfully")
    except Exception as e:
        print(f"  - Error setting corner values: {e}")
    
    return True

def apply_corner_pin_to_projector(projector_obj):
    """프로젝터 객체에 4코너 보정 노드 적용"""
    print(f"Applying corner pin to projector: {projector_obj.name if projector_obj else 'None'}")
    
    if not projector_obj or projector_obj.type != 'CAMERA':
        print("  - Not a camera object")
        return False
    
    if not hasattr(projector_obj, 'corner_pin'):
        print("  - No corner_pin attribute")
        return False
    
    # 코너 핀 노드 그룹 통합
    return integrate_corner_pin_with_projector_node_tree(projector_obj)

def update_corner_pin_nodes(projector_obj):
    """코너 핀 노드의 입력값 업데이트 - 개선 버전"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        print("No projector object or corner_pin attribute")
        return False
    
    corner_pin = projector_obj.corner_pin
    print(f"Update corner values for {projector_obj.name}")
    print(f"- Values: TL={corner_pin.top_left}, TR={corner_pin.top_right}, BL={corner_pin.bottom_left}, BR={corner_pin.bottom_right}")
    
    # 스팟 라이트 찾기
    spot = None
    for child in projector_obj.children:
        if child.type == 'LIGHT' and child.data.type == 'SPOT':
            spot = child
            break
    
    if not spot or not spot.data.node_tree:
        print("No spotlight or node tree found")
        return False
    
    node_tree = spot.data.node_tree
    corner_pin_node = node_tree.nodes.get('Corner Pin')
    
    if not corner_pin_node:
        print("No Corner Pin node found")
        if corner_pin.enabled:
            return apply_corner_pin_to_projector(projector_obj)
        return False
    
    # 코너 값 설정 (다양한 방법 시도)
    methods_tried = []
    success = False
    
    # 방법 1: 인덱스로 접근 (기본 방법)
    try:
        print("Trying method 1: Accessing by index")
        corner_pin_node.inputs[1].default_value = (corner_pin.top_left[0], corner_pin.top_left[1], 0.0)
        corner_pin_node.inputs[2].default_value = (corner_pin.top_right[0], corner_pin.top_right[1], 0.0)
        corner_pin_node.inputs[3].default_value = (corner_pin.bottom_left[0], corner_pin.bottom_left[1], 0.0)
        corner_pin_node.inputs[4].default_value = (corner_pin.bottom_right[0], corner_pin.bottom_right[1], 0.0)
        methods_tried.append("index")
        success = True
        print("- Method 1 successful")
    except Exception as e:
        print(f"- Method 1 failed: {e}")
    
    # 방법 2: 이름으로 접근
    if not success:
        try:
            print("Trying method 2: Accessing by name")
            corner_pin_node.inputs['Top Left'].default_value = (corner_pin.top_left[0], corner_pin.top_left[1], 0.0)
            corner_pin_node.inputs['Top Right'].default_value = (corner_pin.top_right[0], corner_pin.top_right[1], 0.0)
            corner_pin_node.inputs['Bottom Left'].default_value = (corner_pin.bottom_left[0], corner_pin.bottom_left[1], 0.0)
            corner_pin_node.inputs['Bottom Right'].default_value = (corner_pin.bottom_right[0], corner_pin.bottom_right[1], 0.0)
            methods_tried.append("name")
            success = True
            print("- Method 2 successful")
        except Exception as e:
            print(f"- Method 2 failed: {e}")
    
    # 방법 3: 인덱스 상세 디버깅
    if not success:
        try:
            print("Trying method 3: Detailed index debugging")
            for i, socket in enumerate(corner_pin_node.inputs):
                print(f"  Socket {i}: {socket.name}, type: {socket.type}")
            
            # 일반적으로 첫 번째 소켓은 'UV'이고 그 다음이 코너 위치들
            start_idx = 1
            if len(corner_pin_node.inputs) >= start_idx + 4:
                corner_pin_node.inputs[start_idx].default_value = (corner_pin.top_left[0], corner_pin.top_left[1], 0.0)
                corner_pin_node.inputs[start_idx+1].default_value = (corner_pin.top_right[0], corner_pin.top_right[1], 0.0)
                corner_pin_node.inputs[start_idx+2].default_value = (corner_pin.bottom_left[0], corner_pin.bottom_left[1], 0.0)
                corner_pin_node.inputs[start_idx+3].default_value = (corner_pin.bottom_right[0], corner_pin.bottom_right[1], 0.0)
                methods_tried.append("detailed_index")
                success = True
                print("- Method 3 successful")
            else:
                print(f"- Not enough inputs: {len(corner_pin_node.inputs)}")
        except Exception as e:
            print(f"- Method 3 failed: {e}")
    
    # 방법 4: 노드 그룹 내부 접근
    if not success:
        try:
            print("Trying method 4: Accessing node group internals")
            group_node = corner_pin_node.node_tree
            if group_node:
                # 그룹 입력 노드 찾기
                input_node = None
                for node in group_node.nodes:
                    if node.type == 'GROUP_INPUT':
                        input_node = node
                        break
                
                if input_node:
                    # 연결된 소켓 찾기
                    for link in group_node.links:
                        if link.from_node == input_node:
                            socket_name = link.from_socket.name
                            if 'Top Left' in socket_name:
                                target_node = link.to_node
                                target_socket = link.to_socket
                                print(f"  Found link for Top Left: {target_node.name}.{target_socket.name}")
                                # 여기서 값을 설정하는 대신 연결을 확인만 함
                    
                    methods_tried.append("group_internals")
                    print("- Method 4 completed (connection check only)")
            else:
                print("- No node group found")
        except Exception as e:
            print(f"- Method 4 failed: {e}")
    
    # 직접 노드 그룹 데이터 수정 (가장 강력한 방법)
    if not success:
        try:
            print("Trying method 5: Direct node group data modification")
            # 노드 그룹 이름 가져오기
            node_group_name = corner_pin_node.node_tree.name
            node_group = bpy.data.node_groups[node_group_name]
            
            # 디버깅 정보 출력
            print(f"  Node group: {node_group_name}")
            print(f"  Inputs: {[i.name for i in node_group.inputs]}")
            
            # 직접 노드 그룹 소켓 접근
            if 'Top Left' in [i.name for i in node_group.inputs]:
                node_group.inputs['Top Left'].default_value = (corner_pin.top_left[0], corner_pin.top_left[1], 0.0)
                node_group.inputs['Top Right'].default_value = (corner_pin.top_right[0], corner_pin.top_right[1], 0.0)
                node_group.inputs['Bottom Left'].default_value = (corner_pin.bottom_left[0], corner_pin.bottom_left[1], 0.0)
                node_group.inputs['Bottom Right'].default_value = (corner_pin.bottom_right[0], corner_pin.bottom_right[1], 0.0)
                methods_tried.append("direct_group_data")
                success = True
                print("- Method 5 successful")
        except Exception as e:
            print(f"- Method 5 failed: {e}")
    
    if success:
        print(f"Successfully updated corner values using methods: {', '.join(methods_tried)}")
    else:
        print("All methods failed to update corner values")
    
    return success

def node_is_in_path(node_tree, node):
    """노드가 노드 트리의 활성 경로에 있는지 확인"""
    # 입력 소켓에 연결된 링크가 있는지 확인
    has_input_links = False
    for input in node.inputs:
        if input.is_linked:
            has_input_links = True
            break
    
    # 출력 소켓에 연결된 링크가 있는지 확인
    has_output_links = False
    for output in node.outputs:
        if output.is_linked:
            has_output_links = True
            break
    
    # 양쪽 모두 연결되어 있어야 경로에 있는 것으로 판단
    return has_input_links and has_output_links

def bypass_corner_pin_node(node_tree, node):
    """코너 핀 노드를 우회하고 직접 연결"""
    # 입력과 출력 연결 찾기
    input_links = []
    output_links = []
    
    for link in node_tree.links:
        if link.to_node == node:
            input_links.append((link.from_node, link.from_socket, link.to_socket))
        elif link.from_node == node:
            output_links.append((link.to_node, link.to_socket, link.from_socket))
    
    # 모든 기존 링크 제거
    for link in list(node_tree.links):
        if link.to_node == node or link.from_node == node:
            node_tree.links.remove(link)
    
    # 입력 노드와 출력 노드 직접 연결
    if input_links and output_links:
        for from_node, from_socket, _ in input_links:
            for to_node, to_socket, _ in output_links:
                node_tree.links.new(from_socket, to_socket)
                print(f"Bypassed corner pin: {from_node.name} > {to_node.name}")

def register():
    print("corner_pin.nodes.register() called")
    # 노드 그룹 생성은 필요할 때만 수행
    # create_corner_pin_node_group()

def unregister():
    print("corner_pin.nodes.unregister() called")
    # 노드 그룹 삭제
    if 'CornerPinCorrection' in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups['CornerPinCorrection'])