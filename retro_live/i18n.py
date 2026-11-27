"""Application language only; Whisper speech language remains independent."""
LANGUAGES=("pt", "en", "es")
MESSAGES={
 "pt": {"fullscreen":"TELA CHEIA", "history":"HISTÓRICO DE LINKS", "close":"FECHAR", "title":"TRANSMISSÃO / TRANSCRIÇÃO AO VIVO", "source":"FONTE", "watch":"ASSISTIR", "stop":"PARAR", "save":"SALVAR", "transcript":"TRANSCRIÇÃO / AO VIVO", "nosignal":"SEM SINAL", "waiting":"AGUARDANDO TRANSMISSÃO...", "pause":"PAUSAR", "sub_on":"LEGENDA ON", "sub_off":"LEGENDA OFF", "model":"MODELO", "speech":"ÁUDIO", "theme":"TEMA", "ui_lang":"IDIOMA UI", "ready":"DIGITE TWITCH / YOUTUBE / @CANAL | TAB AUTOCOMPLETA", "hint":"[TAB] COMPLETAR  [ENTER] ASSISTIR  [ESPAÇO] PAUSAR  [S] SALVAR  [T] TEMA  [I] IDIOMA UI  [ESC] SAIR", "changed_model":"MODELO ALTERADO (PRÓXIMA LIVE)", "changed_speech":"IDIOMA DO ÁUDIO ALTERADO (PRÓXIMA LIVE)"},
 "en": {"fullscreen":"FULLSCREEN", "history":"LINK HISTORY", "close":"CLOSE", "title":"STREAM / LIVE TRANSCRIPTION", "source":"SOURCE", "watch":"WATCH", "stop":"STOP", "save":"SAVE", "transcript":"TRANSCRIPT / LIVE", "nosignal":"NO SIGNAL", "waiting":"WAITING FOR STREAM...", "pause":"PAUSE", "sub_on":"CAPTIONS ON", "sub_off":"CAPTIONS OFF", "model":"MODEL", "speech":"SPEECH", "theme":"THEME", "ui_lang":"UI LANG", "ready":"TYPE TWITCH / YOUTUBE / @CHANNEL | TAB AUTOCOMPLETE", "hint":"[TAB] COMPLETE  [ENTER] WATCH  [SPACE] PAUSE  [S] SAVE  [T] THEME  [I] UI LANGUAGE  [ESC] EXIT", "changed_model":"MODEL CHANGED (NEXT STREAM)", "changed_speech":"SPEECH LANGUAGE CHANGED (NEXT STREAM)"},
 "es": {"fullscreen":"PANTALLA COMPLETA", "history":"HISTORIAL DE ENLACES", "close":"CERRAR", "title":"DIRECTO / TRANSCRIPCIÓN EN VIVO", "source":"FUENTE", "watch":"VER", "stop":"PARAR", "save":"GUARDAR", "transcript":"TRANSCRIPCIÓN / EN VIVO", "nosignal":"SIN SEÑAL", "waiting":"ESPERANDO TRANSMISIÓN...", "pause":"PAUSA", "sub_on":"SUBTÍTULOS ON", "sub_off":"SUBTÍTULOS OFF", "model":"MODELO", "speech":"AUDIO", "theme":"TEMA", "ui_lang":"IDIOMA UI", "ready":"ESCRIBE TWITCH / YOUTUBE / @CANAL | TAB COMPLETA", "hint":"[TAB] COMPLETAR  [ENTER] VER  [ESPACIO] PAUSA  [S] GUARDAR  [T] TEMA  [I] IDIOMA UI  [ESC] SALIR", "changed_model":"MODELO CAMBIADO (PRÓXIMO DIRECTO)", "changed_speech":"IDIOMA DEL AUDIO CAMBIADO (PRÓXIMO DIRECTO)"}
}
def translate(language: str, key: str) -> str:
    return MESSAGES.get(language, MESSAGES["en"]).get(key,key)
def next_language(language: str) -> str:
    return LANGUAGES[(LANGUAGES.index(language)+1)%len(LANGUAGES)] if language in LANGUAGES else LANGUAGES[0]

MESSAGES["pt"].update(priority="PRIORIDADE", balanced="BALANCEADO", video="VÍDEO", subtitle="LEGENDA")
MESSAGES["en"].update(priority="PRIORITY", balanced="BALANCED", video="VIDEO", subtitle="SUBTITLE")
MESSAGES["es"].update(priority="PRIORIDAD", balanced="EQUILIBRADO", video="VÍDEO", subtitle="SUBTÍTULO")

MESSAGES["pt"].update(resume="RETOMAR", retries="RETENT.", timeout="LIMITE", whisper_wait="AGUARDANDO WHISPER", attempt="TENTATIVA")
MESSAGES["en"].update(resume="RESUME", retries="RETRIES", timeout="TIMEOUT", whisper_wait="WAITING FOR WHISPER", attempt="ATTEMPT")
MESSAGES["es"].update(resume="CONTINUAR", retries="REINT.", timeout="LÍMITE", whisper_wait="ESPERANDO WHISPER", attempt="INTENTO")

