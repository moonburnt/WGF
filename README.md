# Whatever Game Framework

## Description:

**WGF** is an experimental game framework built on top of pygame, with goal to
provide some basic out-of-box, genre-independant functionality (easy scene and
assets management, spritesheets support, etc) in flask-inspired fashion. Right
now its but hobby/research project, with primary focus on tinkering with pygame
and improving common gamedev-related skills.

## Installation:

This library is available on pypi - to install it with pip, simply run:
`pip install WGF`

Or, to enable support for configuration files in toml:
`pip install WGF[toml_support]`

If you run into any pygame-related issues during installation (most likely 
caused by pygame version used by this library having no pre-build wheel for 
your python version) - refer to pygame wiki to find out which dependencies 
you may need to compile it: https://www.pygame.org/wiki/Compilation

## License:

[MIT](LICENSE)
