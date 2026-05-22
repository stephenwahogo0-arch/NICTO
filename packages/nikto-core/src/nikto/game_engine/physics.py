"""NIKTO Advanced Physics — rigid body, soft body, joints, destruction."""

import math
import random
from typing import Optional


class Vec2:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, s):
        return Vec2(self.x * s, self.y * s)

    def __truediv__(self, s):
        return Vec2(self.x / s, self.y / s)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def cross(self, other):
        return self.x * other.y - self.y * other.x

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        l = self.length()
        if l > 0:
            return Vec2(self.x / l, self.y / l)
        return Vec2()

    def rotate(self, angle):
        c, s = math.cos(angle), math.sin(angle)
        return Vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def to_tuple(self):
        return (self.x, self.y)


class RigidBody:
    def __init__(self, mass=1.0, position=Vec2(), velocity=Vec2()):
        self.position = position
        self.velocity = velocity
        self.force = Vec2()
        self.mass = max(0.001, mass)
        self.inv_mass = 1.0 / self.mass
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.torque = 0.0
        self.inertia = mass
        self.inv_inertia = 1.0 / self.inertia
        self.restitution = 0.3
        self.friction = 0.5
        self.damping = 0.99
        self.angular_damping = 0.98
        self.fixed_rotation = False
        self.is_static = False
        self.shape = "circle"
        self.radius = 16.0
        self.width = 32.0
        self.height = 32.0
        self.vertices = []
        self.aabb = None
        self.collision_layer = 1
        self.collision_mask = 1
        self.sleeping = False
        self.sleep_timer = 0.0
        self.sleep_threshold = 0.01
        self.user_data = None

    def get_transform(self):
        return self.position, self.angle

    def apply_force(self, fx, fy):
        self.force.x += fx
        self.force.y += fy

    def apply_force_at_point(self, fx, fy, px, py):
        self.force.x += fx
        self.force.y += fy
        self.torque += (px - self.position.x) * fy - (py - self.position.y) * fx

    def apply_impulse(self, ix, iy):
        self.velocity.x += ix * self.inv_mass
        self.velocity.y += iy * self.inv_mass

    def apply_angular_impulse(self, impulse):
        if not self.fixed_rotation:
            self.angular_velocity += impulse * self.inv_inertia

    def integrate(self, dt):
        if self.is_static or self.sleeping:
            return
        accel_x = self.force.x * self.inv_mass
        accel_y = self.force.y * self.inv_mass
        self.velocity.x += accel_x * dt
        self.velocity.y += accel_y * dt
        self.velocity.x *= self.damping
        self.velocity.y *= self.damping
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
        if not self.fixed_rotation:
            self.angular_velocity += self.torque * self.inv_inertia * dt
            self.angular_velocity *= self.angular_damping
            self.angle += self.angular_velocity * dt
        self.force = Vec2()
        self.torque = 0.0

    def check_sleep(self, dt):
        speed = self.velocity.length()
        if speed < self.sleep_threshold:
            self.sleep_timer += dt
            if self.sleep_timer > 0.5:
                self.sleeping = True
        else:
            self.sleep_timer = 0.0
            self.sleeping = False

    def get_aabb(self):
        if self.shape == "circle":
            return (
                self.position.x - self.radius,
                self.position.y - self.radius,
                self.position.x + self.radius,
                self.position.y + self.radius,
            )
        hw, hh = self.width / 2, self.height / 2
        return (
            self.position.x - hw,
            self.position.y - hh,
            self.position.x + hw,
            self.position.y + hh,
        )


class Joint:
    def __init__(self, body_a, body_b, anchor=Vec2()):
        self.body_a = body_a
        self.body_b = body_b
        self.anchor = anchor
        self.broken = False

    def solve(self):
        pass


class DistanceJoint(Joint):
    def __init__(self, body_a, body_b, anchor_a=Vec2(), anchor_b=Vec2(), distance=None):
        super().__init__(body_a, body_b)
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b
        if distance is None:
            dx = (body_a.position.x + anchor_a.x) - (body_b.position.x + anchor_b.x)
            dy = (body_a.position.y + anchor_a.y) - (body_b.position.y + anchor_b.y)
            self.distance = math.sqrt(dx*dx + dy*dy)
        else:
            self.distance = distance
        self.stiffness = 0.5
        self.damping = 0.1
        self.break_force = float("inf")

    def solve(self):
        if self.broken:
            return
        wa = Vec2(self.anchor_a.x, self.anchor_a.y).rotate(self.body_a.angle)
        wb = Vec2(self.anchor_b.x, self.anchor_b.y).rotate(self.body_b.angle)
        p1 = self.body_a.position + wa
        p2 = self.body_b.position + wb
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.001:
            return
        nx, ny = dx/dist, dy/dist
        delta = dist - self.distance
        force_mag = delta * self.stiffness
        rvx = self.body_b.velocity.x - self.body_a.velocity.x
        rvy = self.body_b.velocity.y - self.body_a.velocity.y
        rel_v = rvx * nx + rvy * ny
        force_mag += rel_v * self.damping
        if abs(force_mag) > self.break_force:
            self.broken = True
            return
        fx, fy = nx * force_mag, ny * force_mag
        self.body_a.apply_force(fx, fy)
        self.body_b.apply_force(-fx, -fy)


