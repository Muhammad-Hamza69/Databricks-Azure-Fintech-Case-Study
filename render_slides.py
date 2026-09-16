import os
import subprocess
import win32com.client

script_dir = r"c:\Users\hp\Desktop\New folder (9)"
pptx_path = os.path.join(script_dir, "Clickstream_Lakehouse_Presentation.pptx")

# Render slides to PNG
out_dir = r"C:\Users\hp\.gemini\antigravity-ide\brain\1df06319-b043-41d3-b3ab-cd7d2a051af5\slide_renders"
os.makedirs(out_dir, exist_ok=True)

try:
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    pres = ppt_app.Presentations.Open(os.path.abspath(pptx_path), WithWindow=False)

    for i, slide in enumerate(pres.Slides):
        img_path = os.path.join(out_dir, f"slide_{i+1}.png")
        slide.Export(os.path.abspath(img_path), "PNG", 1920, 1080)
        print(f"Exported slide {i+1} to {img_path}")

    pres.Close()
    ppt_app.Quit()
    print("Done rendering slides!")
except Exception as e:
    print(f"PowerPoint export failed: {e}")
