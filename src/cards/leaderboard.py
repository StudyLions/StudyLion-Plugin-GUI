import asyncio
from io import BytesIO
from PIL import Image, ImageDraw

from .Card import Card
from .Avatars import avatar_manager
from .Skin import fielded, Skin, FieldDesc
from .Skin import AssetField, NumberField, FontField, ColourField, PointField, ComputedField, StringField
from .Skin import AssetPathField


class LeaderboardEntry:
    __slots__ = (
        'userid',
        'position',
        'time',
        'name',
        'avatar_key',
        'image'
    )

    def __init__(self, userid, position, time, name, avatar_key):
        self.userid = userid

        self.position = position
        self.time = time

        self.name = name
        self.name = ''.join(i if ord(i) < 128 or i == '∞' else '*' for i in self.name)

        self.avatar_key = avatar_key

        self.image = None

    async def get_avatar(self):
        if not self.image:
            self.image = await avatar_manager().get_avatar(
                *self.avatar_key,
                size=512 if self.position in (1, 2, 3) else 256
            )

    def convert_avatar(self):
        if self.image:
            with BytesIO(self.image) as data:
                self.image = Image.open(data).convert('RGBA')


@fielded
class LeaderboardSkin(Skin):
    _card_id = "leaderboard"

    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    header_text_pre_gap: NumberField = 20
    header_text: StringField = "STUDY TIME LEADERBOARD"
    header_text_font: FontField = ('ExtraBold', 80)
    header_text_size: ComputedField = lambda skin: skin.header_text_font.getsize(skin.header_text)
    header_text_colour: ColourField = '#DDB21D'

    header_text_gap: NumberField = 15
    header_text_line_width: NumberField = 5
    header_text_line_gap: NumberField = 20

    subheader_name_font: FontField = ('SemiBold', 27)
    subheader_name_colour: ColourField = '#FFFFFF'
    subheader_value_font: FontField = ('Regular', 27)
    subheader_value_colour: ColourField = '#FFFFFF'

    header_gap: NumberField = 20

    # First page constants
    first_bg_path: AssetPathField = "leaderboard/first_page/bg.png"
    first_header_bg_path: AssetPathField = "leaderboard/first_page/header.png"
    first_header_bg_position: PointField = (0, 0)
    header_bg_gap: NumberField = 20

    first_avatar_mask: AssetField = "leaderboard/first_page/avatar_mask.png"
    first_avatar_bg: AssetField = 'leaderboard/first_page/avatar_bg.png'
    first_level_scale: NumberField = FieldDesc(NumberField, 0.8, integer=False, scale=False)
    crown_1: AssetField = "leaderboard/first_page/crown_1.png"
    crown_2: AssetField = "leaderboard/first_page/crown_2.png"
    crown_3: AssetField = "leaderboard/first_page/crown_3.png"
    crown_gap: NumberField = 10

    first_top_gap: NumberField = 20

    top_name_font: FontField = ('Bold', 30)
    top_name_colour: ColourField = '#DDB21D'
    top_hours_font: FontField = ('Medium', 30)
    top_hours_colour: ColourField = '#FFFFFF'
    top_text_sep: NumberField = 5

    # Other page constants
    other_bg_path: AssetPathField = "leaderboard/other_page/bg.png"
    other_header_bg_path: AssetPathField = "leaderboard/other_page/header.png"
    other_header_gap: NumberField = 20

    # Entry constants
    entry_font: FontField = ("SemiBold", 45)
    entry_colour: ColourField = '#FFFFFF'
    entry_position_at: NumberField = 200
    entry_name_at: NumberField = 300
    entry_time_at: NumberField = -150

    entry_bg: AssetField = "leaderboard/entry_bg.png"
    entry_highlight_bg: AssetField = "leaderboard/entry_highlight_bg.png"
    entry_mask: AssetField = FieldDesc(AssetField, "leaderboard/entry_avatar_mask.png", convert=None)

    entry_gap: NumberField = 13


