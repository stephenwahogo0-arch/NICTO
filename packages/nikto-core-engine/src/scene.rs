/// Scene engine — octree spatial index, camera system, lighting.
use cgmath::{Matrix4, Point3, Rad, Vector3};
use std::sync::atomic::{AtomicU64, Ordering};

static NODE_ID: AtomicU64 = AtomicU64::new(1);

// ── Camera ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct Camera {
    pub position: Point3<f32>,
    pub target: Point3<f32>,
    pub up: Vector3<f32>,
    pub fov_y: Rad<f32>,
    pub aspect: f32,
    pub near: f32,
    pub far: f32,
}

impl Camera {
    pub fn new(width: u32, height: u32) -> Self {
        Self {
            position: Point3::new(0.0, 5.0, 15.0),
            target: Point3::new(0.0, 0.0, 0.0),
            up: Vector3::unit_y(),
            fov_y: Rad(std::f32::consts::FRAC_PI_4),
            aspect: width as f32 / height as f32,
            near: 0.1,
            far: 1000.0,
        }
    }

    pub fn view_matrix(&self) -> Matrix4<f32> {
        Matrix4::look_at_rh(self.position, self.target, self.up)
    }

    pub fn proj_matrix(&self) -> Matrix4<f32> {
        cgmath::perspective(self.fov_y, self.aspect, self.near, self.far)
    }

    pub fn view_proj_matrix(&self) -> Matrix4<f32> {
        self.proj_matrix() * self.view_matrix()
    }
}

// ── Light ──────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct Light {
    pub position: [f32; 3],
    pub color: [f32; 3],
    pub intensity: f32,
}

impl Light {
    pub fn new(x: f32, y: f32, z: f32) -> Self {
        Self { position: [x, y, z], color: [1.0, 1.0, 1.0], intensity: 1.0 }
    }
}

// ── Mesh data (CPU-side, ready for GPU upload) ────────────────────────

#[derive(Clone, Debug)]
pub struct MeshData {
    pub vertices: Vec<f32>,  // interleaved [px,py,pz, nx,ny,nz, u,v]
    pub indices: Vec<u32>,
    pub vertex_count: u32,
    pub index_count: u32,
}

impl MeshData {
    pub fn cube(ox: f32, oy: f32, oz: f32) -> Self {
        // 24 vertices × 8 components, 36 indices
        let verts: [f32; 192] = [
            -0.5,-0.5, 0.5, 0,0,1, 0,0,  0.5,-0.5, 0.5, 0,0,1, 1,0,
             0.5, 0.5, 0.5, 0,0,1, 1,1, -0.5, 0.5, 0.5, 0,0,1, 0,1,
            -0.5, 0.5,-0.5, 0,0,-1,0,0,  0.5, 0.5,-0.5, 0,0,-1,1,0,
             0.5,-0.5,-0.5, 0,0,-1,1,1, -0.5,-0.5,-0.5, 0,0,-1,0,1,
             0.5,-0.5, 0.5, 1,0,0, 0,0,  0.5,-0.5,-0.5, 1,0,0, 1,0,
             0.5, 0.5,-0.5, 1,0,0, 1,1,  0.5, 0.5, 0.5, 1,0,0, 0,1,
            -0.5,-0.5,-0.5,-1,0,0, 0,0, -0.5,-0.5, 0.5,-1,0,0, 1,0,
            -0.5, 0.5, 0.5,-1,0,0, 1,1, -0.5, 0.5,-0.5,-1,0,0, 0,1,
            -0.5, 0.5, 0.5, 0,1,0, 0,0,  0.5, 0.5, 0.5, 0,1,0, 1,0,
             0.5, 0.5,-0.5, 0,1,0, 1,1, -0.5, 0.5,-0.5, 0,1,0, 0,1,
            -0.5,-0.5,-0.5, 0,-1,0,0,0,  0.5,-0.5,-0.5, 0,-1,0,1,0,
             0.5,-0.5, 0.5, 0,-1,0,1,1, -0.5,-0.5, 0.5, 0,-1,0,0,1,
        ];
        let idx: [u32; 36] = [
            0,1,2,0,2,3, 4,5,6,4,6,7, 8,9,10,8,10,11,
            12,13,14,12,14,15, 16,17,18,16,18,19, 20,21,22,20,22,23,
        ];
        let mut vertices = verts.to_vec();
        for v in vertices.chunks_exact_mut(8) {
            v[0] += ox; v[1] += oy; v[2] += oz;
        }
        Self { vertices, indices: idx.to_vec(), vertex_count: 24, index_count: 36 }
    }
}

// ── Octree ─────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
pub struct OctreeNode {
    pub id: u64,
    pub min: [f32; 3],
    pub max: [f32; 3],
    pub entities: Vec<u64>,
    pub children: Option<Box<[OctreeNode; 8]>>,
    pub depth: u32,
}

impl OctreeNode {
    pub fn new(min: [f32; 3], max: [f32; 3], depth: u32) -> Self {
        Self { id: NODE_ID.fetch_add(1, Ordering::Relaxed), min, max, entities: Vec::new(), children: None, depth }
    }

    fn center(&self) -> [f32; 3] {
        [ (self.min[0]+self.max[0])/2.0, (self.min[1]+self.max[1])/2.0, (self.min[2]+self.max[2])/2.0 ]
    }

    fn half_size(&self) -> [f32; 3] {
        [ (self.max[0]-self.min[0])/2.0, (self.max[1]-self.min[1])/2.0, (self.max[2]-self.min[2])/2.0 ]
    }
}