class SpringJoint(DistanceJoint):
    def __init__(self, body_a, body_b, rest_length=100.0, stiffness=0.1, damping=0.05):
        super().__init__(body_a, body_b)
        self.distance = rest_length
        self.stiffness = stiffness
        self.damping = damping


class HingeJoint(Joint):
    def __init__(self, body_a, body_b, pivot=Vec2(), min_angle=-math.pi/4, max_angle=math.pi/4):
        super().__init__(body_a, body_b, pivot)
        self.min_angle = min_angle
        self.max_angle = max_angle

    def solve(self):
        if self.broken:
            return
        rel_angle = self.body_b.angle - self.body_a.angle
        if rel_angle < self.min_angle:
            correction = self.min_angle - rel_angle
            self.body_a.angular_velocity -= correction * 0.1
            self.body_b.angular_velocity += correction * 0.1
        elif rel_angle > self.max_angle:
            correction = self.max_angle - rel_angle
            self.body_a.angular_velocity -= correction * 0.1
            self.body_b.angular_velocity += correction * 0.1


class PhysicsMaterial:
    def __init__(self, density=1.0, friction=0.5, restitution=0.3, name="default"):
        self.density = density
        self.friction = friction
        self.restitution = restitution
        self.name = name

    @classmethod
    def wood(cls):
        return cls(0.7, 0.6, 0.2, "wood")

    @classmethod
    def metal(cls):
        return cls(8.0, 0.3, 0.6, "metal")

    @classmethod
    def rubber(cls):
        return cls(1.2, 0.9, 0.9, "rubber")

    @classmethod
    def glass(cls):
        return cls(2.5, 0.2, 0.1, "glass")

    @classmethod
    def ice(cls):
        return cls(0.9, 0.05, 0.95, "ice")


class SoftBody:
    def __init__(self, x=0, y=0, width=100, height=100, segments=5):
        self.particles = []
        self.springs = []
        self.material = PhysicsMaterial()
        seg = segments
        spacing_x = width / seg
        spacing_y = height / seg
        for row in range(seg + 1):
            for col in range(seg + 1):
                px = x + col * spacing_x
                py = y + row * spacing_y
                body = RigidBody(mass=0.1, position=Vec2(px, py))
                body.damping = 0.95
                body.radius = 2
                body.shape = "circle"
                self.particles.append(body)
        for row in range(seg + 1):
            for col in range(seg + 1):
                idx = row * (seg + 1) + col
                if col < seg:
                    right = idx + 1
                    s = SpringJoint(self.particles[idx], self.particles[right], spacing_x, 0.8, 0.1)
                    self.springs.append(s)
                if row < seg:
                    down = idx + (seg + 1)
                    s = SpringJoint(self.particles[idx], self.particles[down], spacing_y, 0.8, 0.1)
                    self.springs.append(s)
                if col < seg and row < seg:
                    diag = idx + (seg + 1) + 1
                    d = math.sqrt(spacing_x**2 + spacing_y**2)
                    s = SpringJoint(self.particles[idx], self.particles[diag], d, 0.3, 0.05)
                    self.springs.append(s)
        if seg >= 2:
            top_left = self.particles[0]
            top_right = self.particles[seg]
            top_left.is_static = True
            top_right.is_static = True

    def update(self, dt, gravity=200.0):
        for p in self.particles:
            p.apply_force(0, gravity * p.mass)
            p.integrate(dt)
        for _ in range(3):
            for s in self.springs:
                s.solve()
            for s in self.springs:
                if s.broken:
                    self.springs.remove(s)

    def get_surface(self):
        return [(p.position.x, p.position.y) for p in self.particles]


