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
    """프로젝터 노드 트리에 코너 핀 노드 통합 - 개선된 버전"""
    print(f"Integrating corner pin to projector node tree: {projector_obj.name}")
    
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
    
    # 필요한 노드 찾기
    group_node = None  # "!! Don't touch !!" 노드
    image_texture_node = None  # 이미지 텍스처 노드
    emission_node = None  # Emission 노드
    light_output_node = None  # Light Output 노드
    
    for node in node_tree.nodes:
        if node.name == 'Group':  # "!! Don't touch !!" 노드
            group_node = node
        elif node.bl_idname == 'ShaderNodeTexImage':  # 이미지 텍스처 노드
            image_texture_node = node
        elif node.bl_idname == 'ShaderNodeEmission':  # Emission 노드
            emission_node = node
        elif node.bl_idname == 'ShaderNodeOutputLight':  # Light Output 노드
            light_output_node = node
    
    if not group_node:
        print("  - Group node not found")
        return False
    
    if not image_texture_node:
        print("  - Image Texture node not found")
        return False
    
    if not emission_node:
        print("  - Emission node not found")
        return False
    
    if not light_output_node:
        print("  - Light Output node not found")
        return False
    
    # texture vector 출력 찾기
    texture_vector_output = None
    for output in group_node.outputs:
        if output.name == 'texture vector':
            texture_vector_output = output
            break
    
    if not texture_vector_output:
        print("  - texture vector output not found")
        return False
    
    # Vector 입력 찾기
    vector_input = None
    for input in image_texture_node.inputs:
        if input.name == 'Vector':
            vector_input = input
            break
    
    if not vector_input and len(image_texture_node.inputs) > 0:
        # Vector 이름이 없으면 첫 번째 입력 사용
        vector_input = image_texture_node.inputs[0]
    
    if not vector_input:
        print("  - Vector input not found")
        return False
    
    # 중요: 항상 Emission -> Light Output 연결 확인 및 생성
    emission_to_light_exists = False
    for link in node_tree.links:
        if (link.from_node == emission_node and 
            link.to_node == light_output_node):
            emission_to_light_exists = True
            break
    
    if not emission_to_light_exists:
        node_tree.links.new(emission_node.outputs[0], light_output_node.inputs[0])
        print("  - Created missing Emission -> Light Output link")
    
    # 코너 핀 노드 생성 또는 재사용
    corner_pin_node = node_tree.nodes.get('Corner Pin')
    if corner_pin_node:
        print("  - Using existing Corner Pin node")
    else:
        print("  - Creating new Corner Pin node")
        corner_pin_node = node_tree.nodes.new('ShaderNodeGroup')
        corner_pin_node.name = 'Corner Pin'
        
        # 노드 그룹 생성 또는 가져오기
        node_group_name = 'CornerPinCorrection'
        if node_group_name not in bpy.data.node_groups:
            create_corner_pin_node_group()
        
        corner_pin_node.node_tree = bpy.data.node_groups[node_group_name]
        
        # 노드 위치 설정
        corner_pin_node.location = (
            (group_node.location[0] + image_texture_node.location[0]) / 2,
            group_node.location[1] - 150
        )
    
    # 기존 연결 확인 - 모든 연결 시나리오 체크
    has_group_to_corner_pin = False
    has_corner_pin_to_image = False
    has_direct_group_to_image = False
    
    for link in node_tree.links:
        if (link.from_node == group_node and 
            link.from_socket == texture_vector_output and 
            link.to_node == corner_pin_node):
            has_group_to_corner_pin = True
        
        if (link.from_node == corner_pin_node and 
            link.to_node == image_texture_node):
            has_corner_pin_to_image = True
            
        if (link.from_node == group_node and 
            link.from_socket == texture_vector_output and 
            link.to_node == image_texture_node):
            has_direct_group_to_image = True
    
    # 코너 핀이 활성화된 경우
    if projector_obj.corner_pin.enabled:
        # 코너 핀을 통한 연결 설정
        if has_direct_group_to_image:
            # 직접 연결 제거 (코너 핀이 활성화되었으므로)
            for link in list(node_tree.links):
                if (link.from_node == group_node and 
                    link.from_socket == texture_vector_output and 
                    link.to_node == image_texture_node):
                    node_tree.links.remove(link)
                    print("  - Removed direct Group -> Image Texture link")
        
        # 필요한 연결 생성
        if not has_group_to_corner_pin:
            link1 = node_tree.links.new(texture_vector_output, corner_pin_node.inputs[0])
            print(f"  - Created link: Group -> Corner Pin: {link1 is not None}")
        
        if not has_corner_pin_to_image:
            link2 = node_tree.links.new(corner_pin_node.outputs[0], vector_input)
            print(f"  - Created link: Corner Pin -> Image Texture: {link2 is not None}")
        
        # 코너 값 설정
        try:
            corner_pin_node.inputs[1].default_value = (projector_obj.corner_pin.top_left[0], projector_obj.corner_pin.top_left[1], 0.0)
            corner_pin_node.inputs[2].default_value = (projector_obj.corner_pin.top_right[0], projector_obj.corner_pin.top_right[1], 0.0)
            corner_pin_node.inputs[3].default_value = (projector_obj.corner_pin.bottom_left[0], projector_obj.corner_pin.bottom_left[1], 0.0)
            corner_pin_node.inputs[4].default_value = (projector_obj.corner_pin.bottom_right[0], projector_obj.corner_pin.bottom_right[1], 0.0)
            print("  - Corner values set successfully")
        except Exception as e:
            print(f"  - Error setting corner values: {e}")
    else:
        # 코너 핀이 비활성화된 경우
        if has_group_to_corner_pin or has_corner_pin_to_image:
            # 코너 핀 노드 연결 제거
            for link in list(node_tree.links):
                if ((link.from_node == group_node and link.to_node == corner_pin_node) or
                    (link.from_node == corner_pin_node and link.to_node == image_texture_node)):
                    node_tree.links.remove(link)
                    print(f"  - Removed link: {link.from_node.name} -> {link.to_node.name}")
        
        # 직접 연결 생성 (코너 핀 비활성화시)
        if not has_direct_group_to_image:
            link = node_tree.links.new(texture_vector_output, vector_input)
            print(f"  - Created direct link: Group -> Image Texture: {link is not None}")
    
    # Image -> Emission 연결 확인
    image_to_emission_exists = False
    for link in node_tree.links:
        if (link.from_node == image_texture_node and 
            link.to_node == emission_node):
            image_to_emission_exists = True
            break
    
    if not image_to_emission_exists:
        # Image -> Emission 연결 (Color)
        image_color_output = None
        for output in image_texture_node.outputs:
            if output.name == 'Color':
                image_color_output = output
                break
        
        if image_color_output:
            link3 = node_tree.links.new(image_color_output, emission_node.inputs[0])
            print(f"  - Created missing link: Image Texture -> Emission: {link3 is not None}")
    
    return True

