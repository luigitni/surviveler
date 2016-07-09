from context import Context
from events import subscriber
from game import Character
from game.character import EntityType
from game.events import EntitySpawn
from utils import to_scene
import logging


LOG = logging.getLogger(__name__)


class Player(Character):
    """Game entity representing the local player"""

    def update(self, dt):
        """Update the local player.

        This method computes player's game logic as a function of time and sends
        the appropriate event.

        :param dt: Time delta from last update.
        :type dt: float
        """
        super(Player, self).update(dt)

        x, y = self.position

        # update camera position
        context = Context.get_instance()
        context.camera.set_position(to_scene(x, y))


@subscriber(EntitySpawn)
def player_spawn(evt):
    """Instantiate and add the local player into the game.

    :param evt: The event instance
    :type evt: :class:`game.events.EntitySpawn`
    """
    LOG.debug('Event subscriber: {}'.format(evt))
    context = evt.context

    # Only instantiate the player if it does not exist
    entity_exists = context.resolve_entity(evt.srv_id)

    # NOTE: check if the srv_id is exactly the player id received from the
    # server during the handshake.
    is_player = evt.srv_id == evt.context.player_id

    if not entity_exists and is_player:
        # Search for the proper resource to use basing on the entity_type.
        # FIXME: right now it defaults on grunts.
        entities = context.res_mgr.get('/entities')
        resource = context.res_mgr.get(
            entities.data['entities_map'].get(
                EntityType(evt.entity_type).name,
                '/characters/grunt'
            )
        )

        # Search for the player name
        name = context.players_name_map[evt.srv_id]
        # Create the player
        player = Player(resource, name, evt.health, context.scene.root)
        context.entities[player.e_id] = player
        context.server_entities_map[evt.srv_id] = player.e_id
