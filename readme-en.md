# Blender Projector Add-on

A Blender add-on for easy creation and management of physically-based projectors. Implements realistic projection simulation using real manufacturer lens data.

English | [한국어](README.md)

![Projector Add-on for Blender title image](/.github/gifs/title.jpg)

## Features

* Easy creation and manipulation of physically-based projectors
* Real-world projector settings like throw ratio, resolution, and lens shift
* Support for real lens data from various manufacturers (Epson, Christie, Sony, Panasonic, Barco, etc.)
* Project test textures or your own content like images and videos
* Preview the projections in Cycles render mode

## Lens Database

* Contains real lens data from various manufacturers (Epson, Christie, Sony, Panasonic, Barco, NEC, BenQ, JVC, Optoma, Digital Projection, etc.)
* Lens data is based on publicly available information, and some values may be approximate
* **Note**: The lens data in the included JSON files should be used for reference only. Before applying to actual projects, please verify with the manufacturers' latest technical specifications and modify the data if necessary.

## References

* This add-on is based on Jonas Schell's [Blender Projector Add-on](https://github.com/Ocupe/Projectors), with an added lens management system for simulating real projector lens data.

## Projectors Add-on in Action

### Throw Ratio
![Throw Ratio](/.github/gifs/throw_ratio.gif)

### Lens Shift
![Lens Shift](/.github/gifs/lens_shift.gif)

### Image Textures & Resolution
![Image Texture & Resolutions](/.github/gifs/image_textures_resolution.gif)

## Compatibility
* Works with Blender 2.8 and above

## Installation

1. Download this repository as a ZIP file.
2. Open Blender.
3. Go to `Edit > Preferences > Add-ons`.
4. Click `Install from File` and select the downloaded ZIP file.
5. Find "Lighting: Projector" in the list and enable it by clicking the checkbox.

## Documentation

* [User Manual](docs/user_manual_en.md) - Detailed guide on using the add-on
* [Developer Documentation](docs/developer_docs_en.md) - Technical documentation for developers

## Contributing

Issues and feature requests are welcome. If you'd like to contribute to this project:

1. Fork the repository.
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request.

## License

This project is distributed under the GNU GPL v3 License. See `LICENSE` for more information.

## Contact

If you have questions or suggestions, please create an issue or contact the repository maintainer.

---

P.S. Germans like to call a projector, a beamer.
