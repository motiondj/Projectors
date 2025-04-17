import bpy  
from . import ui
from . import projector
from . import operators
# 여기서 lens_management 임포트 제거

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
        # LENS_OT_force_within_limits 오퍼레이터가 operators.py에 제대로 등록되었는지 확인
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


def unregister():
    from . import lens_management
    lens_management.unregister()
    ui.unregister()
    operators.unregister()
    projector.unregister()