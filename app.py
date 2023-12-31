import gradio as gr
import base64
from PIL import ImageColor
from pathlib import Path
import bpy
from tqdm import tqdm
from math import pi
import tempfile


def enable_GPUS():
    bpy.data.scenes[0].render.engine = "CYCLES" #"CYCLES"
    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA"  # or "OPENCL"

    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"

    for scene in bpy.data.scenes:
        scene.cycles.device = "GPU"

    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    print(bpy.context.preferences.addons["cycles"].preferences.compute_device_type)
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        d["use"] = True  # Using all devices, include GPU and CPU
        print(d["name"])


enable_GPUS()

# bpy.ops.wm.read_factory_settings(use_empty=True)

def generate(
    color1,
    color2,
    camera_X,
    camera_Y,
    camera_Z,
    fov,
    torus_X,
    torus_Y,
    torus_Z,
    progress=gr.Progress(track_tqdm=True),
):
    rgb1 = ImageColor.getcolor(color1, "RGBA")
    rgb1 = tuple(v / 255.0 for v in rgb1)
    rgb2 = ImageColor.getcolor(color2, "RGBA")
    rgb2 = tuple(v / 255.0 for v in rgb2)


    # Delete all mesh objects from the scene
    for obj in bpy.context.scene.objects:
    # If the object is of MESH type
      if obj.type == 'MESH':
          # Delete the object
          bpy.data.objects.remove(obj, do_unlink=True)
    # Add a torus
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.5,
        minor_radius=0.75,
        major_segments=12*4,
        minor_segments=12*4,
        align="WORLD",
        location=(0, 1, 1),
        rotation=(torus_X,torus_Y,torus_Z)

    )

    # Assigning the torus to a variable
    torus = bpy.context.view_layer.objects.active

    # Create a new material and assign it to the torus
    material = bpy.data.materials.new(name="RainbowGradient")
    torus.data.materials.append(material)
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear default nodes
    for node in nodes:
        nodes.remove(node)

    # Add a Gradient Texture and set it to a color ramp of a rainbow
    gradient = nodes.new(type="ShaderNodeTexGradient")
    gradient.gradient_type = "LINEAR"
    gradient.location = (0, 0)

    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "LINEAR"
    ramp.location = (200, 0)

    ramp.color_ramp.elements[0].color = rgb1
    ramp.color_ramp.elements[1].color = rgb2

    # Add Shader nodes
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (400, 0)

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600, 0)

    # Connect the nodes
    material.node_tree.links.new
    material.node_tree.links.new(gradient.outputs["Color"], ramp.inputs[0])
    material.node_tree.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Rotate the gradient to apply it from left to right
    torus = bpy.context.view_layer.objects.active
    # torus.rotation_euler = 

    # Light
    light = bpy.data.objects["Light"]
    light.location = (0.1, 0, 2)  # Position the light

    # Camera
    camera = bpy.data.objects["Camera"]
    camera.location = (camera_X, camera_Y, camera_Z)
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 5
    camera.data.dof.aperture_fstop = 4
    camera.data.angle = fov
    camera.data.type = 'PERSP'
  
    # Render
    with tempfile.NamedTemporaryFile(suffix=".JPEG", delete=False) as f:
        
        bpy.context.scene.render.resolution_y = 288
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.image_settings.file_format = "JPEG"
        bpy.context.scene.render.filepath = f.name

        with tqdm() as pbar:

          def elapsed(dummy):
            pbar.update()

          bpy.app.handlers.render_stats.append(elapsed)
          bpy.context.scene.frame_set(1)
          bpy.context.scene.frame_current = 1

          # bpy.ops.render.render(animation=False, write_still=True)
          # bpy.ops.render.render(animation=False, write_still=True)
          bpy.ops.render.render(animation=False, write_still=True)
                                
          bpy.data.images["Render Result"].save_render(
              filepath=bpy.context.scene.render.filepath
          )
          bpy.app.handlers.render_stats.clear()
          return f.name


# generate("#ffffff", "#aaa", 1)
with gr.Blocks() as demo:
    gr.Markdown("""# Gradio with Blender bpy
    based on [kolibril13](https://github.com/kolibril13/ipyblender-experimental)
    """)
    with gr.Row():
        with gr.Column():
            color1 = gr.ColorPicker(value="#59C173")
            color2 = gr.ColorPicker(value="#5D26C1")
            torus_X = gr.Slider(minimum=-pi, maximum=pi, value=0, label="Torus φ")
            torus_Y = gr.Slider(minimum=-pi, maximum=pi, value=-3, label="Torus θ")
            torus_Z = gr.Slider(minimum=-pi, maximum=pi, value=1.5, label="Torus ψ")
            fov = gr.Slider(minimum=0.0, maximum=pi, value=pi/3, label="FOV")
            camera_X = gr.Slider(minimum=-100, maximum=100, value=5, label="Camera X")
            camera_Y = gr.Slider(minimum=-100, maximum=100, value=-3, label="Camera Y")
            camera_Z = gr.Slider(minimum=-100, maximum=100, value=4, label="Camera Z")

            render_btn = gr.Button("Render")
        with gr.Column(scale=3):
            image = gr.Image(type="filepath")

    render_btn.click(
        generate,
        inputs=[
            color1,
            color2,
            camera_X,
            camera_Y,
            camera_Z,
            fov,
            torus_X,
            torus_Y,
            torus_Z,
        ],
        outputs=[image],
    )

demo.queue(concurrency_count=1)
demo.launch(debug=True, inline=True)