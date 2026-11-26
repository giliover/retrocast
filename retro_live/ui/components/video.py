import pygame
from .loading import draw_whisper_loading
from ...performance import measure


class VideoMixin:
    def toggle_video_fullscreen(self):
        """Fullscreen video-only mode, preserving the previous window dimensions."""
        if not self.video_fullscreen:
            self._window_size=self.screen.get_size()
            self.screen=pygame.display.set_mode((0,0),pygame.FULLSCREEN)
            self.video_fullscreen=True
        else:
            self.screen=pygame.display.set_mode(self._window_size,pygame.RESIZABLE)
            self.video_fullscreen=False
        self._scaled_frame_key=None
        self._scaled_frame=None
        self.buttons.clear()


    def draw_fullscreen_video(self):
        w,h=self.screen.get_size()
        self.screen.fill(self.palette.black)
        if self.frame:
            fw,fh=self.frame.get_size()
            scale=min(w/fw,h/fh)
            target=(max(1,int(fw*scale)),max(1,int(fh*scale)))
            key=(id(self.frame),target)
            if key!=self._scaled_frame_key:
                with measure('ui.video_scale'):
                    self._scaled_frame=pygame.transform.smoothscale(self.frame,target)
                self._scaled_frame_key=key
            self.screen.blit(self._scaled_frame,self._scaled_frame.get_rect(center=(w//2,h//2)))
        else:
            self.txt(self.tr('nosignal'),max(20,w//2-80),h//2,self.palette.accent,self.large)
        if self.subtitle and self.session.caption:
            last=self.session.caption
            lines=self.wrap(last,max(100,w-120),self.font)[-3:]
            line_height=28
            box_h=len(lines)*line_height+20
            box=pygame.Surface((max(1,w-80),box_h),pygame.SRCALPHA)
            box.fill((8,12,17,220))
            self.screen.blit(box,(40,h-box_h-35))
            for i,line in enumerate(lines):
                rendered=self.font.render(line,True,self.palette.text)
                self.screen.blit(rendered,rendered.get_rect(centerx=w//2,y=h-box_h-25+i*line_height))
        draw_whisper_loading(self, self.screen.get_rect())
        pygame.display.flip()


    def draw_video_region(self, video):
        self.rect(video,self.palette.black)
        if self.frame:
            fw,fh=self.frame.get_size()
            scale=min((video.width-4)/fw,(video.height-4)/fh)
            target=(max(1,int(fw*scale)),max(1,int(fh*scale)))
            key=(id(self.frame), target)
            if key != self._scaled_frame_key:
                with measure('ui.video_scale'):
                    self._scaled_frame=pygame.transform.smoothscale(self.frame,target)
                self._scaled_frame_key=key
            self.screen.blit(self._scaled_frame,self._scaled_frame.get_rect(center=video.center))
        else:
            self.txt('[ '+self.tr('nosignal')+' ]',video.centerx-100,video.centery-25,self.palette.accent,self.large)
            self.txt('> '+self.tr('waiting'),video.centerx-115,video.centery+13,self.palette.muted,self.small)
        # Subtitles are drawn over video, including semi-transparent backing.
        if self.subtitle and self.session.caption:
            last=self.session.caption
            subtitle_lines=self.wrap(last,video.width-75,self.font)[-3:]
            sh=18+len(subtitle_lines)*24
            surf=pygame.Surface((video.width-28,sh),pygame.SRCALPHA)
            surf.fill((8,12,17,220))
            self.screen.blit(surf,(video.x+14,video.bottom-sh-18))
            for i,line in enumerate(subtitle_lines):
                render=self.font.render(line,True,self.palette.text)
                self.screen.blit(render,render.get_rect(centerx=video.centerx,y=video.bottom-sh-10+i*24))


        draw_whisper_loading(self, video)
