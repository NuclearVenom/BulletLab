import imgui
import imgui.integrations.glfw
import glfw
import sys

def impl_glfw_init():
    width, height = 800, 600
    window_name = "minimal ImGui/GLFW3 example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, 1)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window

def main():
    print(f"PyImGui version: {imgui.VERSION}")
    
    imgui.create_context()
    window = impl_glfw_init()
    impl = imgui.integrations.glfw.GlfwRenderer(window)

    # State variables
    text_buffer = "Initial Text"
    widget_id = "##input"
    focus_requested = False
    
    test_mode = "None"

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()

        imgui.begin("Test Window")
        
        imgui.text(f"Current Buffer: '{text_buffer}'")
        imgui.text(f"Active ID: {widget_id}")
        
        # Test 1: Change only Python string
        if imgui.button("Test 1: Change Python String Only"):
            text_buffer = "HELLO WORLD"
            test_mode = "Change String Only"

        # Test 2: Change ID
        if imgui.button("Test 2: Change Widget ID"):
            text_buffer = "HELLO WORLD"
            widget_id = "##input_changed"
            test_mode = "Change ID"

        # Test 3: Change Focus
        if imgui.button("Test 3: Change Focus (Steal)"):
            text_buffer = "HELLO WORLD"
            focus_requested = True
            test_mode = "Change Focus"

        # Test 4: Both (Change ID and Focus)
        if imgui.button("Test 4: Change ID + Focus"):
            text_buffer = "HELLO WORLD"
            widget_id = "##input_changed_focused"
            focus_requested = True
            test_mode = "Change ID + Focus"
            
        if imgui.button("Reset"):
            text_buffer = "Initial Text"
            widget_id = "##input"
            test_mode = "None"
            
        imgui.text(f"Last Action: {test_mode}")

        imgui.separator()

        if focus_requested:
            imgui.set_keyboard_focus_here()
            focus_requested = False
            
        changed, new_text = imgui.input_text(widget_id, text_buffer, 256)
        if changed:
            text_buffer = new_text

        imgui.end()

        # Render
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()

if __name__ == "__main__":
    main()
