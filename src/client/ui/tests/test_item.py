from ui.item import Anchor
from ui.item import CyclicDependencyError
from ui.item import Item
from ui.item import Margin
from ui.item import ValidationError
from ui.item.root import RootItem
from ui.util.point import Point
import pytest


class Dummy(Item):
    def __init__(self, *args, **kwargs):
        test_id = kwargs.pop('test_id', None)
        super().__init__(*args, **kwargs)
        if test_id:
            self.test_id = test_id

    def update(self, dt):
        pass


@pytest.fixture
def item_cls():
    return Dummy


@pytest.fixture
def parent_item():
    item = RootItem(500, 500)
    item.test_id = 'parent'
    return item


def test_item_is_abtract():
    with pytest.raises(TypeError):
        Item()


def test_item__with_redundant_width_height(item_cls, parent_item):
    # Explicit width and two horizontal anchor values
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                left='parent.left',
                right='parent.right',
                top='parent.top'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                left='parent.left',
                hcenter='parent.hcenter',
                top='parent.top'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                hcenter='parent.hcenter',
                right='parent.right',
                top='parent.top'),
            width=100, height=100)
    # Explicit height and two vertical anchor values
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                top='parent.top',
                bottom='parent.bottom',
                left='parent.left'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                top='parent.top',
                vcenter='parent.vcenter',
                left='parent.left'),
            width=100, height=100)
    with pytest.raises(ValidationError):
        item_cls(
            parent_item,
            anchor=Anchor(
                vcenter='parent.vcenter',
                bottom='parent.bottom',
                left='parent.left'),
            width=100, height=100)


def test_item__without_information(item_cls, parent_item):
    with pytest.raises(ValidationError):
        item_cls(parent_item)


def test_item__with_position_and_size(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(parent_item, position=Point(25, 25), width=30, height=30)
    parent_item.add_child('child', item)
    parent_item.bind_item()
    assert item.anchor == {
        AT.left: 25,
        AT.hcenter: 40,
        AT.right: 55,
        AT.top: 25,
        AT.vcenter: 40,
        AT.bottom: 55,
    }
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == Point(25, 25)
    assert item.width == 30
    assert item.height == 30


def test_item__sub_item_with_position_and_size(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(parent_item, position=Point(25, 25), width=30, height=30)
    parent_item.add_child('child', item)
    sub_item = item_cls(item, position=Point(25, 25), width=30, height=30)
    item.add_child('child', sub_item)
    parent_item.bind_item()
    assert sub_item.anchor == {
        AT.left: 50,
        AT.hcenter: 65,
        AT.right: 80,
        AT.top: 50,
        AT.vcenter: 65,
        AT.bottom: 80,
    }
    assert sub_item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert sub_item.position == Point(50, 50)
    assert sub_item.width == 30
    assert sub_item.height == 30


def test_item__with_anchor_fill(item_cls, parent_item):
    MT = Margin.MarginType
    item = item_cls(parent_item, anchor=Anchor.fill())
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == parent_item.anchor
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == parent_item.position
    assert item.width == parent_item.width
    assert item.height == parent_item.height


def test_item__with_cutom_anchor(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor(
            top='parent.vcenter',
            bottom='parent.bottom',
            hcenter='parent.hcenter'),
        width=100)
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: 200,
        AT.hcenter: 250,
        AT.right: 300,
        AT.top: 250,
        AT.vcenter: 375,
        AT.bottom: 500,
    }
    assert item.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }
    assert item.position == Point(200, 250)
    assert item.width == 100
    assert item.height == 250


def test_item__with_fill_anchor_and_symmetric_margin(item_cls, parent_item):
    MARGIN = 10
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor.fill(),
        margin=Margin.symmetric(MARGIN))
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: parent_item.anchor[AT.left] + MARGIN,
        AT.hcenter: parent_item.anchor[AT.hcenter],
        AT.right: parent_item.anchor[AT.right] - MARGIN,
        AT.top: parent_item.anchor[AT.top] + MARGIN,
        AT.vcenter: parent_item.anchor[AT.vcenter],
        AT.bottom: parent_item.anchor[AT.bottom] - MARGIN,
    }
    assert item.margin == {
        MT.left: MARGIN,
        MT.right: MARGIN,
        MT.top: MARGIN,
        MT.bottom: MARGIN,
    }

    assert item.width == parent_item.width - 2 * MARGIN
    assert item.height == parent_item.height - 2 * MARGIN


def test_item__with_complex_anchor_and_margin(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.hcenter',
            top='parent.top',
            bottom='parent.hcenter'),
        margin=Margin(left=4, right=10, top=10, bottom=4))
    parent_item.add_child('child', item)
    parent_item.bind_item()

    assert item.anchor == {
        AT.left: 4,
        AT.hcenter: 122,
        AT.right: 240,
        AT.top: 10,
        AT.vcenter: 128,
        AT.bottom: 246,
    }
    assert item.margin == {
        MT.left: 4,
        MT.right: 10,
        MT.top: 10,
        MT.bottom: 4,
    }

    assert item.width == 236
    assert item.height == 236


