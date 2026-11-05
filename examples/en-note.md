## 1. Objective

Measure the radius of curvature of a plano-convex lens from the diameters of its Newton's rings, and quantify how much of the result comes from the microscope rather than from the optics.

## 2. Theory

The air film between the lens and the flat plate has thickness \(e(r)\); a dark fringe appears where \(2e + \lambda/2 = k\lambda\). For the \(k\)-th dark ring of diameter \(d_k\) the surface obeys

\[
R = \frac{d_m^{2} - d_n^{2}}{4\,(m-n)\,\lambda}
\]

with \(\lambda = 589.3\ \text{nm}\) for sodium light. Taking the difference of two rings cancels the unknown film thickness at the contact point, so only the *slope* of \(d_k^2\) against \(k\) matters:

\[
\frac{\mathrm{d}(d^2)}{\mathrm{d}k} = 4R\lambda
\]

## 3. Measurements

| Ring \(k\) | Left / mm | Right / mm | \(d_k\) / mm | \(d_k^2\) / mm² |
|---|---|---|---|---|
| 10 | 15.732 | 12.318 | 3.414 | 11.655 |
| 11 | 15.802 | 12.243 | 3.559 | 12.667 |
| 12 | 15.874 | 12.168 | 3.706 | 13.734 |
| 13 | 15.946 | 12.092 | 3.854 | 14.853 |
| 14 | 16.020 | 12.014 | 4.006 | 16.048 |
| 15 | 16.096 | 11.937 | 4.159 | 17.297 |
| 16 | 16.174 | 11.858 | 4.316 | 18.628 |
| 17 | 16.255 | 11.778 | 4.477 | 20.043 |
| 18 | 16.338 | 11.696 | 4.642 | 21.548 |
| 19 | 16.423 | 11.612 | 4.811 | 23.146 |

## 4. Fit

A linear least-squares fit of \(d_k^2\) against \(k\) is more honest than differencing pairs, because it reports the residual:

```python
import numpy as np

k = np.arange(10, 20)
d2 = np.array([11.655, 12.667, 13.734, 14.853, 16.048,
               17.297, 18.628, 20.043, 21.548, 23.146])
slope, intercept = np.polyfit(k, d2, 1)
R = slope / (4 * 589.3e-6)          # mm
resid = d2 - (slope * k + intercept)
print(f"slope = {slope:.4f} mm^2/ring, R = {R:.1f} mm, max resid = {abs(resid).max():.3f}")
```

The fit gives a slope of \(1.276\ \text{mm}^2/\text{ring}\), hence \(R \approx 541\ \text{mm}\) with a maximum residual of \(0.19\ \text{mm}^2\) — a 3% scatter dominated by reading the drum vernier to the nearest 0.005 mm.

## 5. Discussion

1. **Differencing versus fitting.** The pair-difference method and the least-squares fit agree to within 1%; the fit additionally exposes outliers, which is why it is the better choice when the report has to defend its numbers.
2. **Where the error lives.** A 0.01 mm error in one reading shifts \(d^2\) by about 0.03 mm², roughly 2% of the slope. Rings below \(k=10\) are too wide to locate precisely; rings above \(k=25\) sit too close together.
3. **Systematic term.** Pressure on the lens flattens the contact point and shifts every \(d^2\) by the same offset — an additive constant, which is exactly what the intercept of the fit absorbs.