class LeaderboardPage(Card):
    server_route = 'leaderboard_card'

    def __init__(self, server_name, entries, highlight=None):
        self.skin = LeaderboardSkin().load()

        self.server_name = server_name
        self.entries = entries
        self.highlight = highlight
        self.first_page = any(entry.position in (1, 2, 3) for entry in entries)

        self.image = None

    @classmethod
    async def card_route(cls, runner, args, kwargs):
        entries = [LeaderboardEntry(*entry) for entry in kwargs['entries']]
        await asyncio.gather(
            *(entry.get_avatar() for entry in entries)
        )
        kwargs['entries'] = entries
        return await super().card_route(runner, args, kwargs)

    @classmethod
    def _execute(cls, *args, **kwargs):
        for entry in kwargs['entries']:
            entry.convert_avatar()
        return super()._execute(*args, **kwargs)

    def draw(self) -> Image:
        if self.first_page:
            self.image = self._draw_first_page()
        else:
            self.image = self._draw_other_page()
        return self.image

    def _draw_first_page(self) -> Image:
        # Collect background
        image = Image.open(self.skin.first_bg_path)
        draw = ImageDraw.Draw(image)

        # Draw header background
        header_background = Image.open(self.skin.first_header_bg_path)
        image.alpha_composite(
            header_background,
            self.skin.first_header_bg_position
        )

        xpos, ypos = 0, 0

        # Draw the header text
        ypos += self.skin.header_text_pre_gap
        header = self._draw_header_text()
        image.alpha_composite(
            header,
            (xpos + (image.width // 2 - header.width // 2),
             ypos)
        )
        ypos += header.height + self.skin.header_gap

        # Draw the top 3
        first_entry = self.entries[0]
        first = self._draw_first(first_entry, level=1)
        first_x = (image.width - first.width) // 2
        image.alpha_composite(
            first,
            (first_x, ypos)
        )
        first_text_y = ypos + first.height + self.skin.first_top_gap
        text_y = first_text_y
        text_x = first_x + (first.width // 2)
        draw.text(
            (text_x, text_y),
            '1ST',
            font=self.skin.top_name_font,
            fill=self.skin.top_name_colour,
            anchor='mt'
        )
        text_y += self.skin.top_name_font.getsize('1ST')[1] + self.skin.top_text_sep
        draw.text(
            (text_x, text_y),
            first_entry.name,
            font=self.skin.top_name_font,
            fill=self.skin.top_name_colour,
            anchor='mt'
        )
        text_y += self.skin.top_name_font.getsize(first_entry.name)[1] + self.skin.top_text_sep
        draw.text(
            (text_x, text_y),
            "{} hours".format(first_entry.time // 3600),
            font=self.skin.top_hours_font,
            fill=self.skin.top_hours_colour,
            anchor='mt'
        )

        if len(self.entries) >= 2:
            second_entry = self.entries[1]
            second = self._draw_first(second_entry, level=2)
            second_x = image.width // 4 - second.width // 2
            image.alpha_composite(
                second,
                (
                    second_x,
                    ypos + (first.height - second.height) // 2
                )
            )
            text_y = first_text_y
            text_x = second_x + (second.width // 2)
            draw.text(
                (text_x, text_y),
                '2ND',
                font=self.skin.top_name_font,
                fill=self.skin.top_name_colour,
                anchor='mt'
            )
            text_y += self.skin.top_name_font.getsize('2ND')[1] + self.skin.top_text_sep
            draw.text(
                (text_x, text_y),
                second_entry.name,
                font=self.skin.top_name_font,
                fill=self.skin.top_name_colour,
                anchor='mt'
            )
            text_y += self.skin.top_name_font.getsize(second_entry.name)[1] + self.skin.top_text_sep
            draw.text(
                (text_x, text_y),
                "{} hours".format(second_entry.time // 3600),
                font=self.skin.top_hours_font,
                fill=self.skin.top_hours_colour,
                anchor='mt'
            )

        if len(self.entries) >= 3:
            third_entry = self.entries[2]
            third = self._draw_first(third_entry, level=3)
            third_x = 3 * image.width // 4 - third.width // 2
            image.alpha_composite(
                third,
                (
                    third_x,
                    ypos + (first.height - third.height) // 2
                )
            )
            text_y = first_text_y
            text_x = third_x + (third.width // 2)
            draw.text(
                (text_x, text_y),
                '3RD',
                font=self.skin.top_name_font,
                fill=self.skin.top_name_colour,
                anchor='mt'
            )
            text_y += self.skin.top_name_font.getsize('3ND')[1] + self.skin.top_text_sep
            draw.text(
                (text_x, text_y),
                third_entry.name,
                font=self.skin.top_name_font,
                fill=self.skin.top_name_colour,
                anchor='mt'
            )
            text_y += self.skin.top_name_font.getsize(third_entry.name)[1] + self.skin.top_text_sep
            draw.text(
                (text_x, text_y),
                "{} hours".format(third_entry.time // 3600),
                font=self.skin.top_hours_font,
                fill=self.skin.top_hours_colour,
                anchor='mt'
            )

        # Draw the entries
        xpos = (image.width - self.skin.entry_bg.width) // 2
        ypos = header_background.height + self.skin.header_bg_gap

        for entry in self.entries[3:]:
            entry_image = self._draw_entry(
                entry,
                highlight=self.highlight and (entry.position == self.highlight)
            )
            image.alpha_composite(
                entry_image,
                (xpos, ypos)
            )
            ypos += self.skin.entry_bg.height + self.skin.entry_gap

        return image

    def _draw_other_page(self) -> Image:
        # Collect backgrounds
        background = Image.open(self.skin.other_bg_path).convert('RGBA')
        header_bg = Image.open(self.skin.other_header_bg_path).convert('RGBA')

        # Draw header onto background
        header = self._draw_header_text()
        header_bg.alpha_composite(
            header,
            (
                (header_bg.width - header.width) // 2,
                (header_bg.height - header.height) // 2
            )
        )

        # Draw the entries
        xpos = (background.width - self.skin.entry_bg.width) // 2
        ypos = (background.height - 10 * self.skin.entry_bg.height - 9 * self.skin.entry_gap) // 2

        for entry in self.entries:
            entry_image = self._draw_entry(
                entry,
                highlight=self.highlight and (entry.position == self.highlight)
            )
            background.alpha_composite(
                entry_image,
                (xpos, ypos)
            )
            ypos += self.skin.entry_bg.height + self.skin.entry_gap

        # Combine images
        image = Image.new(
            'RGBA',
            (
                background.width,
                header_bg.height + self.skin.other_header_gap + background.height
            )
        )
        image.alpha_composite(
            header_bg,
            (0, 0)
        )
        image.alpha_composite(
            background,
            (0, header_bg.height + self.skin.other_header_gap)
        )
        return image

    def _draw_entry(self, entry, highlight=False) -> Image:
        # Get the appropriate background
        image = (self.skin.entry_bg if not highlight else self.skin.entry_highlight_bg).copy()
        draw = ImageDraw.Draw(image)
        ypos = image.height // 2

        # Mask the avatar, if it exists
        avatar = entry.image
        avatar.thumbnail((187, 187))
        avatar.paste((0, 0, 0, 0), mask=self.skin.entry_mask)

        # Paste avatar onto image
        image.alpha_composite(avatar, (0, 0))

        # Write position
        draw.text(
            (self.skin.entry_position_at, ypos),
            str(entry.position),
            fill=self.skin.entry_colour,
            font=self.skin.entry_font,
            anchor='mm'
        )

        # Write name
        draw.text(
            (self.skin.entry_name_at, ypos),
            entry.name,
            fill=self.skin.entry_colour,
            font=self.skin.entry_font,
            anchor='lm'
        )

        # Write time
        time_str = "{:02d}:{:02d}".format(
            entry.time // 3600,
            (entry.time % 3600) // 60
        )
        draw.text(
            (image.width + self.skin.entry_time_at, ypos),
            time_str,
            fill=self.skin.entry_colour,
            font=self.skin.entry_font,
            anchor='mm'
        )

        return image

    def _draw_first(self, entry, level) -> Image:
        if level == 1:
            crown = self.skin.crown_1
        elif level == 2:
            crown = self.skin.crown_2
        elif level == 3:
            crown = self.skin.crown_3

        image = Image.new(
            'RGBA',
            (self.skin.first_avatar_bg.width,
             crown.height + self.skin.crown_gap
             + self.skin.first_avatar_mask.height
             + (self.skin.first_avatar_bg.height - self.skin.first_avatar_mask.height) // 2)
        )

        # Retrieve and mask avatar
        avatar = entry.image
        avatar.paste((0, 0, 0, 0), mask=self.skin.first_avatar_mask.convert('RGBA'))

        # Paste on the background
        image.paste(
            self.skin.first_avatar_bg,
            (0, image.height - self.skin.first_avatar_bg.height)
        )

        # Paste on the avatar
        image.alpha_composite(
            avatar,
            (
                (self.skin.first_avatar_bg.width - avatar.width) // 2,
                image.height - self.skin.first_avatar_bg.height +
                (self.skin.first_avatar_bg.height - avatar.height) // 2
            )
        )

        image.alpha_composite(
            crown,
            ((image.width - crown.width) // 2, 0)
        )

        # Downscale depending on ranking
        if level in (2, 3):
            new_height = int(image.height * self.skin.first_level_scale)
            image.thumbnail((new_height, new_height))

        return image

    def _draw_header_text(self) -> Image:
        image = Image.new(
            'RGBA',
            (self.skin.header_text_size[0],
             self.skin.header_text_size[1] + self.skin.header_text_gap + self.skin.header_text_line_width
             + self.skin.header_text_line_gap
             + self.skin.subheader_name_font.getsize("THIS MONTH")[1]),
        )
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw the top text
        draw.text(
            (0, 0),
            self.skin.header_text,
            font=self.skin.header_text_font,
            fill=self.skin.header_text_colour
        )
        ypos += self.skin.header_text_size[1] + self.skin.header_text_gap

        # Draw the underline
        draw.line(
            (xpos, ypos,
             xpos + self.skin.header_text_size[0], ypos),
            fill=self.skin.header_text_colour,
            width=self.skin.header_text_line_width
        )
        ypos += self.skin.header_text_line_gap

        # Draw the subheader
        text_name = "SERVER: "
        text_name_width = self.skin.subheader_name_font.getlength(text_name)
        text_value = self.server_name
        text_value_width = self.skin.subheader_value_font.getlength(text_value)
        total_width = text_name_width + text_value_width
        xpos += (image.width - total_width) // 2
        draw.text(
            (xpos, ypos),
            text_name,
            fill=self.skin.subheader_name_colour,
            font=self.skin.subheader_name_font
        )
        xpos += text_name_width
        draw.text(
            (xpos, ypos),
            text_value,
            fill=self.skin.subheader_value_colour,
            font=self.skin.subheader_value_font
        )

        return image


# if __name__ == '__main__':
#     avatar_url = "https://cdn.discordapp.com/avatars/757652191656804413/e49459df05c4ed7995defd7c6ce79a97.png"
#     entries = [
#         LeaderboardEntry(1, 100*3600, name="FIRST PERSON"),
#         LeaderboardEntry(2, 50*3600, name="SECOND PERSON"),
#         LeaderboardEntry(3, 25*3600, name="THIRD PERSON"),
#         LeaderboardEntry(4, 13*3600, name="FOURTH PERSON"),
#         LeaderboardEntry(5, 10*3600 + 20 * 60, name="FIFTH PERSON"),
#         LeaderboardEntry(6, 10*3600 + 20 * 60, name="SIXTH PERSON"),
#         LeaderboardEntry(7, 10*3600 + 20 * 60, name="SEVENTH PERSON"),
#         LeaderboardEntry(8, 10*3600 + 20 * 60, name="EIGHT PERSON"),
#         LeaderboardEntry(9, 10*3600 + 20 * 60, name="NINTH PERSON"),
#         LeaderboardEntry(10, 10*3600 + 20 * 60, name="TENTH PERSON"),
#     ]
#     for entry in entries[:3]:
#         entry.image = Image.open('samples/example_avatar_512.png').convert('RGBA')
#     for entry in entries[3:]:
#         entry.image = Image.open('samples/example_avatar_512.png').convert('RGBA')

#     page = LeaderboardPage("The Study Lions", entries, highlight=15)
#     image = page.draw()
#     image.save("lb_page.png")
