bl_info = {
    "name": "Projection Simulator",
    "author": "Original: Jonas Schell, Modifications: motiondj",
    "description": "Easy Projector creation and modification with lens management system.",
    "blender": (2, 81, 0),
    "version": (2025, 4, 1),
    "location": "3D Viewport > Add > Light > Projection Simulator",
    "category": "Lighting",
    "wiki_url": "",
    "tracker_url": ""
}

import bpy  
from . import ui
from . import projector
from . import operators

def register():
    projector.register()
    operators.register()
    ui.register()
    
    # 렌즈 관리 등록
    try:
        print("Attempting to import lens_management...")
        from . import lens_management
        print("Successfully imported lens_management")
        lens_management.register()
        
        # 렌즈 오퍼레이터 등록 확인
        if hasattr(lens_management, 'operators'):
            if not hasattr(bpy.types, 'LENS_OT_force_within_limits'):
                print("LENS_OT_force_within_limits not registered, attempting to register...")
                try:
                    bpy.utils.register_class(lens_management.operators.LENS_OT_force_within_limits)
                except Exception as e:
                    print(f"Error registering LENS_OT_force_within_limits: {e}")
        
        print("Successfully registered lens_management")
    except Exception as e:
        print(f"Error registering lens_management: {str(e)}")
    
    # 코너 핀 모듈 등록 추가
    try:
        print("Attempting to import corner_pin...")
        from . import corner_pin
        print("Successfully imported corner_pin")
        
        # 이전에 등록된 경우 먼저 등록 해제
        try:
            corner_pin.unregister()
        except:
            pass
        
        corner_pin.register()
        print("Successfully registered corner_pin")
    except Exception as e:
        print(f"Error registering corner_pin: {str(e)}")

def unregister():
    # 코너 핀 모듈 등록 해제 추가
    try:
        from . import corner_pin
        corner_pin.unregister()
    except Exception as e:
        print(f"Error unregistering corner_pin: {str(e)}")
    
    try:
        from . import lens_management
        lens_management.unregister()
    except Exception as e:
        print(f"Error unregistering lens_management: {str(e)}")
        
    ui.unregister()
    operators.unregister()
    projector.unregister()