package game

import (
	"server/game/events"
	"server/game/messages"
	"server/game/resource"
	"server/math"
	"sync"
)

type EntityFilter func(e Entity) bool

type GameState interface {
	World() *World
	Entity(id uint32) Entity
	NearestEntity(pos math.Vec2, f EntityFilter) (Entity, float32)
	AddEntity(ent Entity)
	MapData() *resource.MapData
	EntityData(EntityType) *resource.EntityData
	BuildingData(EntityType) *resource.BuildingData
	GameTime() int16
}

type Game interface {
	Start()
	State() GameState
	QuitChan() chan struct{}
	MessageChan() chan messages.ClientMessage
	PostEvent(*events.Event)
	Pathfinder() *Pathfinder
	WaitGroup() *sync.WaitGroup
}
