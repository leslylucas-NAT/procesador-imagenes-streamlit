import streamlit as st
from PIL import Image, ImageOps  # Importamos ImageOps
import os
import io
import zipfile
from rembg import remove, new_session

# --- CONFIGURACIÓN DE REMBG (VERSION LIGERA) ---
@st.cache_resource
def get_rembg_session():
    return new_session("u2netp")

# --- LÓGICA DE PROCESAMIENTO ---

def procesar_imagen_completo(image_data: bytes, original_filename: str, 
                             target_size: tuple, dpi: tuple, remove_bg: bool) -> list[dict]:
    results = []
    
    try:
        img_original = Image.open(io.BytesIO(image_data))
        
        # --- REDIMENSIÓN SIN DEFORMAR (Proporcional) ---
        # ImageOps.contain ajusta la imagen al máximo posible dentro de target_size
        # sin estirarla, respetando las proporciones del producto.
        img_processed = ImageOps.contain(img_original, target_size, Image.Resampling.LANCZOS)
            
        img_for_png = img_processed.convert('RGBA')
        img_for_jpg = img_processed.convert('RGB') 
        
        name, _ = os.path.splitext(original_filename)

        # --- GENERACIÓN PNG (QUITAR FONDO) ---
        if remove_bg:
            session = get_rembg_session()
            img_final_png = remove(img_for_png, session=session)
            
            buffer_png = io.BytesIO()
            img_final_png.save(buffer_png, format='PNG', dpi=dpi)
            buffer_png.seek(0)
            
            results.append({
                "name": f"{name}.png",
                "data": buffer_png.read(),
                "mime": "image/png"
            })

        # --- GENERACIÓN JPG ---
        buffer_jpg = io.BytesIO()
        img_for_jpg.save(buffer_jpg, format='JPEG', dpi=dpi)
        buffer_jpg.seek(0)

        results.append({
            "name": f"{name}.jpg",
            "data": buffer_jpg.read(),
            "mime": "image/jpeg"
        })

    except Exception as e:
        st.error(f"Error procesando {original_filename}: {e}")
    
    return results

# --- INTERFAZ (Se mantienen tus funciones de UI) ---
def main():
    st.set_page_config(page_title="Procesador Proporcional", layout="centered")
    st.title("✂️ Procesador sin Deformación")
    st.info("Las imágenes se ajustarán al tamaño máximo elegido sin estirarse.")

    with st.sidebar:
        st.header("⚙️ Ajustes")
        input_width = st.number_input("Ancho Máximo", value=1000)
        input_height = st.number_input("Alto Máximo", value=1000)
        input_dpi = st.number_input("DPI", value=150)
        remove_bg_enabled = st.checkbox("Remover fondo (Lite)", value=True)

    uploaded_files = st.file_uploader("Subir imágenes", type=["jpg", "png"], accept_multiple_files=True)

    if uploaded_files and st.button("🚀 Iniciar"):
        st.session_state.processed_results = []
        target_size = (input_width, input_height)
        
        for file in uploaded_files:
            res = procesar_imagen_completo(file.read(), file.name, target_size, (input_dpi, input_dpi), remove_bg_enabled)
            st.session_state.processed_results.extend(res)
        st.success("¡Listo!")

    # Lógica de descarga (ZIP)...
    if 'processed_results' in st.session_state and st.session_state.processed_results:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
            for r in st.session_state.processed_results:
                zf.writestr(r['name'], r['data'])
        st.download_button("Descargar ZIP", zip_buffer.getvalue(), "resultado.zip")

if __name__ == "__main__":
    main()
