import io
from PIL import Image, ImageDraw

from ..utils import asset_path, inter_font


class LeaderboardEntry:
    def __init__(self, position, time, member=None, name=None):
        self.position = position
        self.time = time

        if member:
            self.name = member.name
            self.avatar_url = member.avatar_url_as(format='png', size=512 if position in (1, 2, 3) else 64)
        else:
            self.name = str(name)
            self.avatar_url = None

        self.image = None

    async def save_image(self):
        if self.avatar_url:
            with io.BytesIO() as avatar_data:
                await self.avatar_url.save(avatar_data)
                self.image = Image.open(avatar_data).convert('RGBA')


class LeaderboardPage:
    scale = 2

    header_text_pre_gap = int(scale*20)
    header_text = "STUDY TIME LEADERBOARD"
    header_text_font = inter_font('ExtraBold', size=int(scale*80))
    header_text_size = header_text_font.getsize(header_text)
    header_text_colour = '#DDB21D'

    header_text_gap = int(scale*15)
    header_text_line_width = int(scale*5)
    header_text_line_gap = int(scale*20)

    subheader_name_font = inter_font('SemiBold', size=int(scale*27))
    subheader_name_colour = '#FFFFFF'
    subheader_value_font = inter_font('Regular', size=int(scale*27))
    subheader_value_colour = '#FFFFFF'

    header_gap = int(scale * 20)

    # First page constants
    first_bg_path = asset_path("leaderboard/first_page/bg.png")
    first_header_bg_path = asset_path("leaderboard/first_page/header.png")
    first_header_bg_position = (0, 0)
    header_bg_gap = int(scale * 20)

    first_avatar_mask = Image.open(asset_path("leaderboard/first_page/avatar_mask.png")).convert('RGBA')
    first_avatar_bg = Image.open(asset_path('leaderboard/first_page/avatar_bg.png')).convert('RGBA')
    first_level_scale = 0.8
    crown_1 = Image.open(asset_path("leaderboard/first_page/crown_1.png"))
    crown_2 = Image.open(asset_path("leaderboard/first_page/crown_2.png"))
    crown_3 = Image.open(asset_path("leaderboard/first_page/crown_3.png"))
    crown_gap = int(scale * 10)

    first_top_gap = int(scale * 20)

    top_name_font = inter_font('Bold', size=int(scale * 30))
    top_name_colour = '#DDB21D'
    top_hours_font = inter_font('Medium', size=int(scale * 30))
    top_hours_colour = '#FFFFFF'
    top_text_sep = int(scale * 5)

    # Other page constants
    other_bg_path = asset_path("leaderboard/other_page/bg.png")
    other_header_bg_path = asset_path("leaderboard/other_page/header.png")
    other_header_gap = int(scale * 20)

    # Entry constants
    entry_font = inter_font("SemiBold", size=int(scale * 45))
    entry_colour = '#FFFFFF'
    entry_position_at = int(scale * 200)
    entry_name_at = int(scale * 300)
    entry_time_at = -int(scale * 150)

    entry_bg = Image.open(asset_path("leaderboard/entry_bg.png"))
    entry_highlight_bg = Image.open(asset_path("leaderboard/entry_highlight_bg.png"))
    entry_mask = Image.open(asset_path("leaderboard/entry_avatar_mask.png"))

    entry_gap = int(scale * 13)

    def __init__(self, server_name, entries, highlight=None):
        self.server_name = server_name
        self.entries = entries
        self.highlight = highlight
        self.first_page = any(entry.position in (1, 2, 3) for entry in entries)

    def draw(self) -> Image:
        if self.first_page:
            return self._draw_first_page()
        else:
            return self._draw_other_page()

    def _draw_first_page(self) -> Image:
        # Collect background
        image = Image.open(self.first_bg_path)
        draw = ImageDraw.Draw(image)

        # Draw header background
        header_background = Image.open(self.first_header_bg_path)
        image.alpha_composite(
            header_background,
            self.first_header_bg_position
        )

        xpos, ypos = 0, 0

        # Draw the header text
        ypos += self.header_text_pre_gap
        header = self._draw_header_text()
        image.alpha_composite(
            header,
            (xpos + (image.width // 2 - header.width // 2),
             ypos)
        )
        ypos += header.height + self.header_gap

        # Draw the top 3
        first_entry = self.entries[0]
        first = self._draw_first(first_entry, level=1)
        first_x = (image.width - first.width) // 2
        image.alpha_composite(
            first,
            (first_x, ypos)
        )
        first_text_y = ypos + first.height + self.first_top_gap
        text_y = first_text_y
        text_x = first_x + (first.width // 2)
        draw.text(
            (text_x, text_y),
            '1ST',
            font=self.top_name_font,
            fill=self.top_name_colour,
            anchor='mt'
        )
        text_y += self.top_name_font.getsize('1ST')[1] + self.top_text_sep
        draw.text(
            (text_x, text_y),
            first_entry.name,
            font=self.top_name_font,
            fill=self.top_name_colour,
            anchor='mt'
        )
        text_y += self.top_name_font.getsize(first_entry.name)[1] + self.top_text_sep
        draw.text(
            (text_x, text_y),
            "{} hours".format(first_entry.time // 3600),
            font=self.top_hours_font,
            fill=self.top_hours_colour,
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
                font=self.top_name_font,
                fill=self.top_name_colour,
                anchor='mt'
            )
            text_y += self.top_name_font.getsize('2ND')[1] + self.top_text_sep
            draw.text(
                (text_x, text_y),
                second_entry.name,
                font=self.top_name_font,
                fill=self.top_name_colour,
                anchor='mt'
            )
            text_y += self.top_name_font.getsize(second_entry.name)[1] + self.top_text_sep
            draw.text(
                (text_x, text_y),
                "{} hours".format(second_entry.time // 3600),
                font=self.top_hours_font,
                fill=self.top_hours_colour,
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
                '3ND',
                font=self.top_name_font,
                fill=self.top_name_colour,
                anchor='mt'
            )
            text_y += self.top_name_font.getsize('3ND')[1] + self.top_text_sep
            draw.text(
                (text_x, text_y),
                third_entry.name,
                font=self.top_name_font,
                fill=self.top_name_colour,
                anchor='mt'
            )
            text_y += self.top_name_font.getsize(third_entry.name)[1] + self.top_text_sep
            draw.text(
                (text_x, text_y),
                "{} hours".format(third_entry.time // 3600),
                font=self.top_hours_font,
                fill=self.top_hours_colour,
                anchor='mt'
            )

        # Draw the entries
        xpos = (image.width - self.entry_bg.width) // 2
        ypos = header_background.height + self.header_bg_gap

        for entry in self.entries[3:]:
            entry_image = self._draw_entry(
                entry,
                highlight=self.highlight and (entry.position == self.highlight)
            )
            image.alpha_composite(
                entry_image,
                (xpos, ypos)
            )
            ypos += self.entry_bg.height + self.entry_gap

        return image

    def _draw_other_page(self) -> Image:
        # Collect backgrounds
        background = Image.open(self.other_bg_path).convert('RGBA')
        header_bg = Image.open(self.other_header_bg_path).convert('RGBA')

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
        xpos = (background.width - self.entry_bg.width) // 2
        ypos = (background.height - 10 * self.entry_bg.height - 9 * self.entry_gap) // 2

        for entry in self.entries:
            entry_image = self._draw_entry(
                entry,
                highlight=self.highlight and (entry.position == self.highlight)
            )
            background.alpha_composite(
                entry_image,
                (xpos, ypos)
            )
            ypos += self.entry_bg.height + self.entry_gap

        # Combine images
        image = Image.new(
            'RGBA',
            (
                background.width,
                header_bg.height + self.other_header_gap + background.height
            )
        )
        image.alpha_composite(
            header_bg,
            (0, 0)
        )
        image.alpha_composite(
            background,
            (0, header_bg.height + self.other_header_gap)
        )
        return image

    def _draw_entry(self, entry, highlight=False) -> Image:
        # Get the appropriate background
        image = (self.entry_bg if not highlight else self.entry_highlight_bg).copy()
        draw = ImageDraw.Draw(image)
        ypos = image.height // 2

        # Mask the avatar, if it exists
        avatar = entry.image
        avatar.thumbnail((187, 187))
        avatar.paste((0, 0, 0, 0), mask=self.entry_mask)

        # Paste avatar onto image
        image.alpha_composite(avatar, (0, 0))

        # Write position
        draw.text(
            (self.entry_position_at, ypos),
            str(entry.position),
            fill=self.entry_colour,
            font=self.entry_font,
            anchor='mm'
        )

        # Write name
        draw.text(
            (self.entry_name_at, ypos),
            entry.name,
            fill=self.entry_colour,
            font=self.entry_font,
            anchor='lm'
        )

        # Write time
        time_str = "{:02d}:{:02d}".format(
            entry.time // 3600,
            (entry.time % 3600) // 60
        )
        draw.text(
            (image.width + self.entry_time_at, ypos),
            time_str,
            fill=self.entry_colour,
            font=self.entry_font,
            anchor='mm'
        )

        return image

    def _draw_first(self, entry, level) -> Image:
        if level == 1:
            crown = self.crown_1
        elif level == 2:
            crown = self.crown_2
        elif level == 3:
            crown = self.crown_3

        image = Image.new(
            'RGBA',
            (self.first_avatar_bg.width,
             crown.height + self.crown_gap
             + self.first_avatar_mask.height
             + (self.first_avatar_bg.height - self.first_avatar_mask.height) // 2)
        )

        # Retrieve and mask avatar
        # TODO: Upscale avatar if required
        avatar = entry.image
        avatar.paste((0, 0, 0, 0), mask=self.first_avatar_mask.convert('RGBA'))

        # Paste on the background
        image.paste(
            self.first_avatar_bg,
            (0, image.height - self.first_avatar_bg.height)
        )

        # Paste on the avatar
        image.alpha_composite(
            avatar,
            (
                (self.first_avatar_bg.width - avatar.width) // 2,
                image.height - self.first_avatar_bg.height +
                (self.first_avatar_bg.height - avatar.height) // 2
            )
        )

        image.alpha_composite(
            crown,
            ((image.width - crown.width) // 2, 0)
        )

        # Downscale depending on ranking
        if level in (2, 3):
            new_height = int(image.height * self.first_level_scale)
            image.thumbnail((new_height, new_height))

        return image

    def _draw_header_text(self) -> Image:
        image = Image.new(
            'RGBA',
            (self.header_text_size[0],
             self.header_text_size[1] + self.header_text_gap + self.header_text_line_width
             + self.header_text_line_gap
             + self.subheader_name_font.getsize("THIS MONTH")[1]),
        )
        draw = ImageDraw.Draw(image)
        xpos, ypos = 0, 0

        # Draw the top text
        draw.text(
            (0, 0),
            self.header_text,
            font=self.header_text_font,
            fill=self.header_text_colour
        )
        ypos += self.header_text_size[1] + self.header_text_gap

        # Draw the underline
        draw.line(
            (xpos, ypos,
             xpos + self.header_text_size[0], ypos),
            fill=self.header_text_colour,
            width=self.header_text_line_width
        )
        ypos += self.header_text_line_gap

        # Draw the subheader
        text_name = "SERVER: "
        text_name_width = self.subheader_name_font.getlength(text_name)
        text_value = self.server_name
        text_value_width = self.subheader_value_font.getlength(text_value)
        total_width = text_name_width + text_value_width
        xpos += (image.width - total_width) // 2
        draw.text(
            (xpos, ypos),
            text_name,
            fill=self.subheader_name_colour,
            font=self.subheader_name_font
        )
        xpos += text_name_width
        draw.text(
            (xpos, ypos),
            text_value,
            fill=self.subheader_value_colour,
            font=self.subheader_value_font
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