# Shared UI vocabulary.
MESSAGES['pt'].update({'help': 'AJUDA', 'shortcuts': 'ATALHOS DE TECLADO', 'performance': 'DESEMPENHO', 'live': 'AO VIVO', 'standby': 'EM ESPERA', 'hold': 'HISTÓRICO', 'playing': 'REPRODUZINDO', 'paused': 'PAUSADO', 'buffer': 'BUFFER', 'retries': 'RETENTATIVAS', 'timeout': 'TEMPO DE ESPERA', 'auto': 'AUTO', 'off': 'DESATIVADO', 'on': 'ATIVADO', 'volume': 'VOLUME', 'quality': 'QUALIDADE', 'autocomplete': 'AUTOCOMPLETAR', 'exit': 'SAIR', 'select': 'SELECIONAR', 'open': 'ABRIR', 'page': 'PÁGINA', 'edit_source': 'EDITAR FONTE', 'paste': 'COLAR URL', 'fps': 'FPS', 'fps_adjust': 'AJUSTAR FPS', 'buffer_adjust': 'AJUSTAR BUFFER', 'timeout_adjust': 'AJUSTAR TEMPO DE ESPERA', 'navigate': 'NAVEGAR TRANSCRIÇÃO', 'return_live': 'VOLTAR AO VIVO', 'clipboard': 'ÁREA DE TRANSFERÊNCIA INDISPONÍVEL', 'recent': 'RECENTE', 'channel': 'CANAL', 'stopped': 'PARADO', 'stopping': 'PARANDO...', 'ended': 'FINALIZADO', 'connecting': 'CONECTANDO...', 'insert_url': 'INSIRA UMA URL', 'saved': 'SALVO', 'error': 'ERRO', 'next_stream': 'PRÓXIMA TRANSMISSÃO', 'average': 'MÉDIA', 'maximum': 'MÁX', 'toggle_sub': 'LIGAR/DESLIGAR LEGENDAS E WHISPER', 'pause_resume': 'PAUSAR / RETOMAR', 'source_hint': 'twitch / youtube / @canal / URL', 'space': 'ESPAÇO', 'ui_lang': 'IDIOMA DA INTERFACE', 'phosphor': 'FÓSFORO', 'amber': 'ÂMBAR', 'cyan': 'CIANO', 'mono': 'MONOCROMÁTICO', 'sub_on': 'LEGENDA ATIVADA', 'sub_off': 'LEGENDA DESATIVADA'})
MESSAGES['en'].update({'help': 'HELP', 'shortcuts': 'KEYBOARD SHORTCUTS', 'performance': 'PERFORMANCE', 'live': 'LIVE', 'standby': 'STANDBY', 'hold': 'HOLD', 'playing': 'PLAYING', 'paused': 'PAUSED', 'buffer': 'BUFFER', 'retries': 'RETRIES', 'timeout': 'WAIT TIME', 'auto': 'AUTO', 'off': 'OFF', 'on': 'ON', 'volume': 'VOLUME', 'quality': 'QUALITY', 'autocomplete': 'AUTOCOMPLETE', 'exit': 'EXIT', 'select': 'SELECT', 'open': 'OPEN', 'page': 'PAGE', 'edit_source': 'EDIT SOURCE', 'paste': 'PASTE URL', 'fps': 'FPS', 'fps_adjust': 'ADJUST FPS', 'buffer_adjust': 'ADJUST BUFFER', 'timeout_adjust': 'ADJUST WAIT TIME', 'navigate': 'BROWSE TRANSCRIPT', 'return_live': 'RETURN TO LIVE', 'clipboard': 'CLIPBOARD UNAVAILABLE', 'recent': 'RECENT', 'channel': 'CHANNEL', 'stopped': 'STOPPED', 'stopping': 'STOPPING...', 'ended': 'ENDED', 'connecting': 'CONNECTING...', 'insert_url': 'ENTER A URL', 'saved': 'SAVED', 'error': 'ERROR', 'next_stream': 'NEXT STREAM', 'average': 'AVG', 'maximum': 'MAX', 'toggle_sub': 'TOGGLE CAPTIONS AND WHISPER', 'pause_resume': 'PAUSE / RESUME', 'source_hint': 'twitch / youtube / @channel / URL', 'space': 'SPACE', 'ui_lang': 'INTERFACE LANGUAGE', 'phosphor': 'PHOSPHOR', 'amber': 'AMBER', 'cyan': 'CYAN', 'mono': 'MONOCHROME', 'sub_on': 'CAPTIONS ON', 'sub_off': 'CAPTIONS OFF'})
MESSAGES['es'].update({'help': 'AYUDA', 'shortcuts': 'ATAJOS DE TECLADO', 'performance': 'RENDIMIENTO', 'live': 'EN VIVO', 'standby': 'EN ESPERA', 'hold': 'HISTORIAL', 'playing': 'REPRODUCIENDO', 'paused': 'PAUSADO', 'buffer': 'BÚFER', 'retries': 'REINTENTOS', 'timeout': 'TIEMPO DE ESPERA', 'auto': 'AUTO', 'off': 'DESACTIVADO', 'on': 'ACTIVADO', 'volume': 'VOLUMEN', 'quality': 'CALIDAD', 'autocomplete': 'AUTOCOMPLETAR', 'exit': 'SALIR', 'select': 'SELECCIONAR', 'open': 'ABRIR', 'page': 'PÁGINA', 'edit_source': 'EDITAR FUENTE', 'paste': 'PEGAR URL', 'fps': 'FPS', 'fps_adjust': 'AJUSTAR FPS', 'buffer_adjust': 'AJUSTAR BÚFER', 'timeout_adjust': 'AJUSTAR TIEMPO DE ESPERA', 'navigate': 'NAVEGAR TRANSCRIPCIÓN', 'return_live': 'VOLVER AL DIRECTO', 'clipboard': 'PORTAPAPELES NO DISPONIBLE', 'recent': 'RECIENTE', 'channel': 'CANAL', 'stopped': 'DETENIDO', 'stopping': 'DETENIENDO...', 'ended': 'FINALIZADO', 'connecting': 'CONECTANDO...', 'insert_url': 'INTRODUCE UNA URL', 'saved': 'GUARDADO', 'error': 'ERROR', 'next_stream': 'PRÓXIMO DIRECTO', 'average': 'MEDIA', 'maximum': 'MÁX', 'toggle_sub': 'ACTIVAR/DESACTIVAR SUBTÍTULOS Y WHISPER', 'pause_resume': 'PAUSAR / CONTINUAR', 'source_hint': 'twitch / youtube / @canal / URL', 'space': 'ESPACIO', 'ui_lang': 'IDIOMA DE INTERFAZ', 'phosphor': 'FÓSFORO', 'amber': 'ÁMBAR', 'cyan': 'CIAN', 'mono': 'MONOCROMÁTICO', 'sub_on': 'SUBTÍTULOS ACTIVADOS', 'sub_off': 'SUBTÍTULOS DESACTIVADOS'})

