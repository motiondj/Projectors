# corner_pin/__init__.py 수정

from . import properties
from . import panel
from . import operators
from . import nodes
from . import presets
from . import visual_tools  # 추가

def register():
    properties.register()
    nodes.register()
    operators.register()
    panel.register()
    presets.register()
    visual_tools.register()  # 추가
    print("4-Corner Pin module registered successfully")

def unregister():
    visual_tools.unregister()  # 추가
    presets.unregister()
    panel.unregister()
    operators.unregister()
    nodes.unregister()
    properties.unregister()