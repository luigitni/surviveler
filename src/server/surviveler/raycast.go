package surviveler

import "server/math"
import log "github.com/Sirupsen/logrus"

type RayCastResult struct {
	IsColliding bool
	CollidingPos math.Vec2
}

func CastRay(world *World, origin math.Vec2, dir math.Vec2, length float32) RayCastResult {

	result := RayCastResult{IsColliding:false}

	if int(length) == 0 {
		result.CollidingPos = origin;
	}

	normDir := dir.Normalize();

	line := math.BresenhamLine(origin,
		origin.Add(
			math.Vec2{normDir.X() * float64(length), normDir.Y() * float64(length)},
		),
	);

	l := len(line);

	log.WithField("BresenhamLine", line).Info("Bresenham line computed");

	if l > 0 {
		idx := 0;

		excludesOrigin := math.FromInts(int(origin.X()), int(origin.Y())) != line[0];

		if excludesOrigin {
			idx = l - 1;
		}

		for ;; {
			point := line[idx];
			if !world.IsPointTraversable(point) {
				result.IsColliding = true;
				result.CollidingPos = point;
				log.Info("colliding");
				break;
			}

			if excludesOrigin {
				log.Info("Excludes origin");
				idx--;
				if idx < 0 {
					break;
				}
			} else {
				log.Info("includes origin");
				idx++;
				if idx > l {
					break;
				}
			}
		}
	}

	return result;
}