from PIL import Image
import numpy as np
import os
import sys
from collections import namedtuple


EXAMPLE = np.array(
    [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
    ],
    np.uint8
)


Box = namedtuple('Box', ['x', 'y'])
NearVertices = namedtuple('NearVertices', ['left', 'up', 'right', 'down'])
NearBoxes = namedtuple('NearBoxes', ['upleft', 'upright', 'downright', 'downleft'])


ROW = np.array(
    [
        [255, 0, 0, 0, 255],
        [255, 255, 255, 255],
    ])


LEFT = np.array([-1, 0])
UP = np.array([0, 1])
RIGHT = np.array([1, 0])
DOWN = np.array([0, -1])


DIRECTIONS = {
    (
        (0, 0),
        (0, 0)): (),
    (
        (0, 0),
        (0, 1)): (RIGHT, DOWN),
    (
        (0, 0),
        (1, 0)): (LEFT, DOWN),
    (
        (0, 0),
        (1, 1)): (LEFT, RIGHT),
    (
        (0, 1),
        (0, 0)): (UP, RIGHT),
    (
        (0, 1),
        (0, 1)): (UP, DOWN),
    (
        (0, 1),
        (1, 0)): (LEFT, UP, RIGHT, DOWN),
    (
        (0, 1),
        (1, 1)): (LEFT, UP),
    (
        (1, 0),
        (0, 0)): (LEFT, UP),
    (
        (1, 0),
        (0, 1)): (LEFT, UP, RIGHT, DOWN),
    (
        (1, 0),
        (1, 0)): (UP, DOWN),
    (
        (1, 0),
        (1, 1)): (UP, RIGHT),
    (
        (1, 1),
        (0, 0)): (LEFT, RIGHT),
    (
        (1, 1),
        (0, 1)): (LEFT, DOWN),
    (
        (1, 1),
        (1, 0)): (RIGHT, DOWN),
    (
        (1, 1),
        (1, 1)): (),
}


def load(image_path):
    image = Image.open(image_path)
    grayscale = image.convert('L')
    return np.array(grayscale)


class VertexBoxes:
    """Eases the manipulation of a vertex and near squared 2x2 boxes group.
    """
    def __init__(self, map_, xy):
        self.map = map_
        self.x, self.y = xy
        bx, by = self.map.map_vertex(tuple(xy))

        self.boxes = NearBoxes(
            upleft=(bx - 1, by - 1), upright=(bx, by - 1),  # the 2 upper boxes
            downleft=(bx - 1, by), downright=(bx, by),  # the 2 lower boxes
        )
        self.upper_boxes = self.boxes.upleft, self.boxes.upright
        self.right_boxes = self.boxes.upright, self.boxes.downright
        self.lower_boxes = self.boxes.downright, self.boxes.downleft
        self.left_boxes = self.boxes.upleft, self.boxes.downleft

        # 2 x 2 matrix cotaining box values relative to the vertex
        self.block_matrix = [
            [self.map.get(self.boxes.upleft, 0), self.map.get(self.boxes.upright, 0)],
            [self.map.get(self.boxes.downleft, 0), self.map.get(self.boxes.downright, 0)],
        ]


def is_black(arr, xy):
    x, y = xy
    return arr[(y, x)] == 0


def get_neighbours_values(arr, xy):
    """Returns a dict containing the neighbour values per position.

    :rtype: dict
    """
    ret = {}
    x, y = xy
    height, width = arr.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            tx = x + dx
            ty = y + dy
            if 0 <= tx < width and 0 <= ty < height:
                ret[(dx, dy)] = is_black(arr, (tx, ty))
            else:
                ret[(dx, dy)] = None
    return ret


def get_neighbours(arr, xy):
    """Tells you the list of nearby black pixels.

    :rtype: list
    """
    ret = []
    values = get_neighbours_values(arr, xy)
    for xy, black in values.items():
        if black:
            ret.append(xy)
    return ret


