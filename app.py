import streamlit as st
import pandas as pd
import hashlib
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Gota de Leche - Plataforma Web",
    page_icon="🍼",
    layout="wide"
)

# --- 2. CONEXIÓN CON SUPABASE ---
@st.cache_resource
def conectar_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = conectar_supabase()
except Exception as e:
    st.error(f"Error de configuración en secrets.toml: {e}")

# --- 3. FUNCIONES DE BASE DE DATOS ---

def cargar_noticias():
    # Trae las noticias ordenadas por ID descendente (la más nueva primero)
    respuesta = supabase.table("noticias").select("*").order("id", descending=True).execute()
    return pd.DataFrame(respuesta.data)

def publicar_noticia(titulo, categoria, contenido):
    datos = {
        "titulo": titulo,
        "categoria": categoria,
        "contenido": contenido
    }
    supabase.table("noticias").insert(datos).execute()

def verificar_usuario(username, password_ingresada):
    # Convertimos la contraseña ingresada a SHA-256
    hash_objeto = hashlib.sha256(password_ingresada.encode())
    hash_resultado = hash_objeto.hexdigest()
    
    # Consultamos si coincide el usuario y el hash en Supabase
    respuesta = supabase.table("usuarios")\
        .select("*")\
        .eq("username", username)\
        .eq("password_hash", hash_resultado)\
        .execute()
    
    return len(respuesta.data) > 0

# --- 4. MENÚ DE NAVEGACIÓN (SIDEBAR) ---
with st.sidebar:
    st.markdown("### 🍼 Gota de Leche")
    seccion = st.radio(
        "Navegación:",
        ["Inicio", "Quiénes Somos", "Noticias y Actividades", "Requisitos Beneficiarios", "Panel de Administración"]
    )
    st.markdown("---")
    st.caption("© 2026 Corporación Gota de Leche")

# --- 5. CONTROL DE VISTAS (PÁGINAS) ---

if seccion == "Inicio":
    st.title("Bienvenidos a la Gota de Leche")
    st.write("""
    Esta es la plataforma oficial de la corporación. Nuestra misión es apoyar la nutrición 
    y el desarrollo integral infantil en nuestra comunidad. Navega por las secciones 
    para enterarte de nuestra labor, requisitos para beneficiarios y últimas actividades.
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("**Aviso a la comunidad:** Puedes revisar la pestaña de 'Noticias y Actividades' para enterarte de los últimos cambios de horarios o campañas vigentes.")
    with col2:
        st.success("**¿Quieres colaborar?** Próximamente habilitaremos un módulo de contacto para socios y donaciones.")

elif seccion == "Quiénes Somos":
    st.title("👥 Quiénes Somos")
    st.subheader("Nuestra Historia y Misión")
    st.write("""
    La Corporación Gota de Leche es una institución sin fines de lucro dedicada a proteger 
    y asegurar la correcta alimentación de lactantes y niños en situación de vulnerabilidad. 
    A través de la entrega programada de suplementos y apoyo social, buscamos erradicar 
    las brechas de malnutrición.
    """)

elif seccion == "Noticias y Actividades":
    st.title("📰 Actualidad y Avisos Importantes")
    st.write("Entérate de las últimas novedades de la corporación en tiempo real.")
    
    try:
        df = cargar_noticias()
        if df.empty:
            st.info("No hay publicaciones disponibles por el momento.")
        else:
            for _, fila in df.iterrows():
                # Despliega cada noticia en un contenedor limpio
                with st.container(border=True):
                    st.subheader(fila['titulo'])
                    st.caption(f"Fecha de publicación: {fila['fecha']} | Categoría: {fila['categoria']}")
                    st.write(fila['contenido'])
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")

elif seccion == "Requisitos Beneficiarios":
    st.title("📋 ¿Cómo acceder a los beneficios?")
    st.write("Para postular al programa de asistencia alimentaria, se deben presentar los siguientes documentos en secretaría:")
    st.markdown("""
    * Carnet de Control de Niño Sano al día.
    * Registro Social de Hogares (RSH).
    * Comprobante de domicilio actualizado.
    * Cédula de identidad del tutor legal.
    """)

elif seccion == "Panel de Administración":
    st.title("🔒 Panel de Control (Admin)")
    
    # Manejo del estado de la sesión
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        
    if not st.session_state["autenticado"]:
        st.subheader("Iniciar Sesión")
        usuario_input = st.text_input("Usuario")
        contrasena_input = st.text_input("Contraseña", type="password") 
        
        if st.button("Ingresar"):
            if verificar_usuario(usuario_input, contrasena_input):
                st.session_state["autenticado"] = True
                st.success("¡Autenticación exitosa!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    else:
        st.sidebar.success("Sesión: Administrador Conectado")
        if st.button("Cerrar Sesión"):
            st.session_state["autenticado"] = False
            st.rerun()
            
        st.markdown("---")
        
        # Formulario protegido para insertar nuevas noticias
        with st.form("formulario_noticia", clear_on_submit=True):
            st.subheader("📝 Publicar nuevo contenido en la Web")
            titulo_input = st.text_input("Título de la publicación")
            categoria_input = st.selectbox("Categoría", ["Aviso urgente", "Actividad", "Campaña", "Logro"])
            contenido_input = st.text_area("Escribe el cuerpo de la noticia aquí...")
            
            enviar = st.form_submit_button("Publicar en la Web")
            
            if enviar:
                if titulo_input and contenido_input:
                    try:
                        publicar_noticia(titulo_input, categoria_input, contenido_input)
                        st.success("¡La publicación se ha subido con éxito a Supabase!")
                    except Exception as e:
                        st.error(f"Error al guardar en la base de datos: {e}")
                else:
                    st.warning("Por favor, rellena todos los campos antes de enviar.")