from io import BytesIO
import pickle

from PIL import Image, ImageDraw

from .Card import Card
from .Skin import fielded, Skin, FieldDesc
from .Skin import AssetField, NumberField, FontField, ColourField, ComputedField, RawField, StringField, PointField
from .Avatars import avatar_manager


@fielded
class TasklistSkin(Skin):
    _card_id = "tasklist"

    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    # First page
    first_page_bg: AssetField = "tasklist/first/bg.png"
    first_page_frame: AssetField = "tasklist/first/frame.png"

    title_pre_gap: NumberField = 40
    title_text: StringField = "TO DO LIST"
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: skin.title_font.getsize(skin.title_text)
    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 5
    title_gap: NumberField = 50

    profile_indent: NumberField = 125
    profile_size: ComputedField = lambda skin: (
        skin.first_page_bg.width - 2 * skin.profile_indent,
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

    # Other pages
    other_page_bg: AssetField = "tasklist/other/bg.png"
    other_page_frame: AssetField = "tasklist/other/frame.png"

    # Help frame
    help_frame: AssetField = "tasklist/help_frame.png"

    # Tasks
    task_start_position: PointField = (100, 75)

    task_done_number_bg: AssetField = "tasklist/done.png"
    task_done_number_font: FontField = ('Regular', 45)
    task_done_number_colour: ColourField = '#292828'

    task_done_text_font: FontField = ('Regular', 55)
    task_done_text_colour: ColourField = '#686868'

    task_done_line_width: NumberField = 3.5

    task_undone_number_bg: AssetField = "tasklist/undone.png"
    task_undone_number_font: FontField = ('Regular', 45)
    task_undone_number_colour: ColourField = '#FFFFFF'

    task_undone_text_font: FontField = ('Regular', 55)
    task_undone_text_colour: ColourField = '#FFFFFF'

    task_text_height: ComputedField = lambda skin: skin.task_done_text_font.getsize('TASK')[1]
    task_num_sep: NumberField = 30
    task_inter_gap: NumberField = 32
    task_intra_gap: NumberField = 25

    # Date text
    date_pre_gap: NumberField = 50
    date_font: FontField = ('Bold', 28)
    date_colour: ColourField = '#686868'
    date_gap: NumberField = 50


class Tasklist(Card):
    server_route = 'tasklist'

    def __init__(self, name, discrim, tasks, date, avatar, badges=()):
        self.skin = TasklistSkin().load()

        self.data_name = name
        self.data_discrim = discrim
        self.data_avatar = avatar
        self.data_tasks = tasks
        self.data_date = date
        self.data_badges = badges

        self.tasks_drawn = 0
        self.images = []

    @classmethod
    async def request(cls, *args, **kwargs):
        data = await super().request(*args, **kwargs)
        return pickle.loads(data)

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

    def _execute_draw(self):
        image_data = []
        for image in self.draw():
            with BytesIO() as data:
                image.save(data, format='PNG')
                data.seek(0)
                image_data.append(data.getvalue())
        return pickle.dumps(image_data)

    def draw(self):
        self.images = []
        self.images.append(self._draw_first_page())
        while self.tasks_drawn < len(self.data_tasks):
            self.images.append(self._draw_another_page())

        return self.images

    def _draw_first_page(self) -> Image:
        image = self.skin.first_page_bg
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw header text
        xpos = (image.width - self.skin.title_size[0]) // 2
        ypos += self.skin.title_pre_gap
        draw.text(
            (xpos, ypos),
            self.skin.title_text,
            fill=self.skin.title_colour,
            font=self.skin.title_font
        )

        # Underline it
        ypos += self.skin.title_size[1] + self.skin.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + self.skin.title_size[0], ypos),
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

        if self.data_tasks:
            # Draw the date text
            ypos -= self.skin.date_gap
            date_text = self.data_date.strftime("As of %d %b")
            size = self.skin.date_font.getsize(date_text)
            ypos -= size[1]
            draw.text(
                ((image.width - size[0]) // 2, ypos),
                date_text,
                font=self.skin.date_font,
                fill=self.skin.date_colour
            )
            ypos -= self.skin.date_pre_gap

            # Draw the tasks
            task_image = self._draw_tasks_into(self.skin.first_page_frame.copy())

            ypos -= task_image.height
            image.alpha_composite(
                task_image,
                ((image.width - task_image.width) // 2, ypos)
            )
        else:
            # Draw the help frame
            ypos -= self.skin.date_gap
            image.alpha_composite(
                self.skin.help_frame,
                ((image.width - self.skin.help_frame.width) // 2, ypos - self.skin.help_frame.height)
            )

        return image

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

    def _draw_another_page(self) -> Image:
        image = self.skin.other_page_bg.copy()
        draw = ImageDraw.Draw(image)

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

        # Draw the tasks
        task_image = self._draw_tasks_into(self.skin.other_page_frame.copy())
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
        xpos, ypos = self.skin.task_start_position

        for n, task, done in self.data_tasks[self.tasks_drawn:]:
            # Draw task first to check if it fits on the page
            task_image = self._draw_text(
                task,
                image.width - xpos - self.skin.task_done_number_bg.width - self.skin.task_num_sep,
                done
            )
            if task_image.height + ypos + self.skin.task_inter_gap > image.height:
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
            self.tasks_drawn += 1

        return image

    def _draw_text(self, task, maxwidth, done) -> Image:
        """
        Draw the text of a given task.
        """
        font = self.skin.task_done_text_font if done else self.skin.task_undone_text_font
        colour = self.skin.task_done_text_colour if done else self.skin.task_undone_text_colour

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
        height = sum(height for height in heights) + (len(lines) - 1) * self.skin.task_intra_gap
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
                    fill=self.skin.task_done_text_colour,
                    width=self.skin.task_done_line_width
                )
            y += height + self.skin.task_intra_gap

        return image
