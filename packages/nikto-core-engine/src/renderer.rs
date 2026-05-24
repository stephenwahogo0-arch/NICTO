/// GPU renderer — wgpu-based pipeline for Vulkan/DX12/Metal.
///
/// Runs in its own thread with a winit event loop. Receives commands
/// from Python through a channel. Renders the scene at 60+ FPS.
use cgmath::Matrix4;
use std::sync::mpsc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use wgpu::util::DeviceExt;
use winit::dpi::LogicalSize;
use winit::event::{Event, WindowEvent};
use winit::event_loop::{ControlFlow, EventLoop};
use winit::window::Window;

use crate::scene::{Camera, EntityInstance, Light, MeshData, Scene};

// ── Commands sent from Python to render thread ─────────────────────────

pub enum RenderCommand {
    Start { width: u32, height: u32, title: String },
    Resize { width: u32, height: u32 },
    SetCamera { x: f32, y: f32, z: f32, tx: f32, ty: f32, tz: f32 },
    AddMesh { vertices: Vec<f32>, indices: Vec<u32> },
    SpawnEntity { mesh_idx: usize, x: f32, y: f32, z: f32 },
    UpdateEntityPosition { index: usize, x: f32, y: f32, z: f32 },
    Stop,
}

// ── GPU buffers for a mesh ─────────────────────────────────────────────

struct GpuMesh {
    vertex_buffer: wgpu::Buffer,
    index_buffer: wgpu::Buffer,
    index_count: u32,
}

// ── Uniform buffer data (must match shader layout) ─────────────────────

#[repr(C)]
#[derive(Copy, Clone, Debug, bytemuck::Pod, bytemuck::Zeroable)]
struct ViewUniform {
    view_proj: [[f32; 4]; 4],
}

#[repr(C)]
#[derive(Copy, Clone, Debug, bytemuck::Pod, bytemuck::Zeroable)]
struct EntityUniform {
    model: [[f32; 4]; 4],
    color: [f32; 4],
}

// ── Shaders (WGSL, embedded) ──────────────────────────────────────────

const VERTEX_SHADER: &str = r#"
struct ViewUniform {
    view_proj: mat4x4<f32>,
};
@group(0) @binding(0) var<uniform> view: ViewUniform;

struct EntityUniform {
    model: mat4x4<f32>,
    color: vec4<f32>,
};
@group(1) @binding(0) var<uniform> entity: EntityUniform;

struct VertexInput {
    @location(0) position: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) uv: vec2<f32>,
};

struct VertexOutput {
    @builtin(position) clip_position: vec4<f32>,
    @location(0) world_pos: vec3<f32>,
    @location(1) normal: vec3<f32>,
    @location(2) uv: vec2<f32>,
};

@vertex
fn vs_main(input: VertexInput) -> VertexOutput {
    let world_pos = entity.model * vec4<f32>(input.position, 1.0);
    var out: VertexOutput;
    out.clip_position = view.view_proj * world_pos;
    out.world_pos = world_pos.xyz;
    out.normal = (entity.model * vec4<f32>(input.normal, 0.0)).xyz;
    out.uv = input.uv;
    return out;
}

struct LightData {
    light_pos: vec3<f32>,
    light_color: vec3<f32>,
    intensity: f32,
    ambient: f32,
};
@group(1) @binding(1) var<uniform> light: LightData;

@fragment
fn fs_main(input: VertexOutput) -> @location(0) vec4<f32> {
    let N = normalize(input.normal);
    let L = normalize(light.light_pos - input.world_pos);
    let V = normalize(vec3<f32>(0.0, 0.0, 1.0) - input.world_pos);
    let H = normalize(L + V);

    let diff = max(dot(N, L), 0.0);
    let spec = pow(max(dot(N, H), 0.0), 32.0);

    let ambient = light.ambient * entity.color.rgb;
    let diffuse = diff * entity.color.rgb * light.light_color * light.intensity;
    let specular = spec * vec3<f32>(1.0) * light.intensity * 0.5;

    return vec4<f32>(ambient + diffuse + specular, entity.color.a);
}
"#;

// ── Renderer state (lives on render thread) ────────────────────────────

