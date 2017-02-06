package math

import "math"

func swap(x0 *int, x1 *int) {
	temp := *x0;
	*x0 = *x1;
	*x1 = temp;
}

//Returns the list of points in a line from v1 to v2
//it uses the Bresenham algorithm to find the points on the line
func BresenhamLine(v0 Vec2, v1 Vec2) []Vec2 {

	x0 := int(v0[0]);
	y0 := int(v0[1]);

	x1 := int(v1[0]);
	y1 := int(v1[1]);

	isSteep := math.Abs(float64(y1) - float64(y0)) > math.Abs(float64(x1) - float64(x0));

	//if the ray is steep invert the axis
	if isSteep {
		swap(&x0, &y0);
		swap(&x1, &y1);
	}

	if x0 > x1 {
		swap(&x0, &x1);
		swap(&y0, &y1);
	}

	//Note: compute the slice size so that we avoid calling append
	line := make([]Vec2, x1 - x0 + 1, x1 -x0 + 1)

	deltaX := x1 - x0;
	deltaY := int(math.Abs(float64(y1) -float64(y0)));
	err := 0;
	yStep := 0;
	y := y0;

	if (y0 < y1) {
		yStep = 1;
	} else {
		yStep = -1;
	}

	i := 0;
	for x := x0; x <= x1; x++ {
		if isSteep {
			line[i] = FromInts(y, x);
		} else {
			line[i] = FromInts(x, y);
		}
		err += deltaY;
		if 2 * err > deltaX {
			y += yStep;
			err -= deltaX;
		}
		i++
	}

	return line;
}
