import os
import random
import sys
import requests
from io import BytesIO
from PIL import Image
import replicate
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# --- CONFIGURACIÓN DE SEGURIDAD ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not ELEVENLABS_API_KEY or not REPLICATE_API_TOKEN:
    print("ERROR: Faltan las claves API. Revisa los Secrets de GitHub.")
    sys.exit(1)

# --- BASE DE DATOS DE TEMAS ---
THEMES = [
    "El soldado que salvó a 200 prisioneros usando solo palomas",
    "La mujer espía que hackeó el código Morse en la guerra fría",
    "El ingeniero que detuvo un desastre nuclear con una sola decisión",
    "El explorador perdido que descubrió una civilización olvidada",
    "El artista que pintó secretos de resistencia en paredes durante la guerra"
]

STYLES = [
    "cinematic film noir, high contrast black and white, dramatic shadows",
    "watercolor painting, soft historical illustration, muted colors",
    "oil painting, classical style, dramatic lighting, intense emotion",
    "charcoal sketch, gritty texture, rough lines, intense mood",
    "hyper-realistic photography, 8k resolution, documentary style"
]

def get_topic():
    return random.choice(THEMES)

def generate_script(topic):
    hooks = [
        f"¿Sabías que {topic}? Nadie conoce su nombre, pero...",
        f"Lo que ocurrió con {topic} fue borrado de los libros de historia.",
        f"Este es el acto de valor más grande que nunca verás en Netflix."
    ]
    hook = random.choice(hooks)
    
    script = f"""
    {hook}
    En medio del caos absoluto, {topic}. 
    La mayoría habría huido, pero él/ella tomó una decisión imposible.
    Sin armas, sin ayuda, solo con su mente.
    Su acción cambió el curso de la historia para siempre.
    ¿Te imaginas tener ese valor?
    Descubre la historia completa en el enlace de mi perfil.
    """
    return script.strip()

def generate_voice(script):
    url = "https://api.elevenlabs.io/v1/text-to-speech/Rachel"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open("voiceover.mp3", "wb") as f:
                f.write(response.content)
            return "voiceover.mp3"
        else:
            print(f"Error ElevenLabs: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error generando voz: {e}")
        return None

def generate_images(topic, style):
    images = []
    prompts = [
        f"{style}, {topic}, cinematic composition, wide shot",
        f"{style}, close up of determined face, emotional expression, {topic}",
        f"{style}, dramatic action scene related to {topic}, dynamic angle"
    ]
    
    for i, prompt in enumerate(prompts):
        try:
            output = replicate.run(
                "stability-ai/sdxl",
                input={
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, cartoon, text, watermark, deformed",
                    "width": 1024,
                    "height": 1920, 
                    "num_inference_steps": 25
                }
            )
            img_url = output[0]
            
            # Descargar imagen directamente
            response = requests.get(img_url)
            img_data = BytesIO(response.content)
            image = Image.open(img_data)
            
            filename = f"img_{i}.png"
            image.save(filename)
            images.append(filename)
            
        except Exception as e:
            print(f"Error generando imagen {i}: {e}")
            continue
            
    return images

def create_video(images, audio_file):
    if not images or not audio_file:
        return None
        
    clips = []
    try:
        audio_duration = AudioFileClip(audio_file).duration
    except Exception as e:
        print(f"Error cargando audio: {e}")
        return None
        
    duration_per_img = audio_duration / len(images)
    
    for img_path in images:
        try:
            clip = ImageClip(img_path).set_duration(duration_per_img)
            clips.append(clip)
        except Exception as e:
            print(f"Error procesando imagen {img_path}: {e}")
            continue
        
    if not clips:
        return None
        
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(AudioFileClip(audio_file))
    final_video.write_videofile("final_video.mp4", fps=24, codec='libx264', audio_codec='aac')
    return "final_video.mp4"

def main():
    print("--- INICIANDO SISTEMA AUTÓNOMO ---")
    topic = get_topic()
    print(f"Tema seleccionado: {topic}")
    
    style = random.choice(STYLES)
    print(f"Estilo visual: {style}")
    
    script = generate_script(topic)
    print("Guion generado.")
    
    audio_file = generate_voice(script)
    if not audio_file:
        print("Fallo al generar voz. Deteniendo proceso.")
        return
    
    images = generate_images(topic, style)
    if not images:
        print("Fallo al generar imágenes. Deteniendo proceso.")
        return
    
    video_file = create_video(images, audio_file)
    if not video_file:
        print("Fallo al crear video. Deteniendo proceso.")
        return
    
    print(f"✅ VIDEO GENERADO EXITOSAMENTE: {video_file}")

if __name__ == "__main__":
    main()
