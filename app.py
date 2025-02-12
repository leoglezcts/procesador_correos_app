import streamlit as st
import pandas as pd
import numpy as np
import re
import warnings

# Título de la aplicación
st.title("📩 Procesador de Correos")

# Subida de archivos
archivo_subido = st.file_uploader("📂 Carga tu archivo CSV", type=["csv"])
st.write("Asegurate que tu archivo es CSV-UTF8 y está separado por comas")

# Dropdown (Acordeón) para mostrar/ocultar los features
with st.expander("### ¿Qué hace esta aplicación? 🚀", expanded=False):  # expanded=False para que inicie cerrado
    st.markdown("""
    **Eliminación de correos no válidos:**

    Detecta y elimina correos electrónicos que no cumplen con un formato válido (por ejemplo, correos con doble arroba `@@`, sin `@`, o que contienen caracteres no permitidos).

    **Filtrado de correos no deseados:**

    Usa expresiones regulares (regex) para identificar y eliminar correos que contienen palabras o patrones no deseados, como "dummy", "prueba", "no.tiene", entre otros.

    **Limpieza de typo en el campo de email:**

    Convierte todos los correos a minúsculas, elimina espacios innecesarios y normaliza el formato.

    **Eliminación de duplicados:**

    Elimina correos duplicados que aparecen más de 4 veces en el archivo, lo que ayuda a mantener un DataFrame limpio y sin redundancias.

    **Limpieza en el campo de nombres:**

    Si existe el campo de nombres (`NOMBRES`), la aplicación limpia los datos:
    - Elimina caracteres especiales no permitidos.
    - Rellena nombres vacíos con la palabra "ESTIMADO".
    - Normaliza nombres comunes (por ejemplo, convierte "MA" a "MARIA").

    **Eliminación de registros REPEP:**

    Si existe un campo `FLG_REPEP`, la aplicación elimina los registros marcados con "Y".

    **Generación de archivos de salida:**

    Crea dos archivos CSV como resultado:
    - **Archivo limpio:** Contiene los correos válidos y limpios.
    - **Archivo de correos eliminados:** Contiene los correos que fueron descartados durante el proceso.
    """)

