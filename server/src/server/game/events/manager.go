/*
 * Surviveler events package
 * event manager
 */
package events

type EventHandler func(*Event)

// Private helper type
type listenerMap map[EventType][]EventHandler

type EventManager struct {
	eventQueue chan *Event
	listeners  listenerMap
}

func NewEventManager(q chan *Event) *EventManager {
	self := new(EventManager)
	self.eventQueue = q
	self.listeners = make(listenerMap)
	return self
}

/*
 * registers an event handler for a specified event type.
 */
func (self *EventManager) Subscribe(eventType EventType, callback EventHandler) {
	lst, ok := self.listeners[eventType]
	if !ok {
		lst = make([]EventHandler, 0)
	}
	self.listeners[eventType] = append(lst, callback)
}

/*
 * continuously process events blocking when no events are available
 */
func (self *EventManager) Process() {
	for event := range self.eventQueue {
		lst, ok := self.listeners[event.Type]
		if ok {
			for _, callback := range lst {
				callback(event)
			}
		}
	}
}