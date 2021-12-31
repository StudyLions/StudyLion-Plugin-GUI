import math
from datetime import datetime
from PIL import Image, ImageFont, ImageDraw, ImageOps
from ..utils import asset_path, inter_font


class GoalPage:
    scale = 2

    background = Image.open(asset_path("goals/background.png")).convert('RGBA')

    # Title section
    title_pre_gap = int(scale * 40)
    title_text = "MONTHLY STATISTICS"
    title_font = inter_font('ExtraBold', size=int(scale * 76))
    title_size = title_font.getsize(title_text)
    title_colour = '#DDB21D'
    title_underline_gap = int(scale * 10)
    title_underline_width = int(scale * 5)
    title_gap = int(scale * 50)

    # Profile section
    profile_indent = int(scale * 125)
    profile_size = (
        background.width - 2 * profile_indent,
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

    # Progress bars
    progress_bg = Image.open(asset_path('goals/progress_bg.png'))
    progress_mask = ImageOps.invert(progress_bg.split()[-1].convert('L'))
    progress_end = Image.open(asset_path('goals/progress_end.png'))

    line_gap = int(scale * 10)
    progress_text_at = progress_bg.height // 4

    task_count_font = inter_font('Bold', size=int(scale*76))
    task_count_colour = '#DDB21D'
    task_done_font = inter_font('Bold', size=int(scale*37))
    task_done_colour = '#FFFFFF'
    task_goal_font = inter_font('Bold', size=int(scale*27))
    task_goal_colour = '#FFFFFF'
    task_goal_number_font = inter_font('Light', size=int(scale*27))
    task_goal_number_colour = '#FFFFFF'
    task_text_size = (
        task_count_font.getsize("00")[0]
        + task_done_font.getsize("TASKS DONE")[0]
        + task_goal_font.getsize("GOAL")[0]
        + 3 * line_gap,
        task_done_font.getsize("TASKS DONE")[1]
    )

    attendance_rate_font = inter_font('Bold', size=int(scale*76))
    attendance_rate_colour = '#DDB21D'
    attendance_font = inter_font('Bold', size=int(scale*37))
    attendance_colour = '#FFFFFF'

    studied_text_font = inter_font('Bold', size=int(scale*37))
    studied_text_colour = '#FFFFFF'
    studied_hour_font = inter_font('Bold', size=int(scale*55))
    studied_hour_colour = '#DDB21D'

    progress_gap = int(scale * 50)

    # Tasks
    task_frame = Image.open(asset_path("goals/task_frame.png"))
    task_margin = (100, 50)
    task_column_sep = int(scale * 100)

    task_header_font = inter_font('Black', size=int(scale*50))
    task_header_colour = '#DDB21D'
    task_header_gap = int(scale * 25)
    task_underline_gap = int(scale * 10)
    task_underline_width = int(scale * 5)

    task_done_number_bg = Image.open(asset_path("goals/done.png")).convert('RGBA')
    task_done_number_font = inter_font('Regular', size=int(scale * 28))
    task_done_number_colour = '#292828'

    task_done_text_font = inter_font('Regular', size=int(scale * 35))
    task_done_text_colour = '#686868'

    task_done_line_width = 7

    task_undone_number_bg = Image.open(asset_path("goals/undone.png")).convert('RGBA')
    task_undone_number_font = inter_font('Regular', size=int(scale * 28))
    task_undone_number_colour = '#FFFFFF'

    task_undone_text_font = inter_font('Regular', size=int(scale * 35))
    task_undone_text_colour = '#FFFFFF'

    task_text_height = task_done_text_font.getsize('TASK')[1]
    task_num_sep = int(scale * 15)
    task_inter_gap = int(scale * 25)

    # Date text
    date_pre_gap = int(scale * 25)
    date_font = inter_font('Bold', size=int(scale * 28))
    date_colour = '#6f6e6f'
    date_gap = int(scale * 50)

    def __init__(self,
                 name, discrim, avatar, badges,
                 tasks_done, studied_hours, attendance,
                 tasks_goal, studied_goal, goals,
                 date, month=False):
        self.data_name = name
        self.data_discrim = discrim
        self.data_avatar = avatar
        self.data_badges = badges

        self.data_tasks_done = tasks_done
        self.data_studied_hours = studied_hours
        self.data_attendance = attendance
        self.data_tasks_goal = tasks_goal

        self.data_studied_goal = studied_goal
        self.data_goals = goals
        self.data_date = date
        self.data_month = month

        if month:
            self.title_text = "MONTHLY STATISTICS"
            self.task_header = "GOALS OF THE MONTH"
        else:
            self.title_text = "WEEKLY STATISTICS"
            self.task_header = "GOALS OF THE WEEK"
        self.title_size = self.title_font.getsize(self.title_text)

    def draw(self) -> Image:
        image = self.background.copy()
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
        title_size = self.title_font.getsize(self.title_text)
        ypos += title_size[1] + self.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
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
        task_image = self._draw_tasks()

        ypos -= task_image.height
        image.alpha_composite(
            task_image,
            ((image.width - task_image.width) // 2, ypos)
        )

        # Draw the progress bars

        progress_image = self._draw_progress()
        ypos -= progress_image.height + self.progress_gap
        image.alpha_composite(
            progress_image,
            ((image.width - progress_image.width) // 2, ypos)
        )

        return image

    def _draw_tasks(self):
        image = self.task_frame.copy()
        draw = ImageDraw.Draw(image)

        # Task container is smaller than frame
        xpos, ypos = self.task_margin

        # Draw header text
        draw.text(
            (xpos, ypos),
            self.task_header,
            fill=self.task_header_colour,
            font=self.task_header_font
        )

        # Underline it
        title_size = self.task_header_font.getsize(self.task_header)
        ypos += title_size[1] + self.task_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
            fill=self.task_header_colour,
            width=self.task_underline_width
        )
        ypos += self.task_underline_width + self.task_header_gap

        if len(self.data_goals) > 5:
            # Split remaining space into two boxes
            task_box_1 = Image.new(
                'RGBA',
                (image.width // 2 - self.task_margin[0] - self.task_column_sep // 2,
                 image.height - ypos)
            )
            task_box_2 = Image.new(
                'RGBA',
                (image.width // 2 - self.task_margin[0] - self.task_column_sep // 2,
                 image.height - ypos)
            )
            self._draw_tasks_into(self.data_goals[:5], task_box_1)
            self._draw_tasks_into(self.data_goals[5:], task_box_2)
            image.alpha_composite(
                task_box_1,
                (xpos, ypos)
            )
            image.alpha_composite(
                task_box_2,
                (xpos + task_box_1.width + self.task_column_sep, ypos)
            )
        else:
            task_box = Image.new(
                'RGBA',
                (image.width - 2 * self.task_margin[0], image.height)
            )
            self._draw_tasks_into(self.data_goals, task_box)
            image.alpha_composite(
                task_box,
                (xpos, ypos)
            )
        return image

    def _draw_progress(self):
        image = Image.new('RGBA', (self.background.width, self.progress_bg.height))

        sep = (self.background.width - 3 * self.progress_bg.width) // 4

        xpos = sep
        image.alpha_composite(
            self._draw_task_progress(),
            (xpos, 0)
        )

        xpos += self.progress_bg.width + sep
        image.alpha_composite(
            self._draw_study_progress(),
            (xpos, 0)
        )

        xpos += self.progress_bg.width + sep
        image.alpha_composite(
            self._draw_attendance(),
            (xpos, 0)
        )

        return image

    def _draw_task_progress(self):
        if not self.data_tasks_goal:
            amount = 1
        else:
            amount = self.data_tasks_done / self.data_tasks_goal

        progress_image = self._draw_progress_bar(amount)
        draw = ImageDraw.Draw(progress_image)

        # Draw text into the bar
        ypos = self.progress_text_at
        xpos = progress_image.width // 2

        text = str(self.data_tasks_done)
        draw.text(
            (xpos, ypos),
            text,
            font=self.task_count_font,
            fill=self.task_count_colour,
            anchor='mt'
        )
        ypos += self.task_count_font.getsize(text)[1] + self.line_gap

        text = "TASKS DONE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.task_done_font,
            fill=self.task_done_colour,
            anchor='mt'
        )
        ypos += self.task_done_font.getsize(text)[1] + self.line_gap

        text1 = "GOAL: "
        length1 = self.task_goal_font.getlength(text1)
        text2 = str(self.data_tasks_goal) if self.data_tasks_goal else "N/A"
        length2 = self.task_goal_number_font.getlength(text2)
        draw.text(
            (xpos - length2 // 2, ypos),
            text1,
            font=self.task_goal_font,
            fill=self.task_goal_colour,
            anchor='mt'
        )
        draw.text(
            (xpos + length1 // 2, ypos),
            text2,
            font=self.task_goal_number_font,
            fill=self.task_goal_number_colour,
            anchor='mt'
        )
        return progress_image

    def _draw_study_progress(self):
        if not self.data_studied_goal:
            amount = 1
        else:
            amount = self.data_studied_hours / self.data_studied_goal

        progress_image = self._draw_progress_bar(amount)
        draw = ImageDraw.Draw(progress_image)

        ypos = self.progress_text_at
        xpos = progress_image.width // 2

        text = "STUDIED"
        draw.text(
            (xpos, ypos),
            text,
            font=self.studied_text_font,
            fill=self.studied_text_colour,
            anchor='mt'
        )
        ypos += self.studied_text_font.getsize(text)[1] + self.line_gap

        if self.data_studied_goal:
            text = f"{self.data_studied_hours}/{self.data_studied_goal}"
        else:
            text = str(self.data_studied_hours)
        draw.text(
            (xpos, ypos),
            text,
            font=self.studied_hour_font,
            fill=self.studied_hour_colour,
            anchor='mt'
        )
        ypos += self.studied_hour_font.getsize(text)[1] + self.line_gap

        text = "HOURS"
        draw.text(
            (xpos, ypos),
            text,
            font=self.studied_text_font,
            fill=self.studied_text_colour,
            anchor='mt'
        )
        return progress_image

    def _draw_attendance(self):
        amount = self.data_attendance

        progress_image = self._draw_progress_bar(amount)
        draw = ImageDraw.Draw(progress_image)

        ypos = self.progress_text_at
        xpos = progress_image.width // 2

        text = f"{int(self.data_attendance * 100)}%"
        draw.text(
            (xpos, ypos),
            text,
            font=self.attendance_rate_font,
            fill=self.attendance_rate_colour,
            anchor='mt'
        )
        ypos += self.attendance_rate_font.getsize(text)[1] + self.line_gap

        text = "ATTENDANCE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.attendance_font,
            fill=self.attendance_colour,
            anchor='mt'
        )
        ypos += self.attendance_font.getsize(text)[1] + self.line_gap

        text = "RATE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.attendance_font,
            fill=self.attendance_colour,
            anchor='mt'
        )
        return progress_image

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

    def _draw_tasks_into(self, tasks, image) -> Image:
        """
        Draw as many tasks as possible into the given image background.
        """
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        for n, task, done in tasks:
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

        return image

    def _draw_text(self, task, maxwidth, done) -> Image:
        """
        Draw the text of a given task.
        """
        font = self.task_done_text_font if done else self.task_undone_text_font
        colour = self.task_done_text_colour if done else self.task_undone_text_colour

        size = font.getsize(task)
        image = Image.new('RGBA', (min(size[0], maxwidth), size[1]))
        draw = ImageDraw.Draw(image)

        draw.text((0, 0), task, font=font, fill=colour)

        if done:
            # Also strikethrough
            y = 0
            x1, y1, x2, y2 = font.getbbox(task)
            draw.line(
                (x1, y + y1 + (y2 - y1) // 2, x2, y + y1 + (y2 - y1) // 2),
                fill=self.task_done_text_colour,
                width=self.task_done_line_width
            )

        return image

    def _draw_progress_bar(self, amount):
        bg = self.progress_bg
        end = self.progress_end
        mask = self.progress_mask

        center = (
            bg.width // 2 + 1,
            bg.height // 2
        )
        radius = 2 * 158
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
                    30 - end.height // 2
                )
            )
            canvas.alpha_composite(
                end,
                (
                    x - end.width // 2,
                    y - end.height // 2
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
                fill='#6CB7D0'
            )

            canvas.paste((0, 0, 0, 0), mask=mask)

        image = Image.new('RGBA', size=(bg.width, bg.height))
        image.alpha_composite(bg)
        image.alpha_composite(canvas)

        return image