class DestructionSystem:
    def __init__(self):
        self.fragments = []
        self.vulnerable_bodies = {}

    def register_vulnerable(self, body, hp=100, fragment_count=4):
        self.vulnerable_bodies[id(body)] = {
            "body": body,
            "hp": hp,
            "max_hp": hp,
            "fragment_count": fragment_count,
            "broken": False,
        }

    def damage(self, body, amount, impact_point=None):
        entry = self.vulnerable_bodies.get(id(body))
        if not entry or entry["broken"]:
            return []
        entry["hp"] -= amount
        if entry["hp"] <= 0:
            return self._break(body, impact_point)
        return []

    def _break(self, body, impact_point=None):
        entry = self.vulnerable_bodies.get(id(body))
        if not entry:
            return []
        entry["broken"] = True
        fragments = []
        pos = body.position
        for _ in range(entry["fragment_count"]):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(5, 20)
            fb = RigidBody(
                mass=body.mass / entry["fragment_count"],
                position=Vec2(pos.x + math.cos(angle) * dist, pos.y + math.sin(angle) * dist),
                velocity=Vec2(random.uniform(-100, 100), random.uniform(-100, 100)),
            )
            fb.radius = random.uniform(3, 8)
            fb.shape = "circle"
            fb.restitution = body.restitution
            fb.friction = body.friction
            fb.user_data = {"fragment": True, "alpha": 255}
            fragments.append(fb)
        self.fragments.extend(fragments)
        return fragments

    def update(self, dt):
        self.fragments = [f for f in self.fragments if hasattr(f, "user_data")]
        for f in self.fragments:
            if f.user_data and "alpha" in f.user_data:
                f.user_data["alpha"] -= dt * 200
                if f.user_data["alpha"] <= 0:
                    f.user_data["alpha"] = 0


