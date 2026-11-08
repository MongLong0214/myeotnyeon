import { Easing, interpolate } from 'remotion';

export type Vec3 = [number, number, number];
export type SpikeProps = { landscape: boolean };
export const palette = {
  ink: '#05070D', navy: '#0A1433', blue: '#0B3FA0', deepBlue: '#0F2B73',
  red: '#D7264F', pink: '#F6A6B2', yellow: '#F2D45C', white: '#EDEFF3', grey: '#8A93A6',
};
export const recruits: Vec3[] = Array.from({ length: 6 }, (_, i) => [(i - 2.5) * 0.64 + 0.55, 0, -5.4]);
export const commander: Vec3 = [-1.3, 0, 0.6];
const minus = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const unit = (a: Vec3): Vec3 => { const n = Math.hypot(...a); return a.map(v => v / n) as Vec3; };
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];

// Both renderers use the same world, pinhole projection and 2.5 s / 6% dolly.
// Landscape has its own lens and camera position, rather than a portrait crop.
export const cameraAt = (frame: number, landscape: boolean) => {
  const t = interpolate(frame, [0, 74], [0, 1], {
    easing: Easing.bezier(0.33, 0, 0.2, 1), extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const target: Vec3 = landscape ? [0, 1.15, -2] : [0, 1.05, -3];
  const start: Vec3 = landscape ? [1.1, 3.1, 10.6] : [0.15, 2.85, 8.4];
  const position = start.map((v, i) => v + (target[i] - v) * 0.06 * t) as Vec3;
  return { position, target, fov: landscape ? 38 : 48 };
};
export const project = (world: Vec3, frame: number, width: number, height: number) => {
  const c = cameraAt(frame, width > height);
  const forward = unit(minus(c.target, c.position));
  const right = unit(cross(forward, [0, 1, 0]));
  const up = cross(right, forward);
  const v = minus(world, c.position);
  const k = height / (2 * Math.tan(c.fov * Math.PI / 360) * dot(v, forward));
  return { x: width / 2 + dot(v, right) * k, y: height / 2 - dot(v, up) * k, k };
};
