/*
 * Surviveler game package
 * buildings
 */
package surviveler

import (
	"server/events"
	"server/math"
	"time"

	log "github.com/Sirupsen/logrus"
)

/*
 * BuildingBase is a base containing the required fields for every building
 *
 * It also embeds the common buiding features through methods like induceBuildPower,
 * etc.
 */
type BuildingBase struct {
	totalHP      float64 // total hit points
	curHP        float64 // current hit points
	requiredBP   uint16  // required build power to finish construction
	curBP        uint16  // build power already induced into the construction
	id           uint32
	g            *Game
	pos          math.Vec2
	buildingType EntityType
	isBuilt      bool
}

func (bb *BuildingBase) Type() EntityType {
	return bb.buildingType
}

func (bb *BuildingBase) Id() uint32 {
	return bb.id
}

func (bb *BuildingBase) SetId(id uint32) {
	bb.id = id
}

func (bb *BuildingBase) Position() math.Vec2 {
	return bb.pos
}

func (bb *BuildingBase) BoundingBox() math.BoundingBox {
	x, y := bb.pos.Elem()
	return math.NewBoundingBox(x-0.25, x+0.25, y-0.25, y+0.25)
}

func (bb *BuildingBase) State() EntityState {
	return BuildingState{
		Type:         bb.buildingType,
		Xpos:         float32(bb.pos[0]),
		Ypos:         float32(bb.pos[1]),
		CurHitPoints: uint16(bb.curHP),
		Completed:    bb.isBuilt,
	}
}

func (bb *BuildingBase) DealDamage(damage float64) (dead bool) {
	if damage >= bb.curHP {
		bb.curHP = 0
		bb.g.PostEvent(events.NewEvent(
			events.BuildingDestroyId,
			events.BuildingDestroy{Id: bb.id}))
		dead = true
	} else {
		bb.curHP -= damage
	}
	return
}

func (bb *BuildingBase) HealDamage(damage float64) (healthy bool) {
	healthy = true
	return
}

func (bb *BuildingBase) addBuildPower(bp uint16) {
	if !bb.isBuilt {
		bb.curBP += bp
		bb.curHP = bb.totalHP * (float64(bb.curBP) / float64(bb.requiredBP))
		if bb.curBP >= bb.requiredBP {
			bb.isBuilt = true
			bb.curHP = bb.totalHP
			bb.curBP = bb.requiredBP
		}
		log.WithFields(log.Fields{
			"curHP": uint16(bb.curHP), "totHP": uint16(bb.totalHP),
			"curBP": bb.curBP, "reqBP": bb.requiredBP,
		}).Debug("Receiving Build Power")
	}
}

type BuildingUpdater interface {
	Update(dt time.Duration)
}

/*
 * Barricade is a simple barricade building
 *
 * It implements the Building interface
 */
type Barricade struct {
	BuildingBase
}

/*
 * NewBarricade creates a new barricade
 */
func NewBarricade(g *Game, pos math.Vec2, totHP, reqBP uint16) *MgTurret {
	return &MgTurret{
		BuildingBase: BuildingBase{
			id:           InvalidID,
			g:            g,
			pos:          pos,
			totalHP:      float64(totHP),
			curHP:        1,
			requiredBP:   reqBP,
			curBP:        0,
			buildingType: BarricadeBuilding,
		},
		attackPower: 10.0,
	}
}

func (mg *Barricade) Update(dt time.Duration) {
}

/*
 * AddBuildPower adds a given quantity of build power into the building.
 *
 * Build Power is induced by construction or reparation.
 */
func (mg *Barricade) AddBuildPower(bp uint16) {
	mg.addBuildPower(bp)
}

/*
 * IsBuilt indicates if the building is totally constructed.
 *
 * For the case of a building with shooting ability (eg a turret), this
 * implies the building is active and can shoot
 */
func (mg *Barricade) IsBuilt() bool {
	return mg.isBuilt
}

/*
 * MgTurret is a machine-gun turret building
 *
 * It implements the Building interface
 */
