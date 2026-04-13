if "etapa_diagnostico" not in st.session_state:
    st.session_state.etapa_diagnostico = 0

st.markdown("""
👋 Bienvenido/a. Antes de iniciar una conversación te invito a realizar dos diagnosticos, los cuales me permitiran enfocarme más en tí, no tardará más de 5 minutos

👉 Por favor, responde con sinceridad. Empezaremos por la **evaluación de depresión** (PHQ-9):
""")

if st.session_state.etapa_diagnostico >= 0:
    with st.expander("📝 Realizar Diagnóstico de Depresión (PHQ-9)"):
        st.markdown("Por favor, responde las siguientes preguntas según cómo te has sentido en las **últimas dos semanas**:")

        phq9_respuestas={}
        phq9_preguntas = {
            "1": "Poco interés o placer en hacer cosas",
            "2": "Sentirse decaído, deprimido o sin esperanzas",
            "3": "Dificultad para conciliar el sueño, permanecer dormido o dormir demasiado",
            "4": "Sentirse cansado o con poca energía",
            "5": "Falta de apetito o comer en exceso",
            "6": "Sentirse mal consigo mismo — o que es un fracaso o que ha quedado mal consigo mismo o con su familia",
            "7": "Dificultad para concentrarse en cosas, como leer el periódico o ver la televisión",
            "8": "Moverse o hablar tan despacio que otras personas lo podrían notar. O lo contrario — estar tan inquieto o agitado que se ha estado moviendo mucho más de lo habitual",
            "9": "Pensamientos de que estaría mejor muerto o de hacerse daño de alguna manera"
        }

        opciones = ["Nada en absoluto ", "Varios días ", "Más de la mitad de los días ", "Casi todos los días "]
        puntaje_total=0


        
        for i, pregunta in phq9_preguntas.items():
            respuesta = st.radio(pregunta, opciones, key=i)
            puntaje = opciones.index(respuesta)
            phq9_respuestas[i] = respuesta
            puntaje_total += puntaje

        if st.button("📊 Calcular Resultado"):
            st.session_state.etapa_diagnostico = 1  # Avanzar a la siguiente etapa




if st.session_state.etapa_diagnostico >= 1:

    if puntaje_total <= 4:
        phq9 = "Depresión mínima o inexistente."
        st.success("Depresión mínima o inexistente.")
    elif puntaje_total <= 9:
        phq9 = "Depresión leve."
        st.info("Depresión leve.")
    elif puntaje_total <= 14:
        phq9 = "Depresión moderada."
        st.warning("Depresión moderada.")
    elif puntaje_total <= 19:
        phq9 = "Depresión moderadamente severa."
        st.warning("Depresión moderadamente severa.")
    else:
        phq9 = "Depresión severa. Sería recomendable consultar a un profesional de salud mental."
        st.error("Depresión severa. Sería recomendable consultar a un profesional de salud mental.")
        

    st.markdown("""

👉 Ahora iniciaremos la evaluación de riesgo de suicidio ASQ:
""")

    with st.expander("📝 Herramienta para la Detección del Riesgo de Suicidio (ASQ - NIMH)"):
        st.markdown("Por favor, responde con sinceridad. Esta herramienta busca identificar si existe algún riesgo de suicidio.")

        asq_respuestas = {}
        asq_preguntas = {
            "asq_1": "1. En las últimas semanas, ¿ha deseado estar muerto?",
            "asq_2": "2. En las últimas semanas, ¿ha sentido que usted o su familia estarían mejor si estuviera muerto?",
            "asq_3": "3. En la última semana, ¿ha estado pensando en suicidarse?",
            "asq_4": "4. ¿Alguna vez ha intentado suicidarse?",
        }

        opciones_asq = ["No","Sí"]
        riesgo_positivo = False
        for key, pregunta in asq_preguntas.items():
            respuesta = st.radio(pregunta, opciones_asq, key=key)
            asq_respuestas[key] = respuesta
            if respuesta == "Sí":
                riesgo_positivo = True

        if riesgo_positivo:
            respuesta_5 = st.radio("5. ¿Está pensando en suicidarse en este momento?", opciones_asq, key="asq_5")
            asq_respuestas["asq_5"] = respuesta_5
        else:
            respuesta_5 = "No"

        if st.button("📊 Evaluar Riesgo de Suicidio"):
            st.session_state.etapa_diagnostico = 2


# Botón para reiniciar conversación

if st.session_state.etapa_diagnostico >= 2:

    if not riesgo_positivo:
        st.success("✅ Evaluación negativa: no se identifica riesgo de suicidio.")
        asq_resultado = "negativo"
    elif riesgo_positivo and respuesta_5 == "Sí":
        st.error("⚠️ Riesgo agudo identificado. Se requiere evaluación de seguridad URGENTE.")
        asq_resultado = "positivo_agudo"
    elif riesgo_positivo and respuesta_5 == "No":
        st.warning("⚠️ Riesgo no agudo identificado. Se requiere evaluación de seguridad.")
        asq_resultado = "positivo_no_agudo"

    if st.button("🗑️ Nueva Conversación"):
        st.session_state.chat_history = []
        st.session_state.store = {}

        for i in ["1", "2", "3", "4", "5" ,"6", "7", "8", "9"]:
            st.session_state.pop(i, None)

        for key in ["asq_1", "asq_2", "asq_3", "asq_4", "asq_5"]:
            st.session_state.pop(key, None)
    
        st.session_state.etapa_diagnostico = 0

        st.rerun()