"""Autocomplete local para Twitch/YouTube; sem API nem consulta remota."""
from dataclasses import dataclass
from urllib.parse import urlparse
import re

@dataclass(frozen=True)
class Suggestion:
    label: str
    url: str
    detail: str

PREFIXES = (
    ('TWITCH', 'https://www.twitch.tv/'),
    ('YOUTUBE', 'https://www.youtube.com/watch?v='),
    ('YT LIVE', 'https://www.youtube.com/live/'),
    ('YT CANAL', 'https://www.youtube.com/@'),
)

def normalize_source(value: str) -> str:
    raw = value.strip()
    if not raw: return ''
    if raw.startswith('@'): return 'https://www.twitch.tv/' + raw[1:]
    if re.fullmatch(r'[\w-]{1,50}', raw) and raw.lower() not in ('twitch', 'youtube', 'youtu', 'www'):
        return 'https://www.twitch.tv/' + raw
    for prefix, domain in (('twitch/', 'https://www.twitch.tv/'), ('twitch:', 'https://www.twitch.tv/'), ('youtube/', 'https://www.youtube.com/'), ('youtube:', 'https://www.youtube.com/')):
        if raw.lower().startswith(prefix): return domain + raw[len(prefix):].lstrip('/')
    if raw.startswith('//'): raw = 'https:' + raw
    if '://' not in raw: raw = 'https://' + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('URL invalida')
    return raw

def suggest(value: str, history=()) -> list[Suggestion]:
    q=value.strip(); low=q.lower(); result=[]; seen=set()
    def add(label,url,detail):
        if url not in seen:
            result.append(Suggestion(label,url,detail)); seen.add(url)
    for url in reversed(tuple(history)):
        if not q or low in url.lower(): add('RECENTE',url,'Historico')
    if not q:
        for label,url in PREFIXES: add(label,url,'Dominio')
    else:
        for label,url in PREFIXES:
            if low in label.lower() or url.lower().startswith(low) or low in ('t','tw','twi','y','yo','you','yt'):
                add(label,url,'Completar dominio')
        if re.fullmatch(r'@[\w-]*',q) or re.fullmatch(r'[\w-]+',q):
            if low not in ('twitch','youtube','youtu','www','yt'):
                add('TWITCH CANAL','https://www.twitch.tv/'+q.lstrip('@'),'Canal')
        for label,base in PREFIXES:
            if low.startswith(base.lower()) and len(q)>len(base):
                add(label,q,'URL digitada')
    return result
