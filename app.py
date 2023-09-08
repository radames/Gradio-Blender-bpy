import gradio as gr
import base64
from PIL import ImageColor
from pathlib import Path
import bpy

blender_context = bpy.context

async def generate(color1, color2, light_position):
    rbg1 = ImageColor.getcolor(color1, "RGB")
    rgb2 = ImageColor.getcolor(color2, "RGB")
    print(rbg1, rgb2 , light_position)
 
    light_position_normed = light_position / 20
    # Delete all mesh objects from the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Add a torus
    print(bpy.ops.mesh.primitive_torus_add(
        major_radius=1.5, 
        minor_radius=0.75, 
        major_segments=48*4, 
        minor_segments=12*4, 
        align="WORLD", 
        location=(0, 1, 1),
    ))
    torus = blender_context.active_object

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
    gradient.gradient_type = 'LINEAR'
    gradient.location = (0,0)

    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'LINEAR'
    ramp.location = (200,0)

    ramp.color_ramp.elements[0].color = rgb1
    ramp.color_ramp.elements[1].color = rbg2

    # Add Shader nodes
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (400,0)

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600,0)

    # Connect the nodes
    material.node_tree.links.new
    material.node_tree.links.new(gradient.outputs["Color"], ramp.inputs[0])
    material.node_tree.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    material.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Rotate the gradient to apply it from left to right
    torus.rotation_euler = (0, 0, 1.5708)  # Rotate 90 degrees on the Z axis

    # Light
    light = bpy.data.objects["Light"]
    light.location = (light_position_normed, 0, 2)  # Position the light 

    # Camera
    camera = bpy.data.objects["Camera"]
    camera.location = (5, -3, 4)
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 5
    camera.data.dof.aperture_fstop = 4 

    # Render
    path = "test.png"
    blender_context.scene.render.resolution_x = 1000
    blender_context.scene.render.resolution_y = 400
    blender_context.scene.render.image_settings.file_format = "PNG"
    blender_context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.images["Render Result"].save_render(filepath=blender_context.scene.render.filepath)

    # display(Image("test_sphere.png"))

    # Read the saved image into memory and encode it to base64
    temp_filepath = Path(blender_context.scene.render.filepath)
    with temp_filepath.open("rb") as f:
        my_img = base64.b64encode(f.read()).decode("utf-8")

    return temp_filepath

with gr.Blocks() as demo:
    with gr.Row():   
        with gr.Column():
          color1 = gr.ColorPicker()
          color2 = gr.ColorPicker()
          slider = gr.Slider(minimum=0, maximum=100, value=1)
        with gr.Column(scale=3):
          image = gr.Image(type="filepath")

    slider.change(generate, inputs=[color1, color2, slider], outputs=[image], show_progress=False)



demo.launch(debug=True)