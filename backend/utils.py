import unicodedata

TRADUCCION_REGIONES = {"Americas": "América", "Europe": "Europa", "Africa": "África", "Oceania": "Oceanía", "Asia": "Asia", "Antarctic": "Antártida"}
TRADUCCION_IDIOMAS = {"Spanish": "Español", "English": "Inglés", "French": "Francés", "Portuguese": "Portugués", "German": "Alemán", "Italian": "Italiano", "Chinese": "Chino", "Japanese": "Japonés", "Arabic": "Árabe", "Russian": "Ruso", "Dutch": "Neerlandés", "Hindi": "Hindi", "Korean": "Coreano", "Greek": "Griego", "Turkish": "Turco", "Vietnamese": "Vietnamita", "Thai": "Tailandés", "Māori": "Maorí", "Danish": "Danés", "Greenlandic": "Groenlandés", "Mandarin": "Mandarín"}
TRADUCCION_CAPITALES = {"Mexico City": "Ciudad de México", "Guatemala City": "Ciudad de Guatemala", "Panama City": "Ciudad de Panamá", "Brasília": "Brasilia", "Washington, D.C.": "Washington D.C.", "Beijing": "Pekín", "London": "Londres", "Nuuk": "Nuuk (Godthåb)"}
SINONIMOS_ESPANOL = {"eeuu": "estados unidos", "usa": "estados unidos", "holanda": "países bajos", "inglaterra": "reino unido", "corea": "corea del sur", "groelandia": "groenlandia", "china": "china"}

#Elimina acentos y convierte a minúsculas para comparaciones precisas
def normalizar_texto(texto):
    if not texto: return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto.lower().strip()