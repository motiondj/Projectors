# Blender Projector Add-on User Manual

[한국어 버전](user-manual-ko.md)

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Lens Selection and Application](#lens-selection-and-application)
5. [Lens Management](#lens-management)
6. [Troubleshooting](#troubleshooting)

## Introduction

The Blender Projector Add-on is a tool for simulating the physical characteristics of real projectors in a 3D environment. With this add-on, you can:

- Create and manipulate physically-based projectors
- Apply real-world projector settings like throw ratio, resolution, and lens shift
- Achieve accurate projection simulation based on real manufacturer lens data
- Project test textures or your own content (images, videos)
- Preview projections in Cycles render mode

## Installation

1. Download the latest version of the add-on from the GitHub repository.
2. Do not unzip the downloaded ZIP file.
3. Open Blender and navigate to `Edit > Preferences > Add-ons`.
4. Click on `Install from File` and select the downloaded ZIP file.
5. Find "Lighting: Projector" in the list and enable it by clicking the checkbox.

## Basic Usage

### Creating a Projector

1. In the 3D viewport, select `Add > Light > Projector`.
2. Alternatively, click the `New` button in the Projector panel (Sidebar > Projector tab).

### Adjusting Projector Settings

With a projector selected, adjust the following settings in the Projector tab of the sidebar:

- **Throw Ratio**: The ratio of projection distance to image width
- **Power**: The brightness of the projector
- **Resolution**: The projection resolution
- **Horizontal/Vertical Shift**: Horizontal/vertical lens shift
- **Project**: Type of image to project (Checker, Color Grid, or Custom Texture)
- **Show Pixel Grid**: Toggle to display a pixel grid

### Using Custom Images

1. Select `Custom Texture` from the `Project` dropdown.
2. In the image selection field that appears, choose or import your desired image.
3. Enable `Let Image Define Projector Resolution` to automatically set the projector resolution to match the image.

## Lens Selection and Application

### Selecting Manufacturer and Lens Model

1. Select your projector.
2. Find the `Lens Management` section in the Projector tab of the sidebar.
3. Choose a manufacturer (e.g., Epson, Christie, Sony) from the `Manufacturer` dropdown.
4. Select a lens model from the `Model` dropdown.

### Viewing Lens Specifications

After selecting a lens, you can view the following information:
- Throw Ratio range
- Focal Length
- F-Stop values
- Lens Shift range
- Optical properties (distortion, chromatic aberration, vignetting)

### Lens Limitations

When a lens is selected, the possible range of values for projector settings is automatically restricted to match the physical limitations of the lens:

- The minimum/maximum values of sliders are limited to the possible range of the lens.
- Values outside the lens range are highlighted in red.
- Click the "Fix" button to automatically adjust to values within the lens range.

## Lens Management

### Opening the Lens Management Panel

1. Select the `Lens Manager` tab in the sidebar.
2. Here you can manage manufacturers and lens models.

### Adding a New Manufacturer

1. Click the `+` button in the `Manufacturers` section.
2. Enter the manufacturer name in the dialog and confirm.

### Adding a New Lens Model

1. Select a manufacturer.
2. Click the `+` button in the `Lens Models` section.
3. In the dialog, enter the following information:
   - Model ID: The model identifier
   - Throw Ratio: Min/max values
   - Lens Shift Range: Min/max values for horizontal/vertical shift
   - Focal Length: Min/max/default values
   - F-Stop: Min/max/default values
   - Optical Properties: Distortion, chromatic aberration, vignetting values
   - Additional Info: Notes or references

### Editing and Deleting Lens Data

1. Click the edit icon next to a manufacturer or model to modify its information.
2. Click the delete icon to remove a manufacturer or model.

### Importing/Exporting Data

1. In the `Database Operations` section:
   - Click `Import` to import lens data from a JSON file.
   - Click `Export` to save the current data to a JSON file.
   - Click `Refresh` to reload the database.

## Troubleshooting

### Projector Not Visible

- Ensure the render engine is set to Cycles. (Image projection does not work in Eevee)
- Check for warnings in the Projector panel and click the "Change to Cycles" button.

### Lens Limitation Issues

- If values are shown in red, they exceed the physical limitations of the lens.
- Click the "Fix" button to adjust values within the allowed range.

### Lens Database Errors

- If database files are corrupted, you may need to restore from a backup or reinstall.
- For JSON format errors, check the syntax in the database files using a text editor.

### Lens Manager Panel Not Showing

- Make sure the add-on is properly activated.
- Try restarting Blender to see if this resolves the issue.
