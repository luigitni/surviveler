from matlib import Mat


class SceneRenderContext:
    """Rendering context which is active during the current rendering pass."""

    def __init__(self, rndr, cam):
        """Constructor.

        :param rndr: Active renderer.
        :type rndr: :class:`renderer.Renderer`

        :param cam: Current camera.
        :type cam: :class:`renderer.Camera`
        """
        self._renderer = rndr
        self._camera = cam
        self._modelview_t = cam.modelview
        self._projection_t = cam.projection
        self._view = cam.projection * cam.modelview

    @property
    def renderer(self):
        """Active renderer."""
        return self._renderer

    @property
    def camera(self):
        """Camera to use."""
        return self._camera

    @property
    def modelview(self):
        """Computed model-view transformation matrix."""
        return self._modelview_t

    @property
    def projection(self):
        """Computed projection transformation matrix."""
        return self._projection_t

    @property
    def view(self):
        """Combined projection and model view matrix."""
        return self._view


class Scene:
    """Visual scene which represents the tree of renderable objects.

    The scene has always a root node, to which all other nodes are attached, and
    is always rendered starting from root.
    """

    def __init__(self):
        self.root = RootNode()

    def render(self, rndr, cam):
        """Render the scene using the given renderer.

        :param rndr: Renderer to use.
        :type rndr: :class:`renderer.Renderer`

        :param cam: Camera to use.
        :type cam: :class:`renderer.Camera`
        """
        ctx = SceneRenderContext(rndr, cam)
        self.root.render(ctx)


class SceneNode:
    """Base class for scene nodes.

    A scene node is a renderable element in the scene tree, which can be a
    static geometry, character mesh, UI element and so on.

    Each node has a transformation associated to it, which is local to the node.
    During rendering, that transformation will be chained to those of parent
    nodes and in turn, will affect children nodes.
    """

    def __init__(self):
        self._children = []
        self.parent = None
        self.transform = Mat()

    def render(self, ctx, transform):
        """Renders the node.

        This method should perform all rendering related calls, for which the
        passed computed transform should be used.

        :param ctx: Current render context.
        :type ctx: :class:`SceneRenderContext`

        :param transform: Node's computed transformation matrix. Not to be
            confused with `self.transform`, which describes node's local
            transformation.
        :type transform: :class:`matlib.Mat`
        """
        pass

    @property
    def children(self):
        """List tof children nodes."""
        return self._children

    def add_child(self, node):
        """Add a node as child.

        :param node: Node instance to add as child.
        :type node: a class derived from :class:`renderer.scene.SceneNode`

        :returns: The added node.
        :rtype: :class:`renderer.scene.SceneNode`
        """
        node.parent = self
        self._children.append(node)
        return node

    def remove_child(self, node):
        """Remove a child node.

        :param node: Node instance to remove.
        :type node: a class derived from :class:`renderer.scene.SceneNode`
        """
        try:
            self._children.remove(node)
            node.parent = None
        except ValueError:
            pass

    def to_world(self, pos):
        """Transform local coordinate to world.

        :param pos: Position in node's local coordinate system.
        :type pos: :class:`matlib.Vec`

        :returns: Position in world coordinates.
        :rtype: :class:`matlib.Vec`
        """
        transform = self.transform
        parent = self.parent
        while parent:
            transform *= transform
            parent = parent.parent

        return transform * pos


class RootNode(SceneNode):
    """A special node used as root for the scene tree, which `render()` method
    renders the entire tree and performs the parent-child transformations
    chaining.
    """

    def render(self, ctx, transform=None):
        self.t = Mat()

        def render_all(node, parent_transform):
            self.t.identity()
            self.t *= parent_transform
            self.t *= node.transform
            new_t = Mat(self.t)
            node.render(ctx, new_t)

            for child in node.children:
                render_all(child, new_t)

        for child in self.children:
            render_all(child, self.transform)
