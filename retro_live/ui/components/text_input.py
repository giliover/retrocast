"""Bounded single-line text editing and theme-aware caret rendering."""

class TextCursor:
    def __init__(self):
        self.position = 0
        self.selected = False

    def reset(self, text):
        self.position = len(text)
        self.selected = False

    def edit(self, text, command, value='', limit=2048):
        pos = min(self.position, len(text))
        if command == 'all':
            self.selected = True
            self.position = len(text)
            return text
        if command in ('left', 'right', 'home', 'end'):
            self.position = {'left': 0 if self.selected else max(0,pos-1),
                             'right': len(text) if self.selected else min(len(text),pos+1),
                             'home': 0, 'end': len(text)}[command]
            self.selected = False
            return text
        if command == 'clear' or (self.selected and command in ('backspace','delete')):
            self.reset('')
            return ''
        if command == 'insert':
            start, end = (0,len(text)) if self.selected else (pos,pos)
            value = ''.join(c for c in value[:limit] if c.isprintable())
            value = value[:max(0,limit-len(text)+end-start)]
            if not value: return text
            text = text[:start]+value+text[end:]
            pos = start+len(value)
        elif command == 'backspace' and pos:
            text = text[:pos-1]+text[pos:]; pos -= 1
        elif command == 'delete':
            text = text[:pos]+text[pos+1:]
        self.position = pos
        self.selected = False
        return text

    def viewport(self, text, columns):
        pos = min(self.position,len(text))
        start = max(0,pos-max(1,columns)+1)
        return text[start:start+columns], pos-start


class TextInputMixin:
    def draw_text_input(self, box, value, cursor, active, hint='', prefix=''):
        import pygame
        self.rect(box,self.palette.black,self.palette.accent if active else self.palette.edge)
        font=self.small
        x=box.x+8; y=box.y+6
        if prefix:
            self.txt(prefix,x,y,self.palette.muted,font,maxwidth=box.width//2)
            x+=min(font.size(prefix)[0]+6,box.width//2)
        width=max(1,box.right-x-8)
        columns=max(1,width//max(1,font.size('M')[0]))
        previous=self.screen.get_clip()
        self.screen.set_clip(previous.clip(pygame.Rect(x,box.y,width,box.height)))
        if active:
            visible, offset=cursor.viewport(value,columns)
        else:
            visible,offset=value[-columns:],0
        if active and cursor.selected and value:
            pygame.draw.rect(self.screen,self.palette.accent,(x,y,font.size(visible)[0],font.get_height()))
        self.txt(visible or (hint if not active else ''),x,y,self.palette.black if active and cursor.selected and value else self.palette.text if value else self.palette.muted,font)
        if active:
            caret=x+font.size(visible[:offset])[0]
            pygame.draw.line(self.screen,self.palette.accent,(min(caret,box.right-9),y),(min(caret,box.right-9),y+font.get_height()),2)
        self.screen.set_clip(previous)