def update_corner_pin_nodes(projector_obj):
    """코너 핀 노드의 입력값 업데이트 - 개선 버전"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        print("No projector object or corner_pin attribute")
        return False
    
    corner_pin = projector_obj.corner_pin
    
    # 코너 핀 활성화 여부에 따라 노드 연결 설정
    success = integrate_corner_pin_with_projector_node_tree(projector_obj)
    
    if success:
        print(f"Updated corner pin nodes for {projector_obj.name}")
        return True
    else:
        print(f"Failed to update corner pin nodes for {projector_obj.name}")
        return False

def apply_corner_pin_to_projector(projector_obj):
    """프로젝터 객체에 4코너 보정 노드 적용 - 개선된 버전"""
    print(f"Applying corner pin to projector: {projector_obj.name if projector_obj else 'None'}")
    
    if not projector_obj or projector_obj.type != 'CAMERA':
        print("  - Not a camera object")
        return False
    
    if not hasattr(projector_obj, 'corner_pin'):
        print("  - No corner_pin attribute")
        return False
    
    # 프로젝션 모드 체크
    if not hasattr(projector_obj, 'proj_settings') or projector_obj.proj_settings.projected_texture != 'custom_texture':
        print("  - Not in custom texture mode, corner pin won't be applied")
        projector_obj.corner_pin.enabled = False
        return False
    
    # 코너 핀 노드 그룹 통합
    result = integrate_corner_pin_with_projector_node_tree(projector_obj)
    
    # 로그 메시지
    if result:
        print("  - Corner pin applied successfully")
    else:
        print("  - Failed to apply corner pin")
    
    return result

def update_corner_pin_nodes(projector_obj):
    """코너 핀 노드의 입력값 업데이트 - 개선 버전"""
    if not projector_obj or not hasattr(projector_obj, 'corner_pin'):
        print("No projector object or corner_pin attribute")
        return False
    
    corner_pin = projector_obj.corner_pin
    
    # 코너 핀이 비활성화된 경우 업데이트 필요 없음
    if not corner_pin.enabled:
        return False
    
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
            # 코너 핀이 활성화된 경우, 노드를 생성하고 설정 시도
            return apply_corner_pin_to_projector(projector_obj)
        return False
    
    # 코너 값 설정 성공 여부
    success = False
    
    try:
        # 먼저 노드에 올바른 입력 포트가 있는지 확인
        if len(corner_pin_node.inputs) >= 5:
            corner_pin_node.inputs[1].default_value = (corner_pin.top_left[0], corner_pin.top_left[1], 0.0)
            corner_pin_node.inputs[2].default_value = (corner_pin.top_right[0], corner_pin.top_right[1], 0.0)
            corner_pin_node.inputs[3].default_value = (corner_pin.bottom_left[0], corner_pin.bottom_left[1], 0.0)
            corner_pin_node.inputs[4].default_value = (corner_pin.bottom_right[0], corner_pin.bottom_right[1], 0.0)
            success = True
            print("- Corner pin values updated successfully")
        else:
            print(f"- Corner pin node has insufficient inputs: {len(corner_pin_node.inputs)}")
            # 노드 그룹이 예상과 다르게 구성되어 있을 수 있음
            if corner_pin_node.node_tree and corner_pin_node.node_tree.name != 'CornerPinCorrection':
                print(f"- Warning: Corner pin node has unexpected node tree: {corner_pin_node.node_tree.name}")
    except Exception as e:
        print(f"- Error setting corner values: {e}")
    
    # 연결 확인 및 업데이트
    if success and projector_obj.proj_settings.projected_texture == 'custom_texture':
        # 커스텀 텍스처 모드에서 연결 확인
        has_valid_connection = False
        custom_tex_node = None
        
        # 이미지 텍스처 노드 찾기
        for node in node_tree.nodes:
            if node.bl_idname == 'ShaderNodeTexImage':
                custom_tex_node = node
                break
        
        if custom_tex_node:
            # Corner Pin -> Image Texture 연결 확인
            for link in node_tree.links:
                if link.to_node == custom_tex_node and link.from_node == corner_pin_node:
                    has_valid_connection = True
                    break
            
            # Group -> Corner Pin 연결 확인
            group_connected = False
            group_node = node_tree.nodes.get('Group')
            if group_node:
                for link in node_tree.links:
                    if link.from_node == group_node and link.to_node == corner_pin_node:
                        group_connected = True
                        break
            
            if not has_valid_connection or not group_connected:
                # 연결 다시 수행
                print("- Corner pin connections need to be reestablished")
                try:
                    # 이 경로는 safety check임 - 실제로는 정상 연결 유지를 위한 경로
                    result = apply_corner_pin_to_projector(projector_obj)
                    if result:
                        print("- Corner pin connections reestablished successfully")
                    else:
                        print("- Failed to reestablish corner pin connections")
                except Exception as e:
                    print(f"- Failed to reconnect corner pin: {e}")
    
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
    """코너 핀 노드를 우회하고 직접 연결
    
    Args:
        node_tree: 노드 트리 객체
        node: 우회할 코너 핀 노드
    """
    if not node_tree or not node:
        print("Invalid node tree or node")
        return
    
    print(f"Bypassing corner pin node: {node.name}")
    
    # 입력과 출력 연결 찾기
    input_links = []  # (from_node, from_socket, to_socket)
    output_links = []  # (to_node, to_socket, from_socket)
    
    for link in node_tree.links:
        if link.to_node == node:
            input_links.append((link.from_node, link.from_socket, link.to_socket))
            print(f"  - Found input link: {link.from_node.name} -> {node.name}")
        elif link.from_node == node:
            output_links.append((link.to_node, link.to_socket, link.from_socket))
            print(f"  - Found output link: {node.name} -> {link.to_node.name}")
    
    # 모든 기존 링크 제거
    links_removed = 0
    for link in list(node_tree.links):
        if link.to_node == node or link.from_node == node:
            node_tree.links.remove(link)
            links_removed += 1
    
    print(f"  - Removed {links_removed} links")
    
    # 입력 노드와 출력 노드 직접 연결
    if input_links and output_links:
        for from_node, from_socket, _ in input_links:
            for to_node, to_socket, _ in output_links:
                # 각 입력 노드를 모든 출력 노드에 연결
                new_link = node_tree.links.new(from_socket, to_socket)
                print(f"  - Bypassed corner pin: {from_node.name} > {to_node.name}: {new_link is not None}")
    else:
        print("  - No links to bypass (missing input or output links)")
    
    # 일반적으로 !! Don't touch !! -> Image Texture 연결이 필요한 경우 처리
    group_node = None
    image_texture_node = None
    
    for n in node_tree.nodes:
        if n.name == 'Group':
            group_node = n
        elif n.bl_idname == 'ShaderNodeTexImage':
            image_texture_node = n
    
    if group_node and image_texture_node:
        # texture vector 출력 찾기
        texture_vector_output = None
        for output in group_node.outputs:
            if output.name == 'texture vector':
                texture_vector_output = output
                break
        
        if texture_vector_output:
            # Vector 입력 찾기
            vector_input = None
            for input in image_texture_node.inputs:
                if input.name == 'Vector':
                    vector_input = input
                    break
            
            if not vector_input and len(image_texture_node.inputs) > 0:
                vector_input = image_texture_node.inputs[0]
            
            if vector_input:
                # 이미 이 연결이 있는지 확인
                direct_link_exists = False
                for link in node_tree.links:
                    if (link.from_node == group_node and 
                        link.from_socket == texture_vector_output and 
                        link.to_node == image_texture_node and 
                        link.to_socket == vector_input):
                        direct_link_exists = True
                        break
                
                # 없으면 생성
                if not direct_link_exists:
                    link = node_tree.links.new(texture_vector_output, vector_input)
                    print(f"  - Created fallback direct link: Group -> Image Texture: {link is not None}")

def register():
    print("corner_pin.nodes.register() called")
    # 노드 그룹 생성은 필요할 때만 수행
    # create_corner_pin_node_group()

def unregister():
    print("corner_pin.nodes.unregister() called")
    # 노드 그룹 삭제
    if 'CornerPinCorrection' in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups['CornerPinCorrection'])