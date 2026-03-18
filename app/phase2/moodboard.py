# import os
# import base64
# import uuid
# from typing import List, Dict

# from openai import OpenAI

# MOOD_DIR = "app/data/moodboards"
# os.makedirs(MOOD_DIR, exist_ok=True)

# client = OpenAI()

# def build_prompts(vibe: str, palette: str, season: str, venue_type: str) -> List[str]:
#     base = f"{vibe} wedding style, palette {palette}, season {season}, venue {venue_type}, natural light, editorial photography"
#     return [
#         f"Bouquet concept: {base}, close-up floral bouquet, high detail",
#         f"Tablescape concept: {base}, table setting with linens, plates, candles, centerpiece",
#         f"Ceremony concept: {base}, ceremony aisle, decor, guests area, wide shot",
#         f"Reception concept: {base}, reception decor, lighting, modern details, wide shot",
#     ]

# def save_base64_png(b64: str) -> str:
#     image_bytes = base64.b64decode(b64)
#     filename = f"{uuid.uuid4()}.png"
#     path = os.path.join(MOOD_DIR, filename)
#     with open(path, "wb") as f:
#         f.write(image_bytes)
#     return path

# def generate_images(prompts: List[str]) -> List[str]:
#     """
#     Returns list of local file paths for demo.
#     """
#     paths = []
#     for p in prompts:
#         result = client.images.generate(
#             model="gpt-image-1",
#             prompt=p,
#             size="1024x1024"
#         )
#         b64 = result.data[0].b64_json
#         paths.append(save_base64_png(b64))
#     return paths


# app/phase2/moodboard.py
from openai import OpenAI

client = OpenAI()

def generate_moodboard(prompt: str, n: int = 4):
    # gpt-image-1 returns base64 (b64_json)
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        n=n,
    )

    images = []
    for img in result.data:
        # Convert base64 to a browser-friendly data URL
        images.append(f"data:image/png;base64,{img.b64_json}")

    return images