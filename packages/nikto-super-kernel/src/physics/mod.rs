use pyo3::prelude::*;

/// Sector 1 extension: lightweight physics for game engine (rigid body, collision, gravity).
#[pyclass]
pub struct PhysicsEngine {
    pub(crate) bodies: Vec<RigidBody>,
    gravity: f64,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct RigidBody {
    #[pyo3(get, set)]
    pub x: f64,
    #[pyo3(get, set)]
    pub y: f64,
    #[pyo3(get, set)]
    pub z: f64,
    #[pyo3(get, set)]
    pub vx: f64,
    #[pyo3(get, set)]
    pub vy: f64,
    #[pyo3(get, set)]
    pub vz: f64,
    #[pyo3(get, set)]
    pub mass: f64,
    #[pyo3(get, set)]
    pub radius: f64,
}

impl PhysicsEngine {
    pub fn new(gravity: f64) -> Self {
        Self { bodies: Vec::new(), gravity }
    }

    fn compute_gravity(&self, idx: usize) -> (f64, f64, f64) {
        let mut ax = 0.0; let mut ay = 0.0; let mut az = 0.0;
        for (j, other) in self.bodies.iter().enumerate() {
            if j == idx { continue; }
            let dx = other.x - self.bodies[idx].x;
            let dy = other.y - self.bodies[idx].y;
            let dz = other.z - self.bodies[idx].z;
            let dist_sq = dx * dx + dy * dy + dz * dz + 1e-8;
            let dist = dist_sq.sqrt();
            let force = self.gravity * other.mass / dist_sq;
            ax += force * dx / dist;
            ay += force * dy / dist;
            az += force * dz / dist;
        }
        (ax, ay, az)
    }

    pub fn resolve_collision(a: &mut RigidBody, b: &mut RigidBody) {
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let dz = b.z - a.z;
        let dist_sq = dx * dx + dy * dy + dz * dz;
        let min_dist = a.radius + b.radius;
        if dist_sq < min_dist * min_dist && dist_sq > 1e-12 {
            let dist = dist_sq.sqrt();
            let overlap = min_dist - dist;
            let nx = dx / dist;
            let ny = dy / dist;
            let nz = dz / dist;
            let total_mass = a.mass + b.mass;
            a.x -= nx * overlap * (b.mass / total_mass);
            a.y -= ny * overlap * (b.mass / total_mass);
            a.z -= nz * overlap * (b.mass / total_mass);
            b.x += nx * overlap * (a.mass / total_mass);
            b.y += ny * overlap * (a.mass / total_mass);
            b.z += nz * overlap * (a.mass / total_mass);
            let dvx = b.vx - a.vx;
            let dvy = b.vy - a.vy;
            let dvz = b.vz - a.vz;
            let rel_v = dvx * nx + dvy * ny + dvz * nz;
            if rel_v < 0.0 {
                let impulse = 2.0 * rel_v / total_mass;
                a.vx += impulse * b.mass * nx;
                a.vy += impulse * b.mass * ny;
                a.vz += impulse * b.mass * nz;
                b.vx -= impulse * a.mass * nx;
                b.vy -= impulse * a.mass * ny;
                b.vz -= impulse * a.mass * nz;
            }
        }
    }
}

#[pymethods]
impl PhysicsEngine {
    #[new]
    pub fn new_py(gravity: f64) -> Self {
        Self::new(gravity)
    }

    pub fn add_body(&mut self, x: f64, y: f64, z: f64, mass: f64, radius: f64) {
        self.bodies.push(RigidBody { x, y, z, vx: 0.0, vy: 0.0, vz: 0.0, mass, radius });
    }

    pub fn step(&mut self, dt: f64) {
        for i in 0..self.bodies.len() {
            let (ax, ay, az) = self.compute_gravity(i);
            self.bodies[i].vx += ax * dt;
            self.bodies[i].vy += ay * dt;
            self.bodies[i].vz += az * dt;
            self.bodies[i].x += self.bodies[i].vx * dt;
            self.bodies[i].y += self.bodies[i].vy * dt;
            self.bodies[i].z += self.bodies[i].vz * dt;
        }
        for i in 0..self.bodies.len() {
            let (left, right) = self.bodies.split_at_mut(i + 1);
            for body_j in right.iter_mut() {
                let body_i = &mut left[i];
                Self::resolve_collision(body_i, body_j);
            }
        }
    }

    pub fn body_count(&self) -> usize { self.bodies.len() }
}