struct RenderState {
    device: wgpu::Device,
    queue: wgpu::Queue,
    surface: wgpu::Surface<'static>,
    surface_config: wgpu::SurfaceConfiguration,
    pipeline: wgpu::RenderPipeline,
    view_bind_group: wgpu::BindGroup,
    light_bind_group: wgpu::BindGroup,
    view_uniform_buf: wgpu::Buffer,
    light_uniform_buf: wgpu::Buffer,
    meshes: Vec<GpuMesh>,
    entity_uniforms: Vec<wgpu::Buffer>,
    entity_bind_groups: Vec<wgpu::BindGroup>,
    scene: Scene,
    window: Window,
}

impl RenderState {
    async fn new(window: Window, width: u32, height: u32) -> Self {
        let instance = wgpu::Instance::new(&wgpu::InstanceDescriptor::default());
        let surface = instance.create_surface(window.clone()).unwrap();
        let adapter = instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: Some(&surface),
            force_fallback_adapter: false,
        }).await.unwrap();

        let (device, queue) = adapter.request_device(
            &wgpu::DeviceDescriptor { label: None, required_features: wgpu::Features::empty(),
                required_limits: wgpu::Limits::default(), memory_hints: wgpu::MemoryHints::Performance },
            None,
        ).await.unwrap();

        let caps = surface.get_capabilities(&adapter);
        let format = caps.formats[0];
        let surface_config = wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format, width, height,
            present_mode: wgpu::PresentMode::Fifo,
            alpha_mode: caps.alpha_modes[0],
            view_formats: vec![],
            desired_maximum_frame_latency: 2,
        };
        surface.configure(&device, &surface_config);

        // Shader module
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("PBR Shader"),
            source: wgpu::ShaderSource::Wgsl(VERTEX_SHADER.into()),
        });

        // View uniform buffer
        let view_uniform_buf = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("View Uniform"), size: std::mem::size_of::<ViewUniform>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // Light uniform buffer
        let light_uniform_buf = device.create_buffer(&wgpu::BufferDescriptor {
            label: Some("Light Uniform"), size: std::mem::size_of::<[f32; 8]>() as u64,
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
            mapped_at_creation: false,
        });

        // View bind group (group 0)
        let view_bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: None, entries: &[wgpu::BindGroupLayoutEntry {
                binding: 0, visibility: wgpu::ShaderStages::VERTEX,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform,
                    has_dynamic_offset: false, min_binding_size: None,
                }, count: None,
            }],
        });
        let view_bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: None, layout: &view_bind_group_layout,
            entries: &[wgpu::BindGroupEntry {
                binding: 0, resource: view_uniform_buf.as_entity_binding(),
            }],
        });

        let entity_bind_group_layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: None, entries: &[
                wgpu::BindGroupLayoutEntry { binding: 0, visibility: wgpu::ShaderStages::VERTEX,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false, min_binding_size: None, }, count: None,
                },
                wgpu::BindGroupLayoutEntry { binding: 1, visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Buffer { ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false, min_binding_size: None, }, count: None,
                },
            ],
        });

        // Light bind group (shares entity group 1, binding 1)
        let light_bind_group = device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: Some("Light"), layout: &entity_bind_group_layout,
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: wgpu::BindingResource::Buffer(
                    wgpu::BufferBinding { buffer: &device.create_buffer(&wgpu::BufferDescriptor {
                        label: Some("Dummy Entity"), size: 64,
                        usage: wgpu::BufferUsages::UNIFORM, mapped_at_creation: false,
                    }), offset: 0, size: None }) },
                wgpu::BindGroupEntry { binding: 1, resource: light_uniform_buf.as_entity_binding() },
            ],
        });

        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: None, bind_group_layouts: &[&view_bind_group_layout, &entity_bind_group_layout],
            push_constant_ranges: &[],
        });

        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: None, layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState {
                module: &shader, entry_point: "vs_main",
                buffers: &[wgpu::VertexBufferLayout {
                    array_stride: 8 * 4, // 8 f32 per vertex
                    step_mode: wgpu::VertexStepMode::Vertex,
                    attributes: &[
                        wgpu::VertexAttribute { format: wgpu::VertexFormat::Float32x3, offset: 0, shader_location: 0 },
                        wgpu::VertexAttribute { format: wgpu::VertexFormat::Float32x3, offset: 12, shader_location: 1 },
                        wgpu::VertexAttribute { format: wgpu::VertexFormat::Float32x2, offset: 24, shader_location: 2 },
                    ],
                }],
            },
            fragment: Some(wgpu::FragmentState {
                module: &shader, entry_point: "fs_main",
                targets: &[Some(wgpu::ColorTargetState {
                    format, blend: Some(wgpu::BlendState::REPLACE),
                    write_mask: wgpu::ColorWrites::ALL,
                })],
            }),
            primitive: wgpu::PrimitiveState {
                topology: wgpu::PrimitiveTopology::TriangleList,
                cull_mode: Some(wgpu::Face::Back),
                ..Default::default()
            },
            depth_stencil: None,
            multisample: wgpu::MultisampleState::default(),
            multiview: None,
        });

        let scene = Scene::new(width, height);

        Self { device, queue, surface, surface_config, pipeline, view_bind_group, light_bind_group,
            view_uniform_buf, light_uniform_buf, meshes: Vec::new(),
            entity_uniforms: Vec::new(), entity_bind_groups: Vec::new(), scene, window }
    }

    fn add_mesh(&mut self, mesh: MeshData) -> usize {
        let vertex_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: None, contents: bytemuck::cast_slice(&mesh.vertices),
            usage: wgpu::BufferUsages::VERTEX,
        });
        let index_buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: None, contents: bytemuck::cast_slice(&mesh.indices),
            usage: wgpu::BufferUsages::INDEX,
        });
        let idx = self.meshes.len();
        let gpu_idx = self.scene.add_mesh(mesh);
        self.meshes.push(GpuMesh { vertex_buffer: vertex_buf, index_buffer: index_buf, index_count: 36 });
        idx
    }

    fn spawn_entity(&mut self, mesh_idx: usize, x: f32, y: f32, z: f32) {
        let _id = self.scene.spawn_entity(mesh_idx, x, y, z);
        // Create per-entity uniform buffer
        let model = Matrix4::from_translation(cgmath::Vector3::new(x, y, z));
        let uniform = EntityUniform { model: model.into(), color: [1.0, 1.0, 1.0, 1.0] };
        let buf = self.device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
            label: None, contents: bytemuck::bytes_of(&uniform),
            usage: wgpu::BufferUsages::UNIFORM | wgpu::BufferUsages::COPY_DST,
        });
        // Create entity bind group
        let entity_bg = self.device.create_bind_group(&wgpu::BindGroupDescriptor {
            label: None,
            layout: &self.pipeline.get_bind_group_layout(1),
            entries: &[
                wgpu::BindGroupEntry { binding: 0, resource: buf.as_entity_binding() },
                wgpu::BindGroupEntry { binding: 1, resource: self.light_uniform_buf.as_entity_binding() },
            ],
        });
        self.entity_uniforms.push(buf);
        self.entity_bind_groups.push(entity_bg);
    }

    fn update_camera(&mut self) {
        let view: [[f32; 4]; 4] = self.scene.camera.view_proj_matrix().into();
        let uniform = ViewUniform { view_proj: view };
        self.queue.write_buffer(&self.view_uniform_buf, 0, bytemuck::bytes_of(&uniform));
    }

    fn update_light(&mut self) {
        if let Some(light) = self.scene.lights.first() {
            let data: [f32; 8] = [
                light.position[0], light.position[1], light.position[2], 0.0,
                light.color[0], light.color[1], light.color[2], light.intensity,
            ];
            self.queue.write_buffer(&self.light_uniform_buf, 0, bytemuck::cast_slice(&data));
        }
    }

    fn render(&mut self) {
        self.update_camera();
        self.update_light();

        let frame = match self.surface.get_current_texture() {
            Ok(f) => f,
            Err(_) => return,
        };
        let view = frame.texture.create_view(&wgpu::TextureViewDescriptor::default());

        let mut encoder = self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor::default());
        {
            let mut rpass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: None, color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                    view: &view, resolve_target: None, ops: wgpu::Operations {
                        load: wgpu::LoadOp::Clear(wgpu::Color { r: 0.1, g: 0.1, b: 0.15, a: 1.0 }),
                        store: wgpu::StoreOp::Store,
                    },
                })],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
            });
            rpass.set_pipeline(&self.pipeline);
            rpass.set_bind_group(0, &self.view_bind_group, &[]);

            for (i, entity) in self.scene.entities.iter().enumerate() {
                if i >= self.meshes.len() || entity.mesh_index >= self.meshes.len() {
                    continue;
                }
                if i < self.entity_bind_groups.len() {
                    rpass.set_bind_group(1, &self.entity_bind_groups[i], &[]);
                }
                let mesh = &self.meshes[entity.mesh_index];
                rpass.set_vertex_buffer(0, mesh.vertex_buffer.slice(..));
                rpass.set_index_buffer(mesh.index_buffer.slice(..), wgpu::IndexFormat::Uint32);
                rpass.draw_indexed(0..mesh.index_count, 0, 0..1);
            }
        }
        self.queue.submit(Some(encoder.finish()));
        frame.present();
    }
}