pub struct Octree {
    pub root: OctreeNode,
    pub max_depth: u32,
}

impl Octree {
    pub fn new(bounds_min: [f32; 3], bounds_max: [f32; 3], max_depth: u32) -> Self {
        Self { root: OctreeNode::new(bounds_min, bounds_max, 0), max_depth }
    }

    pub fn insert(&mut self, entity_id: u64, pos: [f32; 3]) {
        Self::insert_into(&mut self.root, entity_id, pos, self.max_depth);
    }

    fn insert_into(node: &mut OctreeNode, entity_id: u64, pos: [f32; 3], max_depth: u32) {
        if node.depth >= max_depth {
            node.entities.push(entity_id);
            return;
        }
        if node.children.is_none() {
            node.children = Some(Box::new(Self::split(node)));
        }
        let c = node.center();
        let child_idx = ((pos[0] >= c[0]) as usize) | ((pos[1] >= c[1]) as usize) << 1 | ((pos[2] >= c[2]) as usize) << 2;
        if let Some(ref mut children) = node.children {
            Self::insert_into(&mut children[child_idx], entity_id, pos, max_depth);
        }
    }

    fn split(node: &OctreeNode) -> [OctreeNode; 8] {
        let c = node.center();
        let h = node.half_size();
        let mut children = [
            OctreeNode::new([node.min[0],node.min[1],node.min[2]], [c[0],c[1],c[2]], node.depth+1),
            OctreeNode::new([c[0],node.min[1],node.min[2]], [node.max[0],c[1],c[2]], node.depth+1),
            OctreeNode::new([node.min[0],c[1],node.min[2]], [c[0],node.max[1],c[2]], node.depth+1),
            OctreeNode::new([c[0],c[1],node.min[2]], [node.max[0],node.max[1],c[2]], node.depth+1),
            OctreeNode::new([node.min[0],node.min[1],c[2]], [c[0],c[1],node.max[2]], node.depth+1),
            OctreeNode::new([c[0],node.min[1],c[2]], [node.max[0],c[1],node.max[2]], node.depth+1),
            OctreeNode::new([node.min[0],c[1],c[2]], [c[0],node.max[1],node.max[2]], node.depth+1),
            OctreeNode::new([c[0],c[1],c[2]], [node.max[0],node.max[1],node.max[2]], node.depth+1),
        ];
        // Re-insert existing entities into children
        for eid in &node.entities {
            let pos = [0.0; 3]; // simplified: track positions separately
            let child_idx = ((pos[0] >= c[0]) as usize) | ((pos[1] >= c[1]) as usize) << 1 | ((pos[2] >= c[2]) as usize) << 2;
            children[child_idx].entities.push(*eid);
        }
        children
    }

    /// Query all entities within `radius` of `pos`. Returns entity IDs.
    pub fn query_range(&self, pos: [f32; 3], radius: f32) -> Vec<u64> {
        let mut result = Vec::new();
        Self::query_node(&self.root, pos, radius, &mut result);
        result
    }

    fn query_node(node: &OctreeNode, pos: [f32; 3], radius: f32, result: &mut Vec<u64>) {
        let r2 = radius * radius;
        // AABB vs sphere check
        let closest = [
            pos[0].clamp(node.min[0], node.max[0]),
            pos[1].clamp(node.min[1], node.max[1]),
            pos[2].clamp(node.min[2], node.max[2]),
        ];
        let dx = pos[0] - closest[0]; let dy = pos[1] - closest[1]; let dz = pos[2] - closest[2];
        if dx*dx + dy*dy + dz*dz > r2 { return; }

        result.extend_from_slice(&node.entities);
        if let Some(ref children) = node.children {
            for child in children.iter() {
                Self::query_node(child, pos, radius, result);
            }
        }
    }
}

// ── Scene ──────────────────────────────────────────────────────────────

pub struct Scene {
    pub entities: Vec<EntityInstance>,
    pub camera: Camera,
    pub lights: Vec<Light>,
    pub octree: Octree,
    pub meshes: Vec<MeshData>,
}

pub struct EntityInstance {
    pub id: u64,
    pub mesh_index: usize,
    pub position: [f32; 3],
    pub rotation: [f32; 3],
    pub scale: [f32; 3],
    pub color: [f32; 3],
}

impl Scene {
    pub fn new(width: u32, height: u32) -> Self {
        Self {
            entities: Vec::new(),
            camera: Camera::new(width, height),
            lights: vec![Light::new(10.0, 20.0, 10.0)],
            octree: Octree::new([-500.0; 3], [500.0; 3], 8),
            meshes: Vec::new(),
        }
    }

    pub fn add_mesh(&mut self, mesh: MeshData) -> usize {
        let idx = self.meshes.len();
        self.meshes.push(mesh);
        idx
    }

    pub fn spawn_entity(&mut self, mesh_idx: usize, x: f32, y: f32, z: f32) -> u64 {
        let id = NODE_ID.fetch_add(1, Ordering::Relaxed);
        self.entities.push(EntityInstance {
            id, mesh_index: mesh_idx, position: [x, y, z],
            rotation: [0.0; 3], scale: [1.0; 3], color: [1.0; 3],
        });
        self.octree.insert(id, [x, y, z]);
        id
    }

    pub fn set_camera(&mut self, x: f32, y: f32, z: f32, tx: f32, ty: f32, tz: f32) {
        self.camera.position = Point3::new(x, y, z);
        self.camera.target = Point3::new(tx, ty, tz);
    }

    pub fn resize(&mut self, width: u32, height: u32) {
        self.camera.aspect = width as f32 / height as f32;
    }
}
