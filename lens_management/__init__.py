from . import database
from . import panel
from . import properties
from . import operators
from . import manager_panel  # 새로 추가

def register():
    print("lens_management.__init__.register() called")
    properties.register()
    operators.register()
    panel.register()
    manager_panel.register()  # 새로 추가
    print("lens_management.__init__.register() completed")

def unregister():
    manager_panel.unregister()  # 새로 추가
    panel.unregister()
    operators.unregister()
    properties.unregister()