def test_item__with_sibling_dependencies(item_cls, parent_item):
    AT = Anchor.AnchorType
    MT = Margin.MarginType

    item1 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            top='parent.top'),
        height=100)
    item2 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            top='item1.bottom'),
        height=100)
    item3 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            top='item2.bottom'),
        height=100)
    item4 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            top='item3.bottom'),
        height=100)
    parent_item.add_child('item3', item3)
    parent_item.add_child('item2', item2)
    parent_item.add_child('item1', item1)
    parent_item.add_child('item4', item4)
    parent_item.bind_item()

    assert item1.anchor == {
        AT.left: 0,
        AT.hcenter: 250,
        AT.right: 500,
        AT.top: 0,
        AT.vcenter: 50,
        AT.bottom: 100,
    }
    assert item1.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }

    assert item1.width == 500
    assert item1.height == 100

    assert item2.anchor == {
        AT.left: 0,
        AT.hcenter: 250,
        AT.right: 500,
        AT.top: 100,
        AT.vcenter: 150,
        AT.bottom: 200,
    }
    assert item2.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }

    assert item2.width == 500
    assert item2.height == 100

    assert item3.anchor == {
        AT.left: 0,
        AT.hcenter: 250,
        AT.right: 500,
        AT.top: 200,
        AT.vcenter: 250,
        AT.bottom: 300,
    }
    assert item3.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }

    assert item3.width == 500
    assert item3.height == 100

    assert item4.anchor == {
        AT.left: 0,
        AT.hcenter: 250,
        AT.right: 500,
        AT.top: 300,
        AT.vcenter: 350,
        AT.bottom: 400,
    }
    assert item4.margin == {
        MT.left: 0,
        MT.right: 0,
        MT.top: 0,
        MT.bottom: 0,
    }

    assert item4.width == 500
    assert item4.height == 100


def test_item__with_sibling_dependencies__cyclic(item_cls, parent_item):
    item1 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            bottom='item2.top'),
        height=100)
    item2 = item_cls(
        parent_item,
        anchor=Anchor(
            left='parent.left',
            right='parent.right',
            top='item1.bottom'),
        height=100)
    parent_item.add_child('item1', item1)
    parent_item.add_child('item2', item2)
    with pytest.raises(CyclicDependencyError):
        parent_item.bind_item()


def test_item__traverse__no_filters(item_cls, parent_item):
    for i in range(10):
        tid = '{}'.format(i)
        item = item_cls(
            parent_item,
            test_id=tid,
            anchor=Anchor.fill())
        parent_item.add_child('{}'.format(i), item)
        for j in range(10):
            tid = '{}-{}'.format(i, j)
            sub_item = item_cls(
                item,
                test_id=tid,
                anchor=Anchor.fill())
            item.add_child('{}-{}'.format(i, j), sub_item)
    parent_item.bind_item()

    i = 10
    j = 10
    for item in parent_item.traverse():
        if i and j:
            assert getattr(item, 'test_id') == '{}-{}'.format(i - 1, j - 1)
            j -= 1
        elif i and not j:
            assert getattr(item, 'test_id') == '{}'.format(i - 1)
            j = 10
            i -= 1
        elif not i and not j:
            assert getattr(item, 'test_id') == 'parent'


def test_item__traverse__pos_filter(item_cls, parent_item):
    item1 = item_cls(
        parent_item,
        test_id='item1',
        anchor=Anchor(
            top='parent.top',
            bottom='parent.vcenter',
            left='parent.left',
            right='parent.hcenter'
        ))
    parent_item.add_child('item1', item1)
    item2 = item_cls(
        parent_item,
        test_id='item2',
        anchor=Anchor(
            top='parent.vcenter',
            bottom='parent.bottom',
            left='parent.hcenter',
            right='parent.right'
        ))
    parent_item.add_child('item2', item2)
    parent_item.bind_item()

    assert [getattr(i, 'test_id') for i in parent_item.traverse(pos=Point(250, 250))] == ['item2', 'item1', 'parent']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(pos=Point(125, 125))] == ['item1', 'parent']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(pos=Point(375, 375))] == ['item2', 'parent']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(pos=Point(125, 375))] == ['parent']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(pos=Point(375, 125))] == ['parent']


def test_item__traverse__pos_and_listen_filter(item_cls, parent_item):
    item1 = item_cls(
        parent_item,
        test_id='item1',
        on={
            'event1': lambda: False,
        },
        anchor=Anchor(
            top='parent.top',
            bottom='parent.vcenter',
            left='parent.left',
            right='parent.hcenter'
        ))
    parent_item.add_child('item1', item1)
    item2 = item_cls(
        parent_item,
        test_id='item2',
        on={
            'event2': lambda: False,
        },
        anchor=Anchor(
            top='parent.vcenter',
            bottom='parent.bottom',
            left='parent.hcenter',
            right='parent.right'
        ))
    parent_item.add_child('item2', item2)
    parent_item.bind_item()

    # Localized items that handles event1
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(250, 250))] == ['item1']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(125, 125))] == ['item1']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(375, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(125, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(375, 125))] == []
    # Localized items that handles event2
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(250, 250))] == ['item2']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(125, 125))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(375, 375))] == ['item2']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(125, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(375, 125))] == []


def test_item__traverse__pos_and_listen_filter__deferred_handler(item_cls, parent_item):
    item1 = item_cls(
        parent_item,
        test_id='item1',

        anchor=Anchor(
            top='parent.top',
            bottom='parent.vcenter',
            left='parent.left',
            right='parent.hcenter'
        ))
    parent_item.add_child('item1', item1)
    item1.on('event1', lambda: False)
    item2 = item_cls(
        parent_item,
        test_id='item2',
        anchor=Anchor(
            top='parent.vcenter',
            bottom='parent.bottom',
            left='parent.hcenter',
            right='parent.right'
        ))
    parent_item.add_child('item2', item2)
    item2.on('event2', lambda: False)
    parent_item.bind_item()

    # Localized items that handles event1
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(250, 250))] == ['item1']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(125, 125))] == ['item1']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(375, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(125, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event1', pos=Point(375, 125))] == []
    # Localized items that handles event2
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(250, 250))] == ['item2']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(125, 125))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(375, 375))] == ['item2']
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(125, 375))] == []
    assert [getattr(i, 'test_id') for i in parent_item.traverse(listen_to='event2', pos=Point(375, 125))] == []
