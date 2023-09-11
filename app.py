import gradio as gr
import base64
from PIL import ImageColor
from pathlib import Path
import bpy
from tqdm import tqdm
from math import pi


def enable_GPUS():
    bpy.data.scenes[0].render.engine = "CYCLES"
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


def generate(
    color1,
    color2,
    camera_X,
    camera_Y,
    camera_Z,
    torus_X,
    torus_Y,
    torus_Z,
    progress=gr.Progress(track_tqdm=True),
):
    rgb1 = ImageColor.getcolor(color1, "RGBA")
    rgb1 = tuple(v / 255.0 for v in rgb1)
    rgb2 = ImageColor.getcolor(color2, "RGBA")
    rgb2 = tuple(v / 255.0 for v in rgb2)

    light_position_normed = light_position / 20
    # Delete all mesh objects from the scene
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.select_by_type(type="MESH")
    bpy.ops.object.delete()

    # Add a torus
    bpy.ops.mesh.primitive_torus_add(
        major_radius=1.5,
        minor_radius=0.75,
        major_segments=2**7,
        minor_segments=2**5,
        align="WORLD",
        location=(0, 1, 1),
    )

    # Assigning the torus to a variable
    # torus = bpy.context.active_object
    torus = bpy.context.view_layer.objects.active
    # print(torus)
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
    torus.rotation_euler = (
        torus_X,
        torus_Y,
        torus_Z,
    )  # Rotate 90 degrees on the Z axis

    # Light
    light = bpy.data.objects["Light"]
    light.location = (light_position_normed, 0, 2)  # Position the light

    # Camera
    camera = bpy.data.objects["Camera"]
    camera.location = (camera_X, camera_Y, camera_Z)
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 5
    camera.data.dof.aperture_fstop = 4

    # Render
    path = "test.png"
    bpy.context.scene.render.resolution_y = 256
    bpy.context.scene.render.resolution_x = 256
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = path

    with tqdm(total=bpy.context.scene.frame_end) as pbar:

        def elapsed(dummy):
            pbar.update()

        bpy.app.handlers.render_stats.append(elapsed)
        bpy.ops.render.render(animation=False, write_still=True)
        bpy.data.images["Render Result"].save_render(
            filepath=bpy.context.scene.render.filepath
        )
        temp_filepath = Path(bpy.context.scene.render.filepath)
        bpy.app.handlers.render_stats.clear()
        return path


# generate("#ffffff", "#aaa", 1)
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            color1 = gr.ColorPicker(value="#59C173")
            color2 = gr.ColorPicker(value="#5D26C1")
            camera_X = gr.Slider(minimum=-100, maximum=100, value=5, label="Camera X")
            camera_Y = gr.Slider(minimum=-100, maximum=100, value=-3, label="Camera X")
            camera_Z = gr.Slider(minimum=-100, maximum=100, value=4, label="Camera X")
            torus_X = gr.Slider(
                minimum=-2 * pi, maximum=2 * pi, value=0, label="Torus φ"
            )
            torus_Y = gr.Slider(
                minimum=-2 * pi, maximum=2 * pi, value=0, label="Torus θ"
            )
            torus_Z = gr.Slider(
                minimum=-2 * pi, maximum=2 * pi, value=pi / 2, label="Torus ψ"
            )

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
            torus_X,
            torus_Y,
            torus_Z,
        ],
        outputs=[image],
    )


# bpy.utils.register_class(generate)
demo.queue()
demo.launch(debug=True, inline=True)
