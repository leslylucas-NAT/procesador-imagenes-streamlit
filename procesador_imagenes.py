import streamlit as st
from PIL import Image
import os
import io
import zipfile
from rembg import remove, new_session  # Importamos new_session

# --- CONFIGURACIÓN DE REMBG (VERSION LIGERA) ---
# Creamos una sesión global para que no cargue el modelo cada vez que procesa una imagen
@st.cache_resource
def get_rembg_session():
    # "u2netp" es la versión ligera (vatios de memoria vs gigas)
    return new_session("u2netp")

# --- LÓGICA DE PROCESAMIENTO COMPLETO DE IMAGEN ---

def procesar_imagen_completo(image_data: bytes, original_filename: str, 
                             size: tuple, dpi: tuple, remove_bg: bool) -> list[dict]:
    results = []
    
    try:
        # 1. Abrir la imagen
        img_original = Image.open(io.BytesIO(image_data))
        
        # --- Aplicar Redimensión ---
        img_processed = img_original.resize(size, Image.Resampling.LANCZOS)
            
        # Versiones para manejar formatos
        img_for_png = img_processed.convert('RGBA')
        img_for_jpg = img_processed.convert('RGB') 
        
        name, _ = os.path.splitext(original_filename)

        # ------------------------------------------------------------------
        # --- GENERACIÓN PNG (CON REMBG LIGERO) ---
        # ------------------------------------------------------------------
        
        if remove_bg:
            # Obtenemos la sesión ligera cargada en caché
            session = get_rembg_session()
            # Aplicamos remove usando esa sesión específica
            img_final_png = remove(img_for_png, session=session)
            
            buffer_png = io.BytesIO()
            img_final_png.save(buffer_png, format='PNG', dpi=dpi)
            buffer_png.seek(0)
            
            output_filename_png = f"{name}.png"
            results.append({
                "name": output_filename_png,
                "data": buffer_png.read(),
                "mime": "image/png"
            })

        # ------------------------------------------------------------------
        # --- GENERACIÓN JPG ---
        # ------------------------------------------------------------------
        
        buffer_jpg = io.BytesIO()
        img_for_jpg.save(buffer_jpg, format='JPEG', dpi=dpi)
        buffer_jpg.seek(0)

        output_filename_jpg = f"{name}.jpg"
        results.append({
            "name": output_filename_jpg,
            "data": buffer_jpg.read(),
            "mime": "image/jpeg"
        })

    except Exception as e:
        st.error(f"Error procesando {original_filename}: {e}")
    
    return results

# --- EL RESTO DE TU INTERFAZ STREAMLIT PERMANECE IGUAL ---
# (Se mantiene el resto del código que ya tenías: main, clear_results, etc.)

def clear_results():
    if 'processed_results' in st.session_state:
        st.session_state.processed_results = []

def main():
    st.set_page_config(page_title="Redimensionador Ligero", layout="centered")
    st.title("✂️ Procesador de Imágenes (Versión Lite)")
    st.markdown("Configura los parámetros. Esta versión usa el modelo **u2netp** para ahorrar memoria.")
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        col1, col2 = st.columns(2)
        with col1:
            input_width = st.number_input("Ancho", min_value=100, max_value=5000, value=500)
        with col2:
            input_height = st.number_input("Alto", min_value=100, max_value=5000, value=500)
        input_dpi = st.number_input("DPI", min_value=72, max_value=600, value=150)
        remove_bg_enabled = st.checkbox("Remover fondo", value=True)
    
    uploaded_files = st.file_uploader("Imágenes", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    
    if uploaded_files:
        if st.button("🚀 Iniciar"):
            st.session_state.processed_results = []
            progress_bar = st.progress(0)
            target_size = (input_width, input_height)
            target_dpi = (input_dpi, input_dpi)
            
            for i, file in enumerate(uploaded_files):
                image_bytes = file.read()
                current_file_results = procesar_imagen_completo(
                    image_bytes, file.name, target_size, target_dpi, remove_bg_enabled
                )
                st.session_state.processed_results.extend(current_file_results)
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            st.success("¡Completado!")
    
    if st.session_state.processed_results:
        # Lógica de descarga... (igual a tu código)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            for res in st.session_state.processed_results:
                zf.writestr(res['name'], res['data'])
        st.download_button("Descargar todo (ZIP)", data=zip_buffer.getvalue(), file_name="fotos.zip")

if __name__ == "__main__":
    main()