type MgTurret struct {
	BuildingBase
	attackPower float64
	lastBurst time.Duration
	lastLock time.Duration
	lastValidTarget time.Duration
	target Entity
}

const (
	//Maximum distance at which the turret can acquire a target
	MgTurretMaxDist float32 = 3.0;
	//Rate at which the turret attempts to acquire a target
	MgTurretAcquiringTargetRate time.Duration = 500 * time.Millisecond
	//time interval between a burst and the next
	MgTurretRateOfFire time.Duration = 250 * time.Millisecond;
	//time needed
	MgTurretLostTarget time.Duration = 500 * time.Millisecond;
)

/*
 * NewMgTurret creates a new machine-gun turret
 */
func NewMgTurret(g *Game, pos math.Vec2, totHP, reqBP uint16) *MgTurret {
	return &MgTurret{
		BuildingBase: BuildingBase{
			id:           InvalidID,
			g:            g,
			pos:          pos,
			totalHP:      float64(totHP),
			curHP:        1,
			requiredBP:   reqBP,
			curBP:        0,
			buildingType: MgTurretBuilding,
		},
		attackPower: 0.2,
	}
}

func (mg *MgTurret) Update(dt time.Duration) {
	mg.lastBurst += dt;
	mg.lastLock += dt;

	//We have a target but we can't fire (out of los or too far)
	if mg.lastValidTarget >= MgTurretLostTarget {
		mg.lastValidTarget = 0;
		mg.target = nil;
		return;
	}

	//if we don't have a target we try to find one
	if mg.target == nil && mg.lastLock >= MgTurretAcquiringTargetRate {
		mg.acquireTarget();
		return;
	}

	//we have a target, we must see if we can shoot him
	if mg.target != nil {
		//check if the target is within distance
		if float32(mg.pos.SquareEuclideanDistance(mg.target.Position())) > MgTurretMaxDist * MgTurretMaxDist {
			//target is too far, can't do shit
			log.WithField("TargetPos", mg.target.Position()).Infof("Target too far!");
			mg.lastValidTarget += dt;
			return;
		}


		ray := mg.g.State().World().LineThrough(mg.pos, mg.target.Position());
		if !ray.IsColliding {
			//target in los, we can shoot!
			if mg.lastBurst >= MgTurretRateOfFire {
				mg.shoot(dt);
				return;
			}
		} else {
			log.WithField("TargetPos", mg.target.Position()).Infof("Target not in los!");
			//target is out of los, can't do shit
			mg.lastValidTarget += dt;
			return;
		}
	}
}

func (mg *MgTurret) shoot(dt time.Duration) {
	log.WithField("TargetPos", mg.target.Position()).Infof("Turrret is shooting");
	//check if the target is in line of sight
	if mg.target.DealDamage(mg.attackPower) {
		//we killed a zombie! clean the target
		mg.target = nil;
	}
	mg.lastBurst = 0;
}

func (mg *MgTurret) acquireTarget() {
	//get the nearest zombie
	world := mg.g.State().World();
	if e, d := mg.g.State().NearestEntity(mg.pos, func(e Entity) bool {
		return e.Type() == ZombieEntity;
	}); d <= MgTurretMaxDist && e != nil {
		//check if the target is in los. If it is the target is locked
		ray := world.CastRay(mg.pos, e.Position().Sub(mg.pos), d);
		if !ray.IsColliding {
			log.WithFields(log.Fields{"Target": e.Id(), "Position": e.Position()}).Infof("Turrret acquired target.");
			mg.target = e;
			mg.lastLock = 0;
		}
	}
}

/*
 * AddBuildPower adds a given quantity of build power into the building.
 *
 * Build Power is induced by construction or reparation.
 */
func (mg *MgTurret) AddBuildPower(bp uint16) {
	mg.addBuildPower(bp)
}

/*
 * IsBuilt indicates if the building is totally constructed.
 *
 * For the case of a building with shooting ability (eg a turret), this
 * implies the building is active and can shoot
 */
func (mg *MgTurret) IsBuilt() bool {
	return mg.isBuilt
}