// ── Public renderer handle (lives on Python side) ──────────────────────

pub struct RenderEngine {
    cmd_tx: Option<mpsc::Sender<RenderCommand>>,
    running: std::sync::Arc<AtomicBool>,
    render_thread: Option<thread::JoinHandle<()>>,
}

impl RenderEngine {
    pub fn new() -> Self {
        Self { cmd_tx: None, running: std::sync::Arc::new(AtomicBool::new(false)), render_thread: None }
    }

    pub fn start(&mut self, width: u32, height: u32, title: &str) {
        if self.running.load(Ordering::SeqCst) { return; }
        self.running.store(true, Ordering::SeqCst);
        let running = self.running.clone();
        let (tx, rx) = mpsc::channel::<RenderCommand>();
        self.cmd_tx = Some(tx);
        let title_owned = title.to_string();

        self.render_thread = Some(thread::spawn(move || {
            let event_loop = EventLoop::new().unwrap();
            let window = winit::window::WindowBuilder::new()
                .with_title(&title_owned)
                .with_inner_size(LogicalSize::new(width as f64, height as f64))
                .build(&event_loop).unwrap();

            let mut state = pollster::block_on(RenderState::new(window, width, height));

            event_loop.run(move |event, elwt| {
                elwt.set_control_flow(ControlFlow::Poll);

                match event {
                    Event::WindowEvent { event: WindowEvent::CloseRequested, .. } => {
                        running.store(false, Ordering::SeqCst);
                        elwt.exit();
                    }
                    Event::WindowEvent { event: WindowEvent::Resized(size), .. } => {
                        state.surface_config.width = size.width;
                        state.surface_config.height = size.height;
                        state.surface.configure(&state.device, &state.surface_config);
                        state.scene.resize(size.width, size.height);
                    }
                    Event::AboutToWait => {
                        // Process commands from Python
                        while let Ok(cmd) = rx.try_recv() {
                            match cmd {
                                RenderCommand::SetCamera { x, y, z, tx, ty, tz } => {
                                    state.scene.set_camera(x, y, z, tx, ty, tz);
                                }
                                RenderCommand::AddMesh { vertices, indices } => {
                                    let mesh = MeshData { vertices, indices, vertex_count: 0, index_count: 0 };
                                    state.add_mesh(mesh);
                                }
                                RenderCommand::SpawnEntity { mesh_idx, x, y, z } => {
                                    state.spawn_entity(mesh_idx, x, y, z);
                                }
                                RenderCommand::Stop | RenderCommand::Start { .. } => {}
                                RenderCommand::Resize { width, height } => {
                                    state.surface_config.width = width;
                                    state.surface_config.height = height;
                                    state.surface.configure(&state.device, &state.surface_config);
                                }
                                RenderCommand::UpdateEntityPosition { index, x, y, z } => {
                                    if index < state.scene.entities.len() {
                                        let ent = &mut state.scene.entities[index];
                                        ent.position = [x, y, z];
                                        // Update uniform
                                        let model = Matrix4::from_translation(cgmath::Vector3::new(x, y, z));
                                        let uniform = EntityUniform { model: model.into(), color: [1.0, 1.0, 1.0, 1.0] };
                                        if index < state.entity_uniforms.len() {
                                            state.queue.write_buffer(&state.entity_uniforms[index], 0, bytemuck::bytes_of(&uniform));
                                        }
                                    }
                                }
                            }
                        }
                        state.render();
                        self::std::thread::yield_now();
                    }
                    _ => {}
                }
            }).unwrap();
        }));
    }

    pub fn send(&self, cmd: RenderCommand) {
        if let Some(ref tx) = self.cmd_tx {
            let _ = tx.send(cmd);
        }
    }

    pub fn stop(&mut self) {
        self.send(RenderCommand::Stop);
        self.running.store(false, Ordering::SeqCst);
        if let Some(handle) = self.render_thread.take() {
            let _ = handle.join();
        }
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::SeqCst)
    }
}

impl Drop for RenderEngine {
    fn drop(&mut self) {
        self.stop();
    }
}
