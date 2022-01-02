from datetime import datetime
from typing import List
from PIL import Image, ImageFont, ImageDraw
from ..utils import asset_path, inter_font


class Tasklist:
    scale = 2

    # First page
    first_page_bg = Image.open(asset_path("tasklist/first/bg.png")).convert('RGBA')
    first_page_frame = Image.open(asset_path("tasklist/first/frame.png")).convert('RGBA')

    title_pre_gap = int(scale * 40)
    title_text = "TO DO LIST"
    title_font = inter_font('ExtraBold', size=int(scale * 76))
    title_size = title_font.getsize(title_text)
    title_colour = '#DDB21D'
    title_underline_gap = int(scale * 10)
    title_underline_width = int(scale * 5)
    title_gap = int(scale * 50)

    profile_indent = int(scale * 125)
    profile_size = (
        first_page_bg.width - 2 * profile_indent,
        int(scale * 200)
    )

    avatar_mask = Image.open(asset_path("tasklist/first/avatar_mask.png"))
    avatar_frame = Image.open(asset_path("tasklist/first/avatar_frame.png"))
    avatar_sep = int(scale * 50)

    name_font = inter_font('BoldItalic', size=int(scale*55))
    name_colour = '#DDB21D'
    discrim_font = name_font
    discrim_colour = '#BABABA'
    name_gap = int(scale * 20)

    badge_end = Image.open(asset_path("tasklist/first/badge_end.png"))
    badge_font = inter_font('Black', size=int(scale*30))
    badge_colour = '#FFFFFF'
    badge_text_colour = '#051822'
    badge_gap = int(scale * 20)
    badge_min_sep = int(scale * 10)

    # Other pages
    other_page_bg = Image.open(asset_path("tasklist/other/bg.png")).convert('RGBA')
    other_page_frame = Image.open(asset_path("tasklist/other/frame.png")).convert('RGBA')

    # Tasks
    task_start_position = (100, 75)

    task_done_number_bg = Image.open(asset_path("tasklist/done.png")).convert('RGBA')
    task_done_number_font = inter_font('Regular', size=int(scale * 45))
    task_done_number_colour = '#292828'

    task_done_text_font = inter_font('Regular', size=int(scale * 55))
    task_done_text_colour = '#686868'

    task_done_line_width = 7

    task_undone_number_bg = Image.open(asset_path("tasklist/undone.png")).convert('RGBA')
    task_undone_number_font = inter_font('Regular', size=int(scale * 45))
    task_undone_number_colour = '#FFFFFF'

    task_undone_text_font = inter_font('Regular', size=int(scale * 55))
    task_undone_text_colour = '#FFFFFF'

    task_text_height = task_done_text_font.getsize('TASK')[1]
    task_num_sep = int(scale * 30)
    task_inter_gap = int(scale * 32)
    task_intra_gap = int(scale * 25)

    # Date text
    date_pre_gap = int(scale * 50)
    date_font = inter_font('Bold', size=int(scale * 28))
    date_colour = '#686868'
    date_gap = int(scale * 50)

    def __init__(self, name, discrim, avatar, tasks, date, badges=()):
        self.data_name = name
        self.data_discrim = discrim
        self.data_avatar = avatar.copy()
        self.data_tasks = tasks
        self.data_date = date
        self.data_badges = badges

        self.tasks_drawn = 0
        self.images = []

    def draw(self):
        self.images = []
        self.images.append(self._draw_first_page())
        while self.tasks_drawn < len(self.data_tasks):
            self.images.append(self._draw_another_page())

        return self.images

    def _draw_first_page(self) -> Image:
        image = self.first_page_bg.copy()
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw header text
        xpos = (image.width - self.title_size[0]) // 2
        ypos += self.title_pre_gap
        draw.text(
            (xpos, ypos),
            self.title_text,
            fill=self.title_colour,
            font=self.title_font
        )

        # Underline it
        ypos += self.title_size[1] + self.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + self.title_size[0], ypos),
            fill=self.title_colour,
            width=self.title_underline_width
        )
        ypos += self.title_underline_width + self.title_gap

        # Draw the profile
        xpos = self.profile_indent
        profile = self._draw_profile()
        image.alpha_composite(
            profile,
            (xpos, ypos)
        )

        # Start from the bottom
        ypos = image.height

        # Draw the date text
        ypos -= self.date_gap
        date_text = self.data_date.strftime("As of %d %b")
        size = self.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.date_font,
            fill=self.date_colour
        )
        ypos -= self.date_pre_gap

        # Draw the tasks
        task_image = self._draw_tasks_into(self.first_page_frame.copy())
        ypos -= task_image.height
        image.alpha_composite(
            task_image,
            ((image.width - task_image.width) // 2, ypos)
        )

        return image

    def _draw_profile(self) -> Image:
        image = Image.new('RGBA', self.profile_size)
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw avatar
        avatar = self.data_avatar
        avatar.paste((0, 0, 0, 0), mask=self.avatar_mask)
        avatar_image = Image.new('RGBA', (264, 264))
        avatar_image.paste(avatar, (3, 4))
        avatar_image.alpha_composite(self.avatar_frame)
        avatar_image = avatar_image.resize((self.profile_size[1], self.profile_size[1]))
        image.alpha_composite(avatar_image, (0, 0))

        xpos += avatar_image.width + self.avatar_sep

        # Draw name
        name_text = self.data_name
        name_length = self.name_font.getlength(name_text + ' ')
        name_height = self.name_font.getsize(name_text)[1]
        draw.text(
            (xpos, ypos),
            name_text,
            fill=self.name_colour,
            font=self.name_font
        )
        draw.text(
            (xpos + name_length, ypos),
            self.data_discrim,
            fill=self.discrim_colour,
            font=self.discrim_font
        )
        ypos += name_height + self.name_gap

        # Draw badges
        _x = 0
        max_x = self.profile_size[0] - xpos

        badges = [self._draw_badge(text) for text in self.data_badges]
        for badge in badges:
            if badge.width + _x > max_x:
                _x = 0
                ypos += badge.height + self.badge_gap
            image.paste(
                badge,
                (xpos + _x, ypos)
            )
            _x += badge.width + self.badge_min_sep
        return image

    def _draw_badge(self, text) -> Image:
        """
        Draw a single profile badge, with the given text.
        """
        text_length = self.badge_font.getsize(text)[0]

        height = self.badge_end.height
        width = text_length + self.badge_end.width

        badge = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))

        # Add blobs to ends
        badge.paste(
            self.badge_end,
            (0, 0)
        )
        badge.paste(
            self.badge_end,
            (width - self.badge_end.width, 0)
        )

        # Add rectangle to middle
        draw = ImageDraw.Draw(badge)
        draw.rectangle(
            (
                (self.badge_end.width // 2, 0),
                (width - self.badge_end.width // 2, height),
            ),
            fill=self.badge_colour,
            width=0
        )

        # Write badge text
        draw.text(
            (self.badge_end.width // 2, height // 2),
            text,
            font=self.badge_font,
            fill=self.badge_text_colour,
            anchor='lm'
        )

        return badge

    def _draw_another_page(self) -> Image:
        image = self.other_page_bg.copy()
        draw = ImageDraw.Draw(image)

        # Start from the bottom
        ypos = image.height

        # Draw the date text
        ypos -= self.date_gap
        date_text = self.data_date.strftime("As of %d %b • {} {}".format(self.data_name, self.data_discrim))
        size = self.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.date_font,
            fill=self.date_colour
        )
        ypos -= self.date_pre_gap

        # Draw the tasks
        task_image = self._draw_tasks_into(self.other_page_frame.copy())
        ypos -= task_image.height
        image.alpha_composite(
            task_image,
            ((image.width - task_image.width) // 2, ypos)
        )
        return image

    def _draw_tasks_into(self, image) -> Image:
        """
        Draw as many tasks as possible into the given image background.
        """
        draw = ImageDraw.Draw(image)
        xpos, ypos = self.task_start_position

        for n, task, done in self.data_tasks[self.tasks_drawn:]:
            # Draw task first to check if it fits on the page
            task_image = self._draw_text(
                task,
                image.width - xpos - self.task_done_number_bg.width - self.task_num_sep,
                done
            )
            if task_image.height + ypos > image.height:
                break

            # Draw number background
            bg = self.task_done_number_bg if done else self.task_undone_number_bg
            image.alpha_composite(
                bg,
                (xpos, ypos)
            )

            # Draw number
            font = self.task_done_number_font if done else self.task_undone_number_font
            colour = self.task_done_number_colour if done else self.task_undone_number_colour
            draw.text(
                (xpos + bg.width // 2, ypos + bg.height // 2),
                str(n),
                fill=colour,
                font=font,
                anchor='mm'
            )

            # Draw text
            image.alpha_composite(
                task_image,
                (xpos + bg.width + self.task_num_sep, ypos - (bg.height - self.task_text_height) // 2)
            )

            ypos += task_image.height + self.task_inter_gap
            self.tasks_drawn += 1

        return image

    def _draw_text(self, task, maxwidth, done) -> Image:
        """
        Draw the text of a given task.
        """
        font = self.task_done_text_font if done else self.task_undone_text_font
        colour = self.task_done_text_colour if done else self.task_undone_text_colour

        # First breakup the text
        lines = []
        line = []
        width = 0
        for word in task.split():
            length = font.getlength(word + ' ')
            if width + length > maxwidth:
                if line:
                    lines.append(' '.join(line))
                    line = []
                width = 0
            line.append(word)
            width += length
        if line:
            lines.append(' '.join(line))

        # Then draw it
        bboxes = [font.getbbox(line) for line in lines]
        heights = [font.getsize(line)[1] for line in lines]
        height = sum(height for height in heights) + (len(lines) - 1) * self.task_intra_gap
        image = Image.new('RGBA', (maxwidth, height))
        draw = ImageDraw.Draw(image)

        x, y = 0, 0
        for line, (x1, y1, x2, y2), height in zip(lines, bboxes, heights):
            draw.text(
                (x, y),
                line,
                fill=colour,
                font=font
            )
            if done:
                # Also strikethrough
                draw.line(
                    (x1, y + y1 + (y2 - y1) // 2, x2, y + y1 + (y2 - y1) // 2),
                    fill=self.task_done_text_colour,
                    width=self.task_done_line_width
                )
            y += height + self.task_intra_gap

        return image
