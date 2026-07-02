import os
import random
import time
from elevenlabs import generate, save
import replicate
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Estas variables se llenarán automáticamente desde GitHub Secrets
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if not ELEVENLABS_API_KEY or not REPLICATE_API_TOKEN:
    raise Exception("Faltan las claves API. Revisa los Secrets de GitHub.")

# --- BASE DE DATOS DE TEMAS (Puedes agregar cientos aquí) ---
THEMES = [
    "El soldado que salvó a 200 prisioneros usando solo palomas",
    "La mujer espía que hackeó el código Morse en la guerra fría",
    "El ingeniero que detuvo un desastre nuclear con una sola decisión",
    "El explorador perdido que descubrió una civilización olvidada",
    "El artista que pintó secretos de resistencia en paredes durante la guerra",
    "El médico que curó epidemias sin medicamentos modernos",
    "El niño de 10 años que salvó un pueblo de un incendio forestal",
    "La maestra que enseñó en secreto bajo un régimen totalitario"
]

# --- ESTILOS VISUALES DINÁMICOS (Para evitar penalización de spam) ---
STYLES = [
    "cinematic film noir, high contrast black and white, dramatic shadows, grainy texture",
    "watercolor painting, soft historical illustration, muted colors, vintage paper texture",
    "oil painting, classical style, dramatic lighting, intense emotion, brush strokes visible",
    "charcoal sketch, gritty texture, rough lines, intense mood, monochrome",
    "hyper-realistic photography, 8k resolution, documentary style, shallow depth of field"
]

def get_topic():
    return random.choice(THEMES)

def generate_script(topic):
    # Simulación de llamada a LLM (En producción real usarías OpenAI API aquí)
    # Para este ejemplo, generamos un guion estructurado basado en el tema
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
    try:
        audio = generate(
            text=script, 
            voice="Rachel", # Voz femenina emotiva y clara
            model="eleven_multilingual_v2"
        )
        save(audio, "voiceover.mp3")
        return "voiceover.mp3"
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
                    "height": 1920, # Formato vertical para Shorts/TikTok
                    "num_inference_steps": 25
                }
            )
            # Replicate devuelve una URL, necesitamos descargarla localmente para MoviePy
            img_url = output[0]
            img_filename = f"img_{i}.png"
            with open(img_filename, "wb") as f:
                f.write(requests.get(img_url).content)
            images.append(img_filename)
        except Exception as e:
            print(f"Error generando imagen {i}: {e}")
            continue
            
    return images

def create_video(images, audio_file):
    if not images or not audio_file:
        return None
        
    clips = []
    audio_duration = AudioFileClip(audio_file).duration
    duration_per_img = audio_duration / len(images)
    
    for img_path in images:
        clip = ImageClip(img_path).set_duration(duration_per_img)
        # Efecto simple de zoom lento (Ken Burns effect simulado)
        # clip = clip.resize(lambda t: 1 + 0.05*t) 
        clips.append(clip)
        
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
    if not audio_file: return
    
    images = generate_images(topic, style)
    if not images: return
    
    video_file = create_video(images, audio_file)
    if not video_file: return
    
    print(f"✅ VIDEO LISTO: {video_file}")
    print("Listo para subir a plataformas (simulado).")
    
    # Aquí iría la lógica de subida a TikTok/YouTube usando sus APIs
    # Por ahora, el video se guarda en la carpeta del repositorio

if __name__ == "__main__":
    main()
