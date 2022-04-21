import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageOps

from .Card import Card
from .Skin import fielded, Skin, FieldDesc
from .Skin import AssetField, AssetPathField, StringField, NumberField, FontField, ColourField, PointField, ComputedField
from .Avatars import avatar_manager


@fielded
class GoalSkin(Skin):
    # TODO: Split into monthly/weekly
    _card_id = 'goals'
    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    background: AssetField = "goals/background.png"

    week_help_frame: AssetPathField = "weekly/help_frame.png"
    month_help_frame: AssetPathField = "monthly/help_frame.png"

    # Title section
    title_pre_gap: NumberField = 40
    title_text: StringField = "MONTHLY STATISTICS"
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: skin.title_font.getsize(skin.title_text)
    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 5
    title_gap: NumberField = 50

    # Profile section
    profile_indent: NumberField = 125
    profile_size: ComputedField = lambda skin: (
        skin.background.width - 2 * skin.profile_indent,
        int(skin._env['scale'] * 200)
    )

    avatar_mask: AssetField = FieldDesc(AssetField, 'tasklist/first/avatar_mask.png', convert=None)
    avatar_frame: AssetField = FieldDesc(AssetField, 'tasklist/first/avatar_frame.png', convert=None)
    avatar_sep: NumberField = 50

    name_font: FontField = ('BoldItalic', 55)
    name_colour: ColourField = '#DDB21D'
    discrim_font: FontField = name_font
    discrim_colour: ColourField = '#BABABA'
    name_gap: NumberField = 20

    badge_end: AssetField = "tasklist/first/badge_end.png"
    badge_font: FontField = ('Black', 30)
    badge_colour: ColourField = '#FFFFFF'
    badge_text_colour: ColourField = '#051822'
    badge_gap: NumberField = 20
    badge_min_sep: NumberField = 10

    # Progress bars
    progress_bg: AssetField = 'goals/progress_bg.png'
    progress_mask: ComputedField = lambda skin: ImageOps.invert(skin.progress_bg.split()[-1].convert('L'))
    progress_end: AssetField = 'goals/progress_end.png'

    line_gap: NumberField = 5
    progress_text_at: ComputedField = lambda skin: 7 * (skin.progress_bg.height // 10)

    task_count_font: FontField = ('Bold', 76)
    task_count_colour: ColourField = '#DDB21D'
    task_done_font: FontField = ('Bold', 37)
    task_done_colour: ColourField = '#FFFFFF'
    task_goal_font: FontField = ('Bold', 27)
    task_goal_colour: ColourField = '#FFFFFF'
    task_goal_number_font: FontField = ('Light', 27)
    task_goal_number_colour: ColourField = '#FFFFFF'
    task_text_size: ComputedField = lambda skin: (
        skin.task_count_font.getsize("00")[0]
        + skin.task_done_font.getsize("TASKS DONE")[0]
        + skin.task_goal_font.getsize("GOAL")[0]
        + 3 * skin.line_gap,
        skin.task_done_font.getsize("TASKS DONE")[1]
    )
    task_progress_text_height: ComputedField = lambda skin: (
        skin.task_count_font.getsize('100')[1] +
        skin.task_done_font.getsize('TASKS DONE')[1] +
        skin.task_goal_font.getsize('GOAL')[1] +
        2 * skin.line_gap
    )

    attendance_rate_font: FontField = ('Bold', 76)
    attendance_rate_colour: ColourField = '#DDB21D'
    attendance_font: FontField = ('Bold', 37)
    attendance_colour: ColourField = '#FFFFFF'
    attendance_text_height: ComputedField = lambda skin: (
        skin.attendance_rate_font.getsize('100%')[1] +
        skin.attendance_font.getsize('ATTENDANCE')[1] * 2 +
        2 * skin.line_gap
    )

    studied_text_font: FontField = ('Bold', 37)
    studied_text_colour: ColourField = '#FFFFFF'
    studied_hour_font: FontField = ('Bold', 60)
    studied_hour_colour: ColourField = '#DDB21D'
    studied_text_height: ComputedField = lambda skin: (
        skin.studied_text_font.getsize('STUDIED')[1] * 2
        + skin.studied_hour_font.getsize('400')[1]
        + 2 * skin.line_gap
    )

    progress_gap: NumberField = 50

    # Tasks
    task_frame: AssetField = "goals/task_frame.png"
    task_margin: PointField = (100, 50)
    task_column_sep: NumberField = 100

    task_header_font: FontField = ('Black', 50)
    task_header_colour: ColourField = '#DDB21D'
    task_header_gap: NumberField = 25
    task_underline_gap: NumberField = 10
    task_underline_width: NumberField = 5

    task_done_number_bg: AssetField = "goals/done.png"
    task_done_number_font: FontField = ('Regular', 28)
    task_done_number_colour: ColourField = '#292828'

    task_done_text_font: FontField = ('Regular', 35)
    task_done_text_colour: ColourField = '#686868'

    task_done_line_width: NumberField = FieldDesc(NumberField, 7, scaled=False)

    task_undone_number_bg: AssetField = "goals/undone.png"
    task_undone_number_font: FontField = ('Regular', 28)
    task_undone_number_colour: ColourField = '#FFFFFF'

    task_undone_text_font: FontField = ('Regular', 35)
    task_undone_text_colour: ColourField = '#FFFFFF'

    task_text_height: ComputedField = lambda skin: skin.task_done_text_font.getsize('TASK')[1]
    task_num_sep: NumberField = 15
    task_inter_gap: NumberField = 25

    # Date text
    date_pre_gap: NumberField = 25
    date_font: FontField = ('Bold', 28)
    date_colour: ColourField = '#6f6e6f'
    date_gap: NumberField = 50


class GoalPage(Card):
    server_route = "goal_card"

    def __init__(self,
                 name, discrim, avatar, badges,
                 tasks_done, studied_hours, attendance,
                 tasks_goal, studied_goal, goals,
                 date, month=False):
        self.skin = GoalSkin().load()

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
        self.title_size = self.skin.title_font.getsize(self.title_text)

        self.image = None

    @classmethod
    async def card_route(cls, runner, args, kwargs):
        kwargs['avatar'] = await avatar_manager().get_avatar(*kwargs['avatar'], 256)
        return await super().card_route(runner, args, kwargs)

    @classmethod
    def _execute(cls, *args, **kwargs):
        with BytesIO(kwargs['avatar']) as image_data:
            with Image.open(image_data).convert('RGBA') as avatar_image:
                kwargs['avatar'] = avatar_image
                return super()._execute(*args, **kwargs)

    def draw(self) -> Image:
        image = self.skin.background
        draw = ImageDraw.Draw(image)

        xpos, ypos = 0, 0

        # Draw header text
        xpos = (image.width - self.title_size[0]) // 2
        ypos += self.skin.title_pre_gap
        draw.text(
            (xpos, ypos),
            self.title_text,
            fill=self.skin.title_colour,
            font=self.skin.title_font
        )

        # Underline it
        title_size = self.skin.title_font.getsize(self.title_text)
        ypos += title_size[1] + self.skin.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
            fill=self.skin.title_colour,
            width=self.skin.title_underline_width
        )
        ypos += self.skin.title_underline_width + self.skin.title_gap

        # Draw the profile
        xpos = self.skin.profile_indent
        profile = self._draw_profile()
        image.alpha_composite(
            profile,
            (xpos, ypos)
        )

        # Start from the bottom
        ypos = image.height

        # Draw the date text
        ypos -= self.skin.date_gap
        date_text = self.data_date.strftime("As of %d %b • {} {}".format(self.data_name, self.data_discrim))
        size = self.skin.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.skin.date_font,
            fill=self.skin.date_colour
        )
        ypos -= self.skin.date_pre_gap

        if self.data_goals or self.data_tasks_goal or self.data_studied_goal:
            # Draw the tasks
            task_image = self._draw_tasks()

            ypos -= task_image.height
            image.alpha_composite(
                task_image,
                ((image.width - task_image.width) // 2, ypos)
            )

            # Draw the progress bars
            progress_image = self._draw_progress()
            ypos -= progress_image.height + self.skin.progress_gap
            image.alpha_composite(
                progress_image,
                ((image.width - progress_image.width) // 2, ypos)
            )
        else:
            if self.data_month:
                help_frame = Image.open(self.skin.month_help_frame).convert('RGBA')
            else:
                help_frame = Image.open(self.skin.week_help_frame).convert('RGBA')

            ypos -= help_frame.height
            image.alpha_composite(
                help_frame,
                ((image.width - help_frame.width) // 2, ypos)
            )

        self.image = image

        return image

    def _draw_tasks(self):
        image = self.skin.task_frame
        draw = ImageDraw.Draw(image)

        # Task container is smaller than frame
        xpos, ypos = self.skin.task_margin

        # Draw header text
        draw.text(
            (xpos, ypos),
            self.task_header,
            fill=self.skin.task_header_colour,
            font=self.skin.task_header_font
        )

        # Underline it
        title_size = self.skin.task_header_font.getsize(self.task_header)
        ypos += title_size[1] + self.skin.task_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
            fill=self.skin.task_header_colour,
            width=self.skin.task_underline_width
        )
        ypos += self.skin.task_underline_width + self.skin.task_header_gap

        if len(self.data_goals) > 5:
            # Split remaining space into two boxes
            task_box_1 = Image.new(
                'RGBA',
                (image.width // 2 - self.skin.task_margin[0] - self.skin.task_column_sep // 2,
                 image.height - ypos)
            )
            task_box_2 = Image.new(
                'RGBA',
                (image.width // 2 - self.skin.task_margin[0] - self.skin.task_column_sep // 2,
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
                (xpos + task_box_1.width + self.skin.task_column_sep, ypos)
            )
        else:
            task_box = Image.new(
                'RGBA',
                (image.width - 2 * self.skin.task_margin[0], image.height)
            )
            self._draw_tasks_into(self.data_goals, task_box)
            image.alpha_composite(
                task_box,
                (xpos, ypos)
            )
        return image

    def _draw_progress(self):
        image = Image.new('RGBA', (self.skin.background.width, self.skin.progress_bg.height))

        sep = (self.skin.background.width - 3 * self.skin.progress_bg.width) // 4

        xpos = sep
        image.alpha_composite(
            self._draw_task_progress(),
            (xpos, 0)
        )

        xpos += self.skin.progress_bg.width + sep
        image.alpha_composite(
            self._draw_study_progress(),
            (xpos, 0)
        )

        xpos += self.skin.progress_bg.width + sep
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
        ypos = self.skin.progress_text_at - self.skin.task_progress_text_height
        xpos = progress_image.width // 2

        text = str(self.data_tasks_done)
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.task_count_font,
            fill=self.skin.task_count_colour,
            anchor='mt'
        )
        ypos += self.skin.task_count_font.getsize(text)[1] + self.skin.line_gap

        text = "TASKS DONE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.task_done_font,
            fill=self.skin.task_done_colour,
            anchor='mt'
        )
        ypos += self.skin.task_done_font.getsize(text)[1] + self.skin.line_gap

        text1 = "GOAL: "
        length1 = self.skin.task_goal_font.getlength(text1)
        text2 = str(self.data_tasks_goal) if self.data_tasks_goal else "N/A"
        length2 = self.skin.task_goal_number_font.getlength(text2)
        draw.text(
            (xpos - length2 // 2, ypos),
            text1,
            font=self.skin.task_goal_font,
            fill=self.skin.task_goal_colour,
            anchor='mt'
        )
        draw.text(
            (xpos + length1 // 2, ypos),
            text2,
            font=self.skin.task_goal_number_font,
            fill=self.skin.task_goal_number_colour,
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

        ypos = self.skin.progress_text_at - self.skin.studied_text_height
        xpos = progress_image.width // 2

        text = "STUDIED"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.studied_text_font,
            fill=self.skin.studied_text_colour,
            anchor='mt'
        )
        ypos += self.skin.studied_text_font.getsize(text)[1] + self.skin.line_gap

        if self.data_studied_goal:
            text = f"{self.data_studied_hours}/{self.data_studied_goal}"
        else:
            text = str(self.data_studied_hours)
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.studied_hour_font,
            fill=self.skin.studied_hour_colour,
            anchor='mt'
        )
        ypos += self.skin.studied_hour_font.getsize(text)[1] + self.skin.line_gap

        text = "HOURS"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.studied_text_font,
            fill=self.skin.studied_text_colour,
            anchor='mt'
        )
        return progress_image

    def _draw_attendance(self):
        amount = self.data_attendance or 0

        progress_image = self._draw_progress_bar(amount)
        draw = ImageDraw.Draw(progress_image)

        ypos = self.skin.progress_text_at - self.skin.attendance_text_height
        xpos = progress_image.width // 2

        if self.data_attendance is not None:
            text = f"{int(self.data_attendance * 100)}%"
        else:
            text = "N/A"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.attendance_rate_font,
            fill=self.skin.attendance_rate_colour,
            anchor='mt'
        )
        ypos += self.skin.attendance_rate_font.getsize(text)[1] + self.skin.line_gap

        text = "ATTENDANCE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.attendance_font,
            fill=self.skin.attendance_colour,
            anchor='mt'
        )
        ypos += self.skin.attendance_font.getsize(text)[1] + self.skin.line_gap

        text = "RATE"
        draw.text(
            (xpos, ypos),
            text,
            font=self.skin.attendance_font,
            fill=self.skin.attendance_colour,
            anchor='mt'
        )
        return progress_image

    def _draw_profile(self) -> Image:
        image = Image.new('RGBA', self.skin.profile_size)
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw avatar
        avatar = self.data_avatar
        avatar.paste((0, 0, 0, 0), mask=self.skin.avatar_mask)
        avatar_image = Image.new('RGBA', (264, 264))
        avatar_image.paste(avatar, (3, 4))
        avatar_image.alpha_composite(self.skin.avatar_frame)
        avatar_image = avatar_image.resize((self.skin.profile_size[1], self.skin.profile_size[1]))
        image.alpha_composite(avatar_image, (0, 0))

        xpos += avatar_image.width + self.skin.avatar_sep

        # Draw name
        name_text = self.data_name
        name_length = self.skin.name_font.getlength(name_text + ' ')
        name_height = self.skin.name_font.getsize(name_text)[1]
        draw.text(
            (xpos, ypos),
            name_text,
            fill=self.skin.name_colour,
            font=self.skin.name_font
        )
        draw.text(
            (xpos + name_length, ypos),
            self.data_discrim,
            fill=self.skin.discrim_colour,
            font=self.skin.discrim_font
        )
        ypos += name_height + self.skin.name_gap

        # Draw badges
        _x = 0
        max_x = self.skin.profile_size[0] - xpos

        badges = [self._draw_badge(text) for text in self.data_badges]
        for badge in badges:
            if badge.width + _x > max_x:
                _x = 0
                ypos += badge.height + self.skin.badge_gap
            image.paste(
                badge,
                (xpos + _x, ypos)
            )
            _x += badge.width + self.skin.badge_min_sep
        return image

    def _draw_badge(self, text) -> Image:
        """
        Draw a single profile badge, with the given text.
        """
        text_length = self.skin.badge_font.getsize(text)[0]

        height = self.skin.badge_end.height
        width = text_length + self.skin.badge_end.width

        badge = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))

        # Add blobs to ends
        badge.paste(
            self.skin.badge_end,
            (0, 0)
        )
        badge.paste(
            self.skin.badge_end,
            (width - self.skin.badge_end.width, 0)
        )

        # Add rectangle to middle
        draw = ImageDraw.Draw(badge)
        draw.rectangle(
            (
                (self.skin.badge_end.width // 2, 0),
                (width - self.skin.badge_end.width // 2, height),
            ),
            fill=self.skin.badge_colour,
            width=0
        )

        # Write badge text
        draw.text(
            (self.skin.badge_end.width // 2, height // 2),
            text,
            font=self.skin.badge_font,
            fill=self.skin.badge_text_colour,
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
                image.width - xpos - self.skin.task_done_number_bg.width - self.skin.task_num_sep,
                done
            )
            if task_image.height + ypos > image.height:
                break

            # Draw number background
            bg = self.skin.task_done_number_bg if done else self.skin.task_undone_number_bg
            image.alpha_composite(
                bg,
                (xpos, ypos)
            )

            # Draw number
            font = self.skin.task_done_number_font if done else self.skin.task_undone_number_font
            colour = self.skin.task_done_number_colour if done else self.skin.task_undone_number_colour
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
                (xpos + bg.width + self.skin.task_num_sep, ypos - (bg.height - self.skin.task_text_height) // 2)
            )

            ypos += task_image.height + self.skin.task_inter_gap

        return image

    def _draw_text(self, task, maxwidth, done) -> Image:
        """
        Draw the text of a given task.
        """
        font = self.skin.task_done_text_font if done else self.skin.task_undone_text_font
        colour = self.skin.task_done_text_colour if done else self.skin.task_undone_text_colour

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
                fill=self.skin.task_done_text_colour,
                width=self.skin.task_done_line_width
            )

        return image

    def _draw_progress_bar(self, amount):
        amount = min(amount, 1)
        amount = max(amount, 0)
        bg = self.skin.progress_bg
        end = self.skin.progress_end
        mask = self.skin.progress_mask

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
