import os
import sys
import random
import requests
from io import BytesIO
from PIL import Image
import replicate
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# --- CONFIGURACIÓN DE SEGURIDAD ---
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not ELEVENLABS_API_KEY or not REPLICATE_API_TOKEN:
    print("❌ ERROR CRÍTICO: Faltan las claves API.")
    print("Verifica GitHub Secrets > Actions > ELEVENLABS_API_KEY y REPLICATE_API_TOKEN")
    sys.exit(1)

print("✅ Claves API cargadas correctamente.")

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
    # Usamos la API directa con requests, SIN importar elevenlabs
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
        print("🎤 Generando voz con ElevenLabs API...")
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            with open("voiceover.mp3", "wb") as f:
                f.write(response.content)
            print("✅ Voz generada exitosamente.")
            return "voiceover.mp3"
        else:
            print(f"❌ Error ElevenLabs: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción generando voz: {e}")
        return None

def generate_images(topic, style):
    images = []
    prompts = [
        f"{style}, {topic}, cinematic composition, wide shot",
        f"{style}, close up of determined face, emotional expression, {topic}",
        f"{style}, dramatic action scene related to {topic}, dynamic angle"
    ]
    
    print("🎨 Generando imágenes con Replicate...")
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
            print(f"  - Descargando imagen {i+1}/3...")
            
            response = requests.get(img_url, timeout=60)
            if response.status_code != 200:
                print(f"  ❌ Error descargando imagen {i+1}: {response.status_code}")
                continue
                
            img_data = BytesIO(response.content)
            image = Image.open(img_data)
            
            filename = f"img_{i}.png"
            image.save(filename)
            images.append(filename)
            print(f"  ✅ Imagen {i+1} guardada.")
            
        except Exception as e:
            print(f"  ❌ Error generando imagen {i+1}: {e}")
            continue
            
    if not images:
        print("❌ No se generaron imágenes.")
        return None
        
    print(f"✅ Imágenes generadas: {len(images)}")
    return images

def create_video(images, audio_file):
    if not images or not audio_file:
        return None
        
    clips = []
    try:
        print("🎬 Creando video final...")
        audio_duration = AudioFileClip(audio_file).duration
        duration_per_img = audio_duration / len(images)
        
        for idx, img_path in enumerate(images):
            clip = ImageClip(img_path).set_duration(duration_per_img)
            clips.append(clip)
            
        final_video = concatenate_videoclips(clips, method="compose")
        final_video = final_video.set_audio(AudioFileClip(audio_file))
        final_video.write_videofile("final_video.mp4", fps=24, codec='libx264', audio_codec='aac')
        print("✅ Video generado exitosamente.")
        return "final_video.mp4"
        
    except Exception as e:
        print(f"❌ Error creando video: {e}")
        return None

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
        sys.exit(1)
    
    images = generate_images(topic, style)
    if not images:
        print("Fallo al generar imágenes. Deteniendo proceso.")
        sys.exit(1)
    
    video_file = create_video(images, audio_file)
    if not video_file:
        print("Fallo al crear video. Deteniendo proceso.")
        sys.exit(1)
    
    print(f"🎉 ¡PROCESO COMPLETADO! Video listo: {video_file}")

if __name__ == "__main__":
    main()