def find_box(arr):
    for y, row in enumerate(arr):
        for x, value in enumerate(row):
            if is_black(arr, (x, y)):
                return x, y


def box2vertices(xy, size):
    x, y = xy
    return (((x + dx) * size, (y + dy) * size) for dy in (0, 1) for dx in (0, 1))


class Map(dict):

    def __init__(self, data, box_size=1):
        super().__init__(data)
        self.map = data
        self.box_size = box_size

    def map_box(self, xy):
        """Given a box position, returns its top-left vertex.
        """
        x, y = xy
        return x * self.box_size, y * self.box_size

    def map_vertex(self, xy):
        """Given a vertex position, returns the map box whose the
        vertex is the top-left one.
        """
        x, y = xy
        return int(x / self.box_size), int(y / self.box_size)

    def vertex2boxes(self, xy):
        """Returns the 4 neighbour map boxes (white or not)
        which share the same given vertex.
        """
        # get the box whose the vertex is the top-left
        return VertexBoxes(self, xy)

    def vertex2blocks(self, xy):
        return [box for box in self.vertex2boxes(xy) if box in self.map]

    def get_next_grid_vertices(self, vertex):
        """Returns the 4 neighbour possible vertices.
        """
        vx, vy = vertex
        return NearVertices(
            up=(vx, vy + self.box_size),
            right=(vx + self.box_size, vy),
            down=(vx, vy - self.box_size),
            left=(vx - self.box_size, vy),
        )

    def get_next_block_vertices(self, vertex):
        """Returns neighbour vertices which are actually block edges or vertices
        (i.e. contiguous to map walls, so not free space vertices).
        """
        ret = []
        v_boxes = self.vertex2boxes(vertex)
        versors = DIRECTIONS[v_boxes.block_matrix]
        ret = [vertex + v for v in versors]
        print('next({}) = {}'.format(vertex, ret))
        return ret

    def build(self):
        #start_box = find_box(self.arr)
        start_box = min(sorted(self.map.keys()))

        v0 = self.map_box(start_box)
        print('Start from {}'.format(v0))
        #self.vertices[v0] = None

        vertex = v0
        tracked = [v0]
        while True:
            for v_next in self.get_next_block_vertices(vertex):
                if v_next not in tracked:
                    break
                else:
                    print('{} in tracked {}'.format(v_next, tracked))

            if v_next in tracked:
                break
            print(v_next)
            tracked.append(v_next)
            vertex = v_next

        # find new contiguous free position to move vertex to


#assert get_edges(ROW) == [((0, 1), 3)], 'fail: {}'.format(get_edges(ROW))


def build_obj(arr, size=1):
    res = []
    v_counter = 1
    vn = 1
    vertices = []
    faces = []
    for y, row in enumerate(arr):
        for x, value in enumerate(row):
            if value == 0:
                v1 = x * size, y * size, 0.0
                v2 = (x + 1) * size, y * size, 0.0
                v3 = x * size, (y + 1) * size, 0.0
                v4 = (x + 1) * size, (y + 1) * size, 0.0
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v1))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v2))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v3))
                vertices.append('v {:.6f} {:.6f} {:.6f}'.format(*v4))
                face = 'f {v1_i} {v2_i} {v3_i} {v4_i}'.format(
                    v1_i=v_counter, v2_i=v_counter + 1, v3_i=v_counter + 3, v4_i=v_counter + 2
                )
                faces.append(face)
                v_counter += 4
                vn += 1
    res.extend(vertices)
    res.append('s off')
    res.extend(faces)
    return '\n'.join(res)


def export_obj(obj, dst):
    with open(dst, 'w') as fp:
        fp.write(obj)
    return os.path.getsize(dst)


def main(image_filepath):
    arr = load(image_filepath)
    obj = build_obj(arr)
    print(export_obj(obj, 'test.obj'))


if __name__ == '__main__':
    main(sys.argv[1])