class PhysicsWorld:
    def __init__(self, gravity=200.0, bounds=(0, 0, 800, 600)):
        self.gravity = gravity
        self.bounds = bounds
        self.bodies = []
        self.joints = []
        self.soft_bodies = []
        self.destruction = DestructionSystem()
        self.constraint_iterations = 5
        self.gravity_wells = []
        self.wind = Vec2()

    def add_body(self, body):
        self.bodies.append(body)
        return body

    def remove_body(self, body):
        if body in self.bodies:
            self.bodies.remove(body)

    def add_joint(self, joint):
        self.joints.append(joint)
        return joint

    def add_soft_body(self, soft_body):
        self.soft_bodies.append(soft_body)
        for p in soft_body.particles:
            self.bodies.append(p)
        return soft_body

    def add_gravity_well(self, x, y, strength=500.0, radius=200.0):
        self.gravity_wells.append({"x": x, "y": y, "strength": strength, "radius": radius})

    def remove_gravity_well(self, index):
        if 0 <= index < len(self.gravity_wells):
            self.gravity_wells.pop(index)

    def raycast(self, x1, y1, x2, y2, layer_mask=1):
        hits = []
        dx, dy = x2 - x1, y2 - y1
        dist = math.sqrt(dx*dx + dy*dy)
        if dist == 0:
            return hits
        nx, ny = dx/dist, dy/dist
        for body in self.bodies:
            if not (body.collision_layer & layer_mask):
                continue
            if body.is_static:
                continue
            bx, by = body.position.x, body.position.y
            to_body_x, to_body_y = bx - x1, by - y1
            t = to_body_x * nx + to_body_y * ny
            if t < 0 or t > dist:
                continue
            closest_x = x1 + nx * t
            closest_y = y1 + ny * t
            cdx, cdy = bx - closest_x, by - closest_y
            cdist = math.sqrt(cdx*cdx + cdy*cdy)
            if cdist <= body.radius:
                hits.append((body, t / dist, Vec2(closest_x, closest_y)))
        hits.sort(key=lambda h: h[1])
        return hits

    def step(self, dt):
        sub_steps = 4
        sub_dt = dt / sub_steps
        for _ in range(sub_steps):
            self._sub_step(sub_dt)

    def _sub_step(self, dt):
        for body in self.bodies:
            if body.is_static:
                continue
            body.apply_force(0, self.gravity * body.mass)
            body.apply_force(self.wind.x, self.wind.y)
            for well in self.gravity_wells:
                dx = well["x"] - body.position.x
                dy = well["y"] - body.position.y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < well["radius"] and dist > 0:
                    strength = well["strength"] * (1 - dist / well["radius"])
                    body.apply_force(dx/dist * strength, dy/dist * strength)
            body.integrate(dt)
        self._solve_collisions(dt)
        self._solve_constraints()
        for body in self.bodies:
            body.check_sleep(dt)
            self._enforce_bounds(body)
        self.joints = [j for j in self.joints if not j.broken]
        for j in self.joints:
            j.solve()
        for sb in self.soft_bodies:
            sb.particles = [p for p in sb.particles if p.position.y < 2000]
        self.destruction.update(dt)

    def _solve_collisions(self, dt):
        for i in range(len(self.bodies)):
            for j in range(i + 1, len(self.bodies)):
                a, b = self.bodies[i], self.bodies[j]
                if a.is_static and b.is_static:
                    continue
                if not (a.collision_layer & b.collision_mask or b.collision_layer & a.collision_mask):
                    continue
                if self._check_collision(a, b):
                    self._resolve_collision(a, b, dt)

    def _check_collision(self, a, b):
        if a.shape == "circle" and b.shape == "circle":
            dx = b.position.x - a.position.x
            dy = b.position.y - a.position.y
            dist = math.sqrt(dx*dx + dy*dy)
            return dist < a.radius + b.radius
        if a.shape == "circle" and b.shape != "circle":
            return self._circle_vs_poly(a, b)
        if a.shape != "circle" and b.shape == "circle":
            return self._circle_vs_poly(b, a)
        return self._poly_vs_poly(a, b)

    def _circle_vs_poly(self, circle, poly):
        cx, cy = circle.position.x, circle.position.y
        verts = poly.vertices
        if not verts:
            return False
        for v in verts:
            dx = cx - v.x
            dy = cy - v.y
            if math.sqrt(dx*dx + dy*dy) < circle.radius:
                return True
        return False

    def _poly_vs_poly(self, a, b):
        if not a.vertices or not b.vertices:
            return False
        for va in a.vertices:
            for vb in b.vertices:
                dx = va.x - vb.x
                dy = va.y - vb.y
                if math.sqrt(dx*dx + dy*dy) < 5:
                    return True
        return False

    def _resolve_collision(self, a, b, dt):
        dx = b.position.x - a.position.x
        dy = b.position.y - a.position.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.001:
            dx, dy = 0.001, 0
            dist = 0.001
        nx, ny = dx/dist, dy/dist
        if a.shape == "circle" and b.shape == "circle":
            overlap = a.radius + b.radius - dist
        else:
            overlap = 2.0
        if overlap > 0:
            total_mass = a.mass + b.mass
            if not a.is_static:
                a.position.x -= nx * overlap * (a.mass / total_mass) * 0.5
                a.position.y -= ny * overlap * (a.mass / total_mass) * 0.5
            if not b.is_static:
                b.position.x += nx * overlap * (b.mass / total_mass) * 0.5
                b.position.y += ny * overlap * (b.mass / total_mass) * 0.5
            rvx = b.velocity.x - a.velocity.x
            rvy = b.velocity.y - a.velocity.y
            rel_v = rvx * nx + rvy * ny
            if rel_v > 0:
                restitution = min(a.restitution, b.restitution)
                j = -(1 + restitution) * rel_v
                j /= a.inv_mass + b.inv_mass
                a.velocity.x -= j * nx * a.inv_mass
                a.velocity.y -= j * ny * a.inv_mass
                b.velocity.x += j * nx * b.inv_mass
                b.velocity.y += j * ny * b.inv_mass
                friction = math.sqrt(a.friction * b.friction)
                tx, ty = -ny, nx
                rt = rvx * tx + rvy * ty
                jt = -rt / (a.inv_mass + b.inv_mass)
                if abs(jt) > friction * abs(j):
                    jt = math.copysign(friction * abs(j), jt)
                a.velocity.x -= jt * tx * a.inv_mass
                a.velocity.y -= jt * ty * a.inv_mass
                b.velocity.x += jt * tx * b.inv_mass
                b.velocity.y += jt * ty * b.inv_mass

    def _solve_constraints(self):
        for _ in range(self.constraint_iterations):
            for body in self.bodies:
                if body.is_static:
                    continue

    def _enforce_bounds(self, body):
        min_x, min_y, max_x, max_y = self.bounds
        r = body.radius if body.shape == "circle" else max(body.width, body.height) / 2
        if body.position.x - r < min_x:
            body.position.x = min_x + r
            body.velocity.x = -body.velocity.x * body.restitution
        if body.position.x + r > max_x:
            body.position.x = max_x - r
            body.velocity.x = -body.velocity.x * body.restitution
        if body.position.y - r < min_y:
            body.position.y = min_y + r
            body.velocity.y = -body.velocity.y * body.restitution
        if body.position.y + r > max_y:
            body.position.y = max_y - r
            body.velocity.y = -body.velocity.y * body.restitution

    def query_aabb(self, x1, y1, x2, y2, layer_mask=1):
        results = []
        for body in self.bodies:
            if not (body.collision_layer & layer_mask):
                continue
            baabb = body.get_aabb()
            if baabb[0] < x2 and baabb[2] > x1 and baabb[1] < y2 and baabb[3] > y1:
                results.append(body)
        return results
