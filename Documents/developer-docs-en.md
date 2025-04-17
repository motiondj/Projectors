# Blender Projector Add-on Developer Documentation

[한국어 버전](developer-docs-ko.md)

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Modules](#core-modules)
4. [Lens Management System](#lens-management-system)
5. [Data Structures](#data-structures)
6. [API Documentation](#api-documentation)
7. [Extension Guide](#extension-guide)
8. [Testing and Debugging](#testing-and-debugging)

## Introduction

The Blender Projector Add-on is a tool for simulating the physical characteristics of real projectors in Blender. This developer documentation provides information needed to understand and extend the add-on's internal structure and functionality.

### Development Environment

- Blender version compatibility: 2.8 and above
- Python version: 3.7 and above
- Additional dependencies: None (uses only Blender's built-in Python environment)

## Project Structure

The overall structure of the add-on is as follows:

```
projector/
├── __init__.py           # Add-on entry point
├── projector.py          # Core projector functionality
├── ui.py                 # Projector UI
├── operators.py          # Operator implementations
├── helper.py             # Utility functions
├── tests.py              # Test code
└── lens_management/      # Lens management system
    ├── __init__.py       # Lens module initialization
    ├── database.py       # Data loading and management
    ├── properties.py     # Lens property definitions
    ├── panel.py          # Panel for Projector tab
    ├── operators.py      # Lens-related operators
    ├── manager_panel.py  # Panel for Lens Manager tab
    └── database/         # Lens data files
        ├── epson.json    # Epson lens data
        ├── panasonic.json # Panasonic lens data
        ├── christie.json # Christie lens data
        ├── barco.json    # Barco lens data
        └── sony.json     # Sony lens data
```

### Key File Descriptions

- **`__init__.py`**: Add-on metadata and register/unregister functions
- **`projector.py`**: Core functionality including projector creation, settings management, and node tree setup
- **`ui.py`**: Blender UI panels and related elements
- **`operators.py`**: Operators for creating, deleting projectors, etc.
- **`helper.py`**: Collection of utility functions
- **`lens_management/`**: Lens management system module
  - **`database.py`**: Lens database loading and management functions
  - **`properties.py`**: Blender property definitions and update callbacks
  - **`panel.py`**: Lens selection UI integrated into Projector tab
  - **`operators.py`**: Lens-related operators (add, edit, delete, etc.)
  - **`manager_panel.py`**: Dedicated tab UI for lens management

## Core Modules

### Projector Creation and Setup

Projectors are created using the `create_projector()` function in `projector.py`. This function:

1. Creates spotlight and camera objects
2. Sets the spotlight as a child of the camera
3. Adds a custom node tree to the spotlight
4. Initializes projector settings (calls `init_projector()`)

```python
def create_projector(context):
    # Create spotlight
    bpy.ops.object.light_add(type='SPOT', location=(0, 0, 0))
    spot = context.object
    # Setup...
    add_projector_node_tree_to_spot(spot)
    
    # Create camera
    bpy.ops.object.camera_add(...)
    cam = context.object
    
    # Set parent relationship
    spot.parent = cam
    
    return cam
```

### Node Tree System

The core functionality of the projector is implemented through a complex node tree applied to the spotlight:

- **Texture Mapping**: Maps projection images to 3D space
- **Pixel Grid**: Grid overlay for resolution visualization
- **Image Mixing**: Switching between checker, color grid, and custom textures

### Update Functions

Major projector settings are handled by their respective update functions:

- `update_throw_ratio()`: Updates throw ratio and related camera settings
- `update_lens_shift()`: Updates lens shift and texture mapping
- `update_resolution()`: Handles resolution changes
- `update_projected_texture()`: Handles projection texture changes
- `update_checker_color()`: Updates checker texture color
- `update_pixel_grid()`: Toggles pixel grid display

## Lens Management System

The lens management system provides functionality to load real manufacturer lens data and apply it to projector settings.

### Database Management

The `LensDatabase` class (in `database.py`) loads and manages lens data from JSON files:

```python
class LensDatabase:
    def __init__(self):
        self.manufacturers = {}
        self.cache = {}
        self.last_load_time = {}
        self.load_all_databases()
    
    def load_all_databases(self):
        # Load all JSON files
        
    def get_manufacturers(self):
        # Return list of manufacturers
    
    def get_models(self, manufacturer):
        # Return list of models for a specific manufacturer
    
    def get_lens_profile(self, manufacturer, model):
        # Return profile data for a specific lens
```

### Property System

`properties.py` defines Blender properties and update callbacks for lens selection:

```python
class LensManagerProperties(bpy.types.PropertyGroup):
    manufacturer: EnumProperty(
        name="Manufacturer",
        items=get_manufacturers,
        update=update_manufacturer
    )
    
    model: EnumProperty(
        name="Model",
        items=get_models,
        update=update_lens_settings
    )
```

### Projector Integration

Lens data is applied to projector settings through the `update_from_lens_profile()` function:

```python
def update_from_lens_profile(projector_obj, lens_profile):
    # Update projector settings based on lens profile data
    # Set limitation values for throw ratio, lens shift, etc.
```

Projector settings are adjusted according to the physical limitations of the lens:
- Slider range limitations (hard_min, hard_max)
- Adjustment of out-of-range values (force_within_limits)
- Visual feedback (UI warnings)

## Data Structures

### JSON Schema

Lens data is stored in JSON files with the following structure:

```json
{
  "MODEL_NUMBER": {
    "specs": {
      "focal_length": {"min": value, "max": value, "default": value},
      "throw_ratio": {"min": value, "max": value, "default": value},
      "f_stop": {"min": value, "max": value, "default": value},
      "lens_shift": {
        "h_shift_range": [min%, max%],
        "v_shift_range": [min%, max%]
      },
      "supported_resolutions": ["1920x1080", "3840x2160", ...],
      "notes": "additional description"
    },
    "optical_properties": {
      "distortion": value,
      "chromatic_aberration": value,
      "vignetting": value
    }
  }
}
```

### Data Conversion

Values loaded from the database are converted into formats usable in Blender through various conversion functions:

- `parse_throw_ratio()`: Parses throw ratio strings to min/max values
- `percent_to_blender_shift()`: Converts percentage shift values to Blender units
- `throw_ratio_to_focal_length()`: Converts throw ratio to focal length

## API Documentation

### Blender Integration

### Core API

#### Projector Creation and Management

- `create_projector(context)`: Creates and returns a new projector object
- `init_projector(proj_settings, context)`: Initializes projector settings
- `update_from_lens_profile(projector_obj, lens_profile)`: Applies lens profile data to a projector
- `is_within_lens_limits(projector_obj)`: Checks if projector settings are within lens limitations

#### Utility Functions

- `get_projectors(context, only_selected=False)`: Gets all or selected projector objects in the scene
- `get_projector(context)`: Gets the currently selected projector
- `get_resolution(proj_settings, context)`: Gets the currently used resolution

### Lens Management API

#### Database Access

- `lens_db.get_manufacturers()`: Gets list of manufacturers
- `lens_db.get_models(manufacturer)`: Gets list of models for a specific manufacturer
- `lens_db.get_lens_profile(manufacturer, model)`: Gets specific lens profile
- `lens_db.get_throw_ratio_limits(manufacturer, model)`: Gets throw ratio limitations
- `lens_db.get_lens_shift_limits(manufacturer, model, is_horizontal=True)`: Gets lens shift limitations

#### Data Management

- `lens_db.add_manufacturer(name)`: Adds a new manufacturer
- `lens_db.add_lens_model(manufacturer, model_id, specs)`: Adds a new lens model
- `lens_db.update_lens_model(manufacturer, model_id, specs)`: Updates lens model information
- `lens_db.delete_lens_model(manufacturer, model_id)`: Deletes a lens model
- `lens_db.import_database(filepath)`: Imports lens data from a JSON file
- `lens_db.export_database(filepath, manufacturer=None)`: Exports lens data to a JSON file
- `lens_db.refresh_database()`: Refreshes the database

## Extension Guide

### Adding New Features

To extend the lens management system, follow these steps:

1. **Add New Data Fields**:
   - Modify the `standardize_lens_data()` function in `database.py`
   - Update the JSON schema to include new fields
   - Add new Blender properties in `properties.py`

2. **Add New UI Elements**:
   - Add new UI elements in `panel.py` or `manager_panel.py`
   - Define new panel classes if needed

3. **Implement Feature Logic**:
   - Add necessary functions to appropriate modules
   - Implement update callback functions

### Extending Optical Simulation

Extension guide for future optical distortion simulation:

1. **Create New Node Group**:
   ```python
   def create_optical_effects_node_group():
       # Create node group for distortion, chromatic aberration, vignetting effects
   ```

2. **Connect Lens Profile Properties**:
   ```python
   def apply_optical_properties(profile, projector_obj):
       # Connect lens profile optical properties to node group
   ```

3. **Add UI Controls**:
   ```python
   class OPTICAL_PT_effects_panel(Panel):
       # UI panel for optical effects controls
   ```

### Adding New Manufacturers and Lens Data

To permanently add new manufacturers or lens data:

1. Create a `[manufacturer].json` file in the `lens_management/database/` directory
2. Structure the data as follows:
   ```json
   {
     "MODEL_ID": {
       "specs": {
         "focal_length": {"min": 18.0, "max": 25.0, "default": 21.0},
         "throw_ratio": {"min": 1.2, "max": 1.7, "default": 1.45},
         ...
       },
       "optical_properties": {
         ...
       }
     }
   }
   ```
3. Restart the add-on or call `refresh_database()`

## Testing and Debugging

### Test Framework

The add-on includes a basic test framework:
- Unit tests defined in the `tests.py` file
- Test execution for various Blender versions through `cmd.py`

```python
# Run tests
python cmd.py test
```

### Debugging Tips

1. **Enable Console Logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Data Validation Errors**:
   ```python
   errors = lens_db.validate_database()
   if errors:
       print("Database validation errors:", errors)
   ```

3. **Prevent Infinite Recursion**:
   Use flags in update functions to prevent infinite recursion:
   ```python
   if getattr(update_function, '_is_updating', False):
       return
   update_function._is_updating = True
   try:
       # Update logic
   finally:
       update_function._is_updating = False
   ```

4. **Cache Mechanism**:
   Clear cache when troubleshooting:
   ```python
   # Clear cache
   clear_cache()
   ```
