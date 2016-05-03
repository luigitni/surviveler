from OpenGL.GL import GL_COLOR_BUFFER_BIT
from OpenGL.GL import GL_FRONT_AND_BACK
from OpenGL.GL import GL_LINE
from OpenGL.GL import GL_SHADING_LANGUAGE_VERSION
from OpenGL.GL import GL_VERSION
from OpenGL.GL import glClear
from OpenGL.GL import glClearColor
from OpenGL.GL import glFlush
from OpenGL.GL import glGetString
from OpenGL.GL import glPolygonMode
from exceptions import ConfigError
from exceptions import OpenGLError
from exceptions import SDLError
from utils import as_utf8
import logging
import sdl2 as sdl


LOG = logging.getLogger(__name__)


class Renderer:
    """An OpenGL rendering context.

    A renderer abstracts OS-specific details like window creation and OpenGL
    context set up.
    """

    def __init__(self, config):
        """Constructor.

        Instantiates a window and sets up an OpenGL context for it, which is
        immediately made active, using the given configuration data.

        :param config: Renderer-specific configuration.
        :type config: mapping-like interface.
        """
        try:
            width = int(config['width'])
            height = int(config['height'])
            depth = int(config.get('depth', 24))
            gl_major, gl_minor = [
                int(v) for v in config.get('openglversion', '3.3').split('.')
            ]
        except (KeyError, TypeError, ValueError) as err:
            raise ConfigError(err)

        # window creation
        self.window = sdl.SDL_CreateWindow(
            b"Surviveler",
            sdl.SDL_WINDOWPOS_CENTERED,
            sdl.SDL_WINDOWPOS_CENTERED,
            width,
            height,
            sdl.SDL_WINDOW_OPENGL)
        if self.window is None:
            raise SDLError('Unable to create a {}x{}x{} window'.format(
                width, height, depth))

        # OpenGL 3.3 core profile context initialization
        sdl.SDL_GL_SetAttribute(
            sdl.SDL_GL_CONTEXT_PROFILE_MASK,
            sdl.SDL_GL_CONTEXT_PROFILE_CORE)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MAJOR_VERSION, gl_major)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_CONTEXT_MINOR_VERSION, gl_minor)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_DOUBLEBUFFER, 1)
        sdl.SDL_GL_SetAttribute(sdl.SDL_GL_DEPTH_SIZE, depth)

        self.gl_ctx = sdl.SDL_GL_CreateContext(self.window)
        if self.gl_ctx is None:
            raise OpenGLError('Unable to create OpenGL {}.{} context'.format(
                gl_major, gl_minor))

        LOG.info('OpenGL version: {}'.format(as_utf8(glGetString(GL_VERSION))))
        LOG.info('GLSL version: {}'.format(
            as_utf8(glGetString(GL_SHADING_LANGUAGE_VERSION))))

        self._width = width
        self._height = height
        self.gl_setup(width, height)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def gl_setup(self, width, height):
        """Private."""
        glClearColor(0, 0, 0, 0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    def clear(self):
        """Clear buffers."""
        glClear(GL_COLOR_BUFFER_BIT)

    def present(self):
        """Present updated buffers to screen."""
        glFlush()
        sdl.SDL_GL_SwapWindow(self.window)

    def shutdown(self):
        """Shuts down the renderer.

        Destroys the OpenGL context and the window associated with the renderer.
        """
        sdl.SDL_GL_DeleteContext(self.gl_ctx)
        sdl.SDL_DestroyWindow(self.window)