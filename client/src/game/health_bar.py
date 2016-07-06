from context import Context
from game import Entity
from game.components import Renderable
from math import pi
from matlib import Vec
from renderer import Rect
import logging
import math


LOG = logging.getLogger(__name__)


class HealthBar(Entity):
    """Game entity which represents a generic health bar."""

    def __init__(self, resource, value, parent_node):
        """Constructor.

        :param resource: The health bar resource
        :type resource: :class:`loaders.Resource`

        :param value: The percentage of health
        :type value: :class:`float`

        :param parent_node: The parent node in the scene graph
        :type parent_node: :class:`renderer.scene.SceneNode`
        """
        self._value = value

        self.w = resource.data['width']
        self.h = resource.data['height']
        self.y_offset = resource.data['y_offset']

        mesh = resource.userdata.get('mesh')
        if not mesh:
            mesh = Rect(self.w, self.h)
            resource.userdata['mesh'] = mesh

        shader = resource['shader']

        params = {
            'width': float(self.w),
            'value': value * self.w,
            'bg_color': Vec(0, 0, 0, 1),
            'fg_color': Vec(0.2, 0.4, 1, 1),
        }

        renderable = Renderable(
            parent_node,
            mesh,
            shader,
            params,
            enable_light=False)

        t = renderable.transform
        t.translate(Vec(-self.w / 2, self.y_offset, 0))
        t.rotate(Vec(1, 0, 0), pi / 2)

        super().__init__(renderable)

    @property
    def value(self):
        """Returns the value [0,1] of that is currently displayed.

        :returns: The value of the health bar
        :rtype: :class:`float`
        """
        return self._value

    @value.setter
    def value(self, v):
        """Sets the value [0,1] to be displayed.

        :param v: The value of the health bar
        :type v: :class:`float`
        """
        self._value = v
        self[Renderable].node.params['value'] = v * self.w

    def destroy(self):
        """Removes itself from the scene.
        """
        LOG.debug('Destroying health bar')
        node = self[Renderable].node
        node.parent.remove_child(node)

    def update(self, dt):
        """Updates the health bar.

        :param dt: Time delta from last update.
        :type dt: float
        """
        context = Context.get_instance()
        c_pos = context.camera.position
        direction = Vec(c_pos.x, c_pos.y, c_pos.z, 1)
        direction.norm()
        z_axis = Vec(0, 0, 1)

        # Find the angle between the camera and the health bar, then rotate it.
        angle = math.acos(z_axis.dot(direction))
        t = self[Renderable].transform
        t.identity()
        t.translate(Vec(-self.w / 2, self.y_offset, 0))
        t.rotate(Vec(1, 0, 0), angle)