if archivo_subido:
    if st.button("🚀 Procesar Archivo"):
        st.write("Procesando archivo...")
        
        # Leer el archivo subido
        df = pd.read_csv(archivo_subido, on_bad_lines='skip', low_memory=False, encoding = 'latin1', sep=",")
        
        # Definir la función limpiar_correos
        def limpiar_correos(df, wrong_words_regex):
            # Ignorar advertencias de grupos de captura en regex
            warnings.filterwarnings("ignore", category=UserWarning)
            
            # Eliminar valores nulos en 'EMAIL'
            st.write("**SECCIÓN DE NULOS**")
            st.write(f"Número de registros antes de eliminar valores nulos en 'EMAIL': {len(df)}")
            df.dropna(subset=['EMAIL'], inplace=True)
            st.write(f"Número de registros después de eliminar valores nulos en 'EMAIL': {len(df)}")
            st.write()
            
            # Limpiar la columna 'EMAIL'
            df['EMAIL'] = df['EMAIL'].str.lower().str.strip().str.replace(' ', '')
            
            # Filtrar correos no deseados usando regex
            combined_regex = '|'.join(wrong_words_regex)
            mask = df['EMAIL'].str.contains(combined_regex, regex=True)
            correos_eliminados = df[mask]['EMAIL'].tolist()
            df_clean = df[~mask]
            
            # Eliminar duplicados con frecuencia mayor a 4
            frecuencia_correos = df_clean.groupby('EMAIL').size()
            correos_repetidos = frecuencia_correos[frecuencia_correos > 4].index
            df_clean = df_clean[~df_clean['EMAIL'].isin(correos_repetidos)]
            
            st.write("**SECCIÓN DE REGISTROS CON FRECUENCIAS ALTAS**")
            st.write(f"Número de correos con frecuencia mayor a cuatro: {len(correos_repetidos)}")
            st.write(f"Número de filas eliminadas debido a duplicados con frecuencia mayor a cuatro: {len(df) - len(df_clean)}")
            st.write()
            
            # Limpiar la columna 'NOMBRES'
            if 'NOMBRES' in df_clean.columns:
                df_clean['NOMBRES'] = (
                    df_clean['NOMBRES']
                    .str.strip()
                    .replace(['', ' ', '  ', '   '], np.nan, regex=False)
                    .replace(r'[^a-zA-Z\s]', np.nan, regex=True)
                    .replace('.', '')
                    .fillna('ESTIMADO')
                    .replace('MA', 'MARIA')
                    .str.split(" ").str.get(0)
                )
                st.write("**SECCIÓN DE LLENADO DE NOMBRES VACÍOS**")
                st.write(f"Cantidad de nombres llenados con 'ESTIMADO': {(df_clean['NOMBRES'] == 'ESTIMADO').sum()}")
                st.write()
            else:
                st.write("Error: La columna 'NOMBRES' no existe en el DataFrame.")
            
            # Eliminar registros REPEP
            if 'FLG_REPEP' in df_clean.columns:
                st.write('**SECCIÓN DE REPEP**')
                st.write(f'El número de registros en el DataFrame antes de eliminar REPEP: {len(df_clean)}')
                repep = len(df_clean[df_clean['FLG_REPEP'] == 'Y'])
                st.write(f'El número de registros REPEP es de: {repep}')
                df_clean = df_clean[df_clean['FLG_REPEP'] != 'Y']
                st.write(f'El número de registros en el DataFrame después de eliminar REPEP: {len(df_clean)}')
                st.write()
            else:
                st.write("Error: La columna 'FLG_REPEP' no existe en el DataFrame.")
            
            # Guardar resultados
            st.write("**SECCIÓN DE CORREOS ELIMINADOS POR REGEX**")
            st.write(f"Número de correos eliminados por patrones no deseados: {len(correos_eliminados)}")
            st.write()
            
            return df_clean, pd.DataFrame(correos_eliminados, columns=['Correo Eliminado'])
        
        # Definir las expresiones regulares para palabras no deseadas
        wrong_words_regex = [
            r'@@', r'\.\.', r'\.com@', r'[\+\&:,"\' ]', r'ñ', r'^[._\W]', r'\.$', r'@.*@', r'^[^@]*$',
            r'gm?ial|gnial|dumy|notene', r'@(yopmail)', r'(dummy|prueba|ejemplo|temporal)',
            r'\bcorreoprueba\b', r'\b(?:no[_.-]?tiene|sin[_.-]?correo|no[_.-]?tengo|no[_.-]?existe|no[_.-]?cuenta(?:con)?correo)\b',
            r'\b(?:no[_.-]?aplica|no[_.-]?maneja[_.-]?correo|no[_.-]?brinda|no[_.-]?asigna[_.-]?correo)\b',
            r'\b(?:no[_.-]?se[_.-]?lo[_.-]?sabe|no[_.-]?da|no[_.-]?desea|no[_.-]?dejo)\b',
            r'^(1\.21|1212|1122|121|12.1|1\.2)', r'^(618)', r'^(123|1234|12345)@', r'^[zZ]+@',
            r'^(sinusuario|demientras|notengo|virtual|facturas[-_]?izzi|cliente(?:nuevo|izzi)|izzi|aaa|om|lacasadelbrujo|nohaycorreo|ninguno|001)@.*$',
            r'^(manololo|sinmail|n|ngonzalez|generico|atencionalcliente|izzigenerico|p-ngonzalezg|a.empresarial)@.*$',
            r'^(ventas\d+clientes|xxx|generico\d+)@.*$', r'^(jesus|jose)@.*$|^sincorreo\d+@.*$',
            r'^(correo|123456|sin.correo|no.se.lo.sabe|wizzgenerico)@.*$', r'^(abc|abc123|atc|sincontacto|iz.z.ot.el.e)@.*$',
            r'[\w.-]*no[_.-]?tiene[\w.-]*@[\w.-]*', r'@no[_.-]?tiene[\w.-]*',
            r'^(nocuenta[\w-]+|nodejo[\w-]+|noda[\w-]+|nodesea[\w-]+)@', r'^(0+|1)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            r"^[a-zA-Z0-9]{1,2}@[\w.-]+\.[a-zA-Z]{2,}$",
        ]
        
        # Procesar el archivo
        df_clean, correos_eliminados = limpiar_correos(df, wrong_words_regex)
        
        # Mostrar el resultado
        st.write("Archivo procesado con éxito!")
        
        # Permitir la descarga del archivo limpio
        output_csv = df_clean.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar archivo limpio",
            data=output_csv,
            file_name='archivo_limpio.csv',
            mime='text/csv',
        )
        
        # Permitir la descarga del archivo con correos eliminados
        correos_eliminados_csv = correos_eliminados.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar correos eliminados",
            data=correos_eliminados_csv,
            file_name='correos_eliminados.csv',
            mime='text/csv',
        )
        
        st.success("✅ Proceso completado")