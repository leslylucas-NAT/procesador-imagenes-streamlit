import streamlit as st
from PIL import Image
import os
import io
import zipfile
from rembg import remove

# --- LÓGICA DE PROCESAMIENTO COMPLETO DE IMAGEN ---

def procesar_imagen_completo(image_data: bytes, original_filename: str, 
                             size: tuple, dpi: tuple, remove_bg: bool) -> list[dict]:
    """
    Procesa una imagen usando parámetros definidos por el usuario.
    APLICA SOLO REDIMENSIÓN al tamaño 'size'.
    Si remove_bg es False, solo genera el archivo JPG.
    Retorna una lista de diccionarios con los datos de cada imagen procesada.
    """
    results = []
    
    try:
        # 1. Abrir la imagen
        img_original = Image.open(io.BytesIO(image_data))
        
        # --- Aplicar Redimensión (resize) ---
        # El cambio solicitado es reemplazar la lógica de 'crop' por un simple 'resize'.
        # Se usa LANCZOS para obtener la mejor calidad de redimensión.
        img_processed = img_original.resize(size, Image.Resampling.LANCZOS)
            
        # Versiones para manejar formatos (RGBA para PNG, RGB para JPG)
        img_for_png = img_processed.convert('RGBA')
        img_for_jpg = img_processed.convert('RGB') 
        
        name, _ = os.path.splitext(original_filename)

        # ------------------------------------------------------------------
        # --- GENERACIÓN PNG (CONDICIONAL) ---
        # ------------------------------------------------------------------
        
        if remove_bg:
            # Eliminar el fondo (solo aplica a la versión RGBA)
            img_final_png = remove(img_for_png)
            
            buffer_png = io.BytesIO()
            img_final_png.save(buffer_png, format='PNG', dpi=dpi)
            buffer_png.seek(0)
            
            output_filename_png = f"{name}.png"
            results.append({
                "name": output_filename_png,
                "data": buffer_png.read(),
                "mime": "image/png"
            })
        # Si remove_bg es False, NO se genera el archivo PNG.

        # ------------------------------------------------------------------
        # --- GENERACIÓN JPG (INCONDICIONAL) ---
        # ------------------------------------------------------------------
        
        buffer_jpg = io.BytesIO()
        # Se guarda la versión RGB redimensionada.
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

# --- INTERFAZ STREAMLIT ---

def clear_results():
    """Función para limpiar los resultados de la sesión."""
    if 'processed_results' in st.session_state:
        st.session_state.processed_results = []

def main():
    st.set_page_config(page_title="Redimensionador de Imágenes Web Avanzado", layout="centered")
    st.title("✂️ Procesador de Imágenes")
    st.markdown("Configura los parámetros para **redimensionar** y/o eliminar el fondo de tus imágenes.")
    
    
    # ------------------------------------------------------------------
    # --- CONFIGURACIÓN DE PARÁMETROS POR EL USUARIO (Sidebar) ---
    # ------------------------------------------------------------------
    
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Parámetros de Tamaño
        st.subheader("Tamaño y Resolución")
        col1, col2 = st.columns(2)
        with col1:
            input_width = st.number_input("Ancho (píxeles)", min_value=100, max_value=5000, value=500, step=50)
        with col2:
            input_height = st.number_input("Alto (píxeles)", min_value=100, max_value=5000, value=500, step=50)
        
        input_dpi = st.number_input("DPI (Puntos por Pulgada)", min_value=72, max_value=600, value=150, step=10)
        
        # Parámetro de Eliminación de Fondo
        st.subheader("Eliminación de Fondo")
        # La clave está aquí: si es True, se genera PNG sin fondo. Si es False, solo se genera JPG.
        remove_bg_enabled = st.checkbox("Remover fondo", value=True)
        
        st.markdown("---")
        st.info("💡 **El formato JPG siempre mantiene el fondo original.**")

    
    # ------------------------------------------------------------------
    # --- UPLOAD DE ARCHIVOS ---
    # ------------------------------------------------------------------
    
    uploaded_files = st.file_uploader("Arrastra y suelta tus imágenes aquí", 
                                      type=["jpg", "jpeg", "png"], 
                                      accept_multiple_files=True,
                                      key='uploaded_files')
    
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = []
    
    
    # ------------------------------------------------------------------
    # --- BOTÓN DE PROCESAMIENTO (SOLO VISIBLE CON ARCHIVOS) ---
    # ------------------------------------------------------------------
    
    if uploaded_files:
        
        if st.button("🚀 Iniciar"):
            st.session_state.processed_results = [] # Limpiar justo antes de procesar
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            target_size = (input_width, input_height)
            target_dpi = (input_dpi, input_dpi)
            total_files = len(uploaded_files)
            
            for i, file in enumerate(uploaded_files):
                progress = (i + 1) / total_files
                progress_bar.progress(progress)
                status_text.text(f"Procesando {i + 1} de {total_files}: {file.name}...")

                image_bytes = file.read()
                
                current_file_results = procesar_imagen_completo(
                    image_bytes, file.name, target_size, target_dpi, remove_bg_enabled
                )
                
                st.session_state.processed_results.extend(current_file_results)
            
            progress_bar.empty()
            status_text.empty()
            
            if st.session_state.processed_results:
                st.success(f"¡Procesamiento de {total_files} imágenes completado! (Generando {len(st.session_state.processed_results)} archivos en total)")
            else:
                st.warning("No se pudieron procesar las imágenes.")
    else:
        # Si no hay archivos en el uploader, limpia resultados previos y muestra un mensaje
        clear_results()
        st.info("Sube las imágenes para comenzar el procesamiento.")


    # ------------------------------------------------------------------
    # --- LÓGICA DE DESCARGA DUAL (ZIP y Individual) ---
    # ------------------------------------------------------------------
    if st.session_state.processed_results:
        st.subheader("⬇️ Descargar Resultados")
        
        col_zip, col_ind = st.columns([1, 2])

        # --- Opción 1: DESCARGA EN LOTE (ZIP) ---
        with col_zip:
            st.markdown("**Opción A: Descarga Completa**")
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
                for result in st.session_state.processed_results:
                    zf.writestr(result['name'], result['data'])
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="⬇️ Descarga Completa ZIP",
                data=zip_buffer.read(),
                file_name="imagenes_procesadas_lote.zip",
                mime="application/zip",
                key="download_all_zip"
            )

        # --- Opción 2: DESCARGA INDIVIDUAL ---
        with col_ind:
            st.markdown("**Opción B: Descarga Individual**")
            for i, result in enumerate(st.session_state.processed_results):
                st.download_button(
                    label=f"Descargar: {result['name']}",
                    data=result['data'],
                    file_name=result['name'],
                    mime=result['mime'],
                    key=f"download_file_{i}"
                )

if __name__ == "__main__":
    main()
