import math
from PIL import Image, ImageDraw, ImageOps

from ..utils import asset_path, inter_font


class TimerCard:
    scale = 2

    background = Image.open(asset_path("timer/background.png")).convert('RGBA')
    main_colour: str

    header_field_height = 343
    header_font = inter_font('ExtraBold', size=int(scale*76))

    inner_margin = 80
    inner_sep = 15

    # Timer section
    # Outer progress bar
    progress_end: Image
    progress_start: Image
    progress_bg = Image.open(asset_path("timer/break_timer.png")).convert('RGBA')
    progress_mask = ImageOps.invert(progress_bg.split()[-1].convert('L'))

    timer_bg = Image.open(asset_path("timer/timer_bg.png")).convert('RGBA')

    # Inner timer text
    countdown_font = inter_font('Light', size=int(scale*112))
    countdown_gap = int(scale * 10)
    stage_font = inter_font('Light', size=int(scale*43.65))
    stage_colour = '#FFFFFF'

    mic_icon: Image
    stage_text: str

    # Members
    user_bg = Image.open(asset_path("timer/break_user.png")).convert('RGBA')
    user_mask = Image.open(asset_path("timer/avatar_mask.png")).convert('RGBA')

    time_font = inter_font('Black', size=int(scale*26))
    time_colour = '#FFFFFF'

    tag_gap = 11
    tag: Image
    tag_font = inter_font('SemiBold', size=int(scale*25))

    # grid_x = (background.width - progress_mask.width - 2 * progress_end.width - grid_start[0] - user_bg.width) // 4
    grid_x = 344
    grid_y = 246

    # Date text
    date_font = inter_font('Bold', size=int(scale * 28))
    date_colour = '#6f6e6f'
    date_gap = int(scale * 50)

    def __init__(self, name, remaining, duration, users):
        self.data_name = name
        self.data_remaining = 5 * math.ceil(remaining / 5)
        self.data_duration = duration
        self.data_amount = 1 - remaining / duration
        self.data_users = sorted(users[:25], key=lambda user: user[1], reverse=True)  # (avatar, time)

    @staticmethod
    def format_time(time, hours=True):
        if hours:
            return "{:02}:{:02}".format(int(time // 3600), int((time // 60) % 60))
        else:
            return "{:02}:{:02}".format(int(time // 60), int(time % 60))

    def draw(self):
        image = self.background.copy()
        draw = ImageDraw.Draw(image)

        # Draw header
        text = self.data_name
        length = self.header_font.getlength(text)
        draw.text(
            (image.width // 2, self.header_field_height // 2),
            text,
            fill=self.main_colour,
            font=self.header_font,
            anchor='mm'
        )

        # Draw timer
        timer_image = self._draw_progress_bar(self.data_amount)
        ypos = timer_y = (
            self.header_field_height
            + (image.height - self.header_field_height - timer_image.height) // 2
            - self.progress_end.height // 2
        )
        xpos = timer_x = image.width - self.inner_margin - timer_image.width

        image.alpha_composite(
            timer_image,
            (xpos, ypos)
        )

        # Draw timer text
        stage_size = self.stage_font.getsize(' ' + self.stage_text)

        ypos += timer_image.height // 2 - stage_size[1] // 2
        xpos += timer_image.width // 2
        draw.text(
            (xpos, ypos),
            (text := self.format_time(self.data_remaining)),
            fill=self.main_colour,
            font=self.countdown_font,
            anchor='mm'
        )

        size = int(self.countdown_font.getsize(text)[1])
        ypos += size

        self.mic_icon.thumbnail((stage_size[1], stage_size[1]))
        length = int(self.mic_icon.width + self.stage_font.getlength(' ' + self.stage_text))
        xpos -= length // 2

        image.alpha_composite(
            self.mic_icon,
            (xpos, ypos - self.mic_icon.height)
        )
        draw.text(
            (xpos + self.mic_icon.width, ypos),
            ' ' + self.stage_text,
            fill=self.stage_colour,
            font=self.stage_font,
            anchor='ls'
        )

        # Draw user grid
        if self.data_users:
            grid_image = self.draw_user_grid()

            # ypos = self.header_field_height + (image.height - self.header_field_height - grid_image.height) // 2
            ypos = timer_y + (timer_image.height - grid_image.height) // 2 - stage_size[1] // 2
            xpos = (
                self.inner_margin
                + (timer_x - self.inner_sep - self.inner_margin) // 2
                - grid_image.width // 2
            )

            image.alpha_composite(
                grid_image,
                (xpos, ypos)
            )

        # Draw the footer
        ypos = image.height
        ypos -= self.date_gap
        date_text = "Use !now [text] to show what you are working on!"
        size = self.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.date_font,
            fill=self.date_colour
        )
        return image

    def draw_user_grid(self) -> Image:
        users = self.data_users

        # Set these to 5 and 5 to force top left corner
        rows = math.ceil(len(users) / 5)
        columns = 5
        # columns = min(len(users), 5)

        size = (
            (columns - 1) * self.grid_x + self.user_bg.width,
            (rows - 1) * self.grid_y + self.user_bg.height + self.tag_gap + self.tag.height
        )

        image = Image.new(
            'RGBA',
            size
        )
        for i, user in enumerate(users):
            x = (i % 5) * self.grid_x
            y = (i // 5) * self.grid_y

            user_image = self.draw_user(user)
            image.alpha_composite(
                user_image,
                (x, y)
            )
        return image

    def draw_user(self, user):
        width = self.user_bg.width
        height = self.user_bg.height + self.tag_gap + self.tag.height
        image = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(image)

        image.alpha_composite(self.user_bg)

        avatar, time, tag = user
        avatar = avatar.copy()
        timestr = self.format_time(time, hours=True)

        # Mask avatar
        avatar.paste((0, 0, 0, 0), mask=self.user_mask)

        # Resize avatar
        avatar.thumbnail((self.user_bg.height - 10, self.user_bg.height - 10))

        image.alpha_composite(
            avatar,
            (5, 5)
        )
        draw.text(
            (120, self.user_bg.height // 2),
            timestr,
            anchor='lm',
            font=self.time_font,
            fill=self.time_colour
        )

        if tag:
            ypos = self.user_bg.height + self.tag_gap
            image.alpha_composite(
                self.tag,
                ((image.width - self.tag.width) // 2, ypos)
            )
            draw.text(
                (image.width // 2, ypos + self.tag.height // 2),
                tag,
                font=self.tag_font,
                fill='#FFFFFF',
                anchor='mm'
            )
        return image

    def _draw_progress_bar(self, amount):
        amount = min(amount, 1)
        amount = max(amount, 0)
        bg = self.timer_bg
        end = self.progress_start
        mask = self.progress_mask

        center = (
            bg.width // 2 + 1,
            bg.height // 2
        )
        radius = 553
        theta = amount * math.pi * 2 - math.pi / 2
        x = int(center[0] + radius * math.cos(theta))
        y = int(center[1] + radius * math.sin(theta))

        canvas = Image.new('RGBA', size=(bg.width, bg.height))
        draw = ImageDraw.Draw(canvas)

        if amount >= 0.01:
            canvas.alpha_composite(
                end,
                (
                    center[0] - end.width // 2,
                    26 - end.height // 2
                )
            )

            sidelength = bg.width // 2
            line_ends = (
                int(center[0] + sidelength * math.cos(theta)),
                int(center[1] + sidelength * math.sin(theta))
            )
            if amount <= 0.25:
                path = [
                    center,
                    (center[0], center[1] - sidelength),
                    (bg.width, 0),
                    line_ends
                ]
            elif amount <= 0.5:
                path = [
                    center,
                    (center[0], center[1] - sidelength),
                    (bg.width, 0),
                    (bg.width, bg.height),
                    line_ends
                ]
            elif amount <= 0.75:
                path = [
                    center,
                    (center[0], center[1] - sidelength),
                    (bg.width, 0),
                    (bg.width, bg.height),
                    (0, bg.height),
                    line_ends
                ]
            else:
                path = [
                    center,
                    (center[0], center[1] - sidelength),
                    (bg.width, 0),
                    (bg.width, bg.height),
                    (0, bg.height),
                    (0, 0),
                    line_ends
                ]

            draw.polygon(
                path,
                fill=self.main_colour
            )

            canvas.paste((0, 0, 0, 0), mask=mask)

        image = Image.new(
            'RGBA',
            size=(bg.width + self.progress_end.width,
                  bg.height + self.progress_end.height)
        )
        image.alpha_composite(
            bg,
            (self.progress_end.width // 2,
             self.progress_end.height // 2)
        )
        image.alpha_composite(
            canvas,
            (self.progress_end.width // 2,
             self.progress_end.height // 2)
        )

        image.alpha_composite(
            self.progress_end,
            (
                x,
                y
            )
        )

        return image


class FocusTimerCard(TimerCard):
    main_colour = '#DDB21D'
    user_bg = Image.open(asset_path("timer/focus_user.png")).convert('RGBA')
    mic_icon = Image.open(asset_path("timer/mute.png")).convert('RGBA')
    progress_end = Image.open(asset_path("timer/progress_end_focus.png")).convert('RGBA')
    progress_start = Image.open(asset_path("timer/progress_start_focus.png")).convert('RGBA')
    stage_text = "FOCUS"
    tag = Image.open(asset_path("timer/focus_tag.png")).convert("RGBA")


class BreakTimerCard(TimerCard):
    main_colour = '#78B7EF'
    user_bg = Image.open(asset_path("timer/break_user.png")).convert('RGBA')
    mic_icon = Image.open(asset_path("timer/unmute.png")).convert('RGBA')
    progress_end = Image.open(asset_path("timer/progress_end_break.png")).convert('RGBA')
    progress_start = Image.open(asset_path("timer/progress_start_break.png")).convert('RGBA')
    stage_text = "BREAK"
    tag = Image.open(asset_path("timer/break_tag.png")).convert("RGBA")