# Keep internal status codes/logs stable; translate at presentation time.
def translate_status(language, status):
    exact = {"PRONTO":"ready", "INSIRA UMA URL":"insert_url", "CONECTANDO...":"connecting", "ENDED":"ended", "STOPPED":"stopped", "STOPPING...":"stopping", "WAITING FOR WHISPER...":"whisper_wait"}
    if status in exact: return translate(language, exact[status])
    for key in ("changed_model", "changed_speech", "clipboard", "ready"):
        if any(status == messages[key] for messages in MESSAGES.values()):
            return translate(language, key)
    for prefix, key in (("ERRO: ", "error"), ("SALVO: ", "saved"), ("VIDEO: ", "video"), ("BUFFER: ", "buffer"), ("PLAYING | BUFFER ", "playing"), ("FRAME: ", "video")):
        if status.startswith(prefix):
            tail = status[len(prefix):].replace(" (next WATCH)", " ("+translate(language,"next_stream")+")")
            label = translate(language,key)
            if key == "playing": label += " | " + translate(language,"buffer")
            return label + ": " + tail
    return status

MESSAGES['pt'].update(history_online='DISPONÍVEL', history_offline='OFFLINE', history_checking='VERIFICANDO', history_unknown='SEM STATUS')
MESSAGES['en'].update(history_online='AVAILABLE', history_offline='OFFLINE', history_checking='CHECKING', history_unknown='UNKNOWN')
MESSAGES['es'].update(history_online='DISPONIBLE', history_offline='SIN CONEXIÓN', history_checking='COMPROBANDO', history_unknown='SIN ESTADO')

MESSAGES['pt'].update(history_sort='ORDENAR', history_sort_recent='MAIS RECENTES', history_sort_available='DISPONÍVEIS PRIMEIRO', history_sort_help='ALTERNAR ORDEM NO HISTÓRICO')
MESSAGES['en'].update(history_sort='SORT', history_sort_recent='MOST RECENT', history_sort_available='AVAILABLE FIRST', history_sort_help='TOGGLE HISTORY SORT ORDER')
MESSAGES['es'].update(history_sort='ORDENAR', history_sort_recent='MÁS RECIENTES', history_sort_available='DISPONIBLES PRIMERO', history_sort_help='CAMBIAR ORDEN DEL HISTORIAL')

MESSAGES["pt"].update(history_order_fixed="DISPONÍVEIS PRIMEIRO · MAIS RECENTES", history_search="PESQUISAR", history_empty="NENHUM LINK ENCONTRADO", history_search_help="PESQUISAR EM TODO O HISTÓRICO")
MESSAGES["en"].update(history_order_fixed="AVAILABLE FIRST · MOST RECENT", history_search="SEARCH", history_empty="NO LINKS FOUND", history_search_help="SEARCH ALL HISTORY")
MESSAGES["es"].update(history_order_fixed="DISPONIBLES PRIMERO · MÁS RECIENTES", history_search="BUSCAR", history_empty="NO SE ENCONTRARON ENLACES", history_search_help="BUSCAR EN TODO EL HISTORIAL")
