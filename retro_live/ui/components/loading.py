"""Bounded spinner overlay, independent of the audio/video clock."""
import math
import time
import pygame


def draw_whisper_loading(ui, region):
    v = ui.session.video
    if not (ui.session.running and ui.subtitle and v.whisper_waiting):
        return
    x, y = region.center
    width = min(310, region.width-8)
    if width < 40 or region.height < 90:
        return
    box = pygame.Rect(0, 0, width, 88)
    box.center = (x,y)
    ui.rect(box, ui.palette.black, ui.palette.edge)
    tick = int(time.monotonic()*10)%12
    for i in range(12):
        angle = i*math.tau/12
        color = ui.palette.accent if (i-tick)%12 < 3 else ui.palette.edge
        pygame.draw.circle(ui.screen,color,(x+int(15*math.cos(angle)),y-20+int(15*math.sin(angle))),3)
    ui.txt(ui.tr('whisper_wait'),box.x+10,y+3,ui.palette.text,ui.small,maxwidth=width-20)
    policy = v.ai_policy or v.whisper_policy
    ui.txt(f"{ui.tr('attempt')}: {v.ai_attempt or '-'} | WAIT: {policy.timeout}s",box.x+10,y+23,ui.palette.muted,ui.tiny,maxwidth=width-20)
