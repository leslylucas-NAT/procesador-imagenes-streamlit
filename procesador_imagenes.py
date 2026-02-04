import streamlit as st
from PIL import Image, ImageOps
import os
import io
import zipfile
from rembg import remove, new_session

# --- CONFIGURACIÓN DE REMBG (VERSION LIGERA) ---
@st.cache_resource
def get_rembg_session():
    return new_session("u2netp")

def procesar_imagen_completo(image_data: bytes, original_filename: str, 
                             target_size: tuple, dpi: tuple, remove_bg: bool) -> list[dict]:
    results = []
    
    try:
        # 1. Abrir imagen original
        img_original = Image.open(io.BytesIO(image_data))
        
        # 2. Redimensionar proporcionalmente para que quepa en el cuadro
        # Esto evita la deformación
        img_original.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # 3. Crear un "lienzo" nuevo del tamaño EXACTO pedido (ej. 500x500)
        # Para PNG usamos RGBA (transparente), para JPG usamos RGB (blanco)
        
        # --- PROCESO PARA PNG (CON FONDO TRANSPARENTE) ---
        if remove_bg:
            session = get_rembg_session()
            # Quitamos el fondo primero
            img_no_bg = remove(img_original, session=session)
            
            # Creamos el lienzo transparente exacto
            final_png = Image.new("RGBA", target_size, (0, 0, 0, 0))
            
            # Centramos el producto en el lienzo
            x = (target_size[0] - img_no_bg.size[0]) // 2
            y = (target_size[1] - img_no_bg.size[1]) // 2
            final_png.paste(img_no_bg, (x, y), img_no_bg)
            
            buffer_png = io.BytesIO()
            final_png.save(buffer_png, format='PNG', dpi=dpi)
            buffer_png.seek(0)
            
            name, _ = os.path.splitext(original_filename)
            results.append({
                "name": f"{name}.png",
                "data": buffer_png.read(),
                "mime": "image/png"
            })

        # --- PROCESO PARA JPG (CON FONDO BLANCO) ---
        # Creamos el lienzo blanco exacto
        final_jpg = Image.new("RGB", target_size, (255, 255, 255))
        
        # Centramos el producto original (con su fondo)
        img_rgb = img_original.convert("RGB")
        x = (target_size[0] - img_rgb.size[0]) // 2
        y = (target_size[1] - img_rgb.size[1]) // 2
        final_jpg.paste(img_rgb, (x, y))
        
        buffer_jpg = io.BytesIO()
        final_jpg.save(buffer_jpg, format='JPEG', dpi=dpi)
        buffer_jpg.seek(0)

        name, _ = os.path.splitext(original_filename)
        results.append({
            "name": f"{name}.jpg",
            "data": buffer_jpg.read(),
            "mime": "image/jpeg"
        })

    except Exception as e:
        st.error(f"Error procesando {original_filename}: {e}")
    
    return results

# --- INTERFAZ (Sin cambios mayores, solo mantenemos la estructura) ---
def main():
    st.set_page_config(page_title="Procesador Tamaño Exacto", layout="centered")
    st.title("📏 Tamaño Exacto sin Deformar")
    st.write("Tus imágenes serán exactamente del tamaño que pidas, centrando el producto.")

    with st.sidebar:
        st.header("⚙️ Configuración")
        input_width = st.number_input("Ancho Exacto (px)", value=500)
        input_height = st.number_input("Alto Exacto (px)", value=500)
        input_dpi = st.number_input("DPI", value=150)
        remove_bg_enabled = st.checkbox("Remover fondo", value=True)

    uploaded_files = st.file_uploader("Subir imágenes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []

    if uploaded_files and st.button("🚀 Procesar"):
        st.session_state.processed_results = []
        target_size = (input_width, input_height)
        
        for file in uploaded_files:
            res = procesar_imagen_completo(file.read(), file.name, target_size, (input_dpi, input_dpi), remove_bg_enabled)
            st.session_state.processed_results.extend(res)
        st.success("¡Proceso terminado!")

    if st.session_state.processed_results:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            for r in st.session_state.processed_results:
                zf.writestr(r['name'], r['data'])
        st.download_button("⬇️ Descargar Todo (ZIP)", zip_buffer.getvalue(), "imagenes_exactas.zip")

if __name__ == "__main__":
    main()
