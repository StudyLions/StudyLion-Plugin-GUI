from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from ..utils import asset_path, inter_font

from .Card import Card
from .Avatars import avatar_manager
from .Skin import fielded, Skin, FieldDesc
from .Skin import AssetField, StringField, NumberField, FontField, ColourField, PointField, ComputedField, RawField
from .Skin import AssetPathField


@fielded
class ProfileSkin(Skin):
    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    # Background images
    bg_path: AssetField = "profile/background.png"

    # Inner container
    container_position: PointField = (70, 50)  # Position of top left corner
    container_size: PointField = (1400, 575)  # Size of the inner container

    # Header
    header_font: FontField = ('BlackItalic', 28)
    header_colour_1: ColourField = '#DDB21D'
    header_colour_2: ColourField = '#BABABA'
    header_gap: NumberField = 35
    header_height: ComputedField = lambda skin: skin.header_font.getsize("USERNAME #0000")[1]

    # Column 1
    avatar_mask: AssetField = FieldDesc(AssetField, 'profile/avatar_mask.png', convert=None)
    avatar_outline: AssetField = FieldDesc(AssetField, 'profile/avatar_outline.png', convert=None)
    avatar_size: ComputedField = lambda skin: skin.avatar_outline.size
    avatar_gap: NumberField = 10

    coin_icon: AssetField = 'profile/coin.png'
    coin_font: FontField = ('Black', 14)
    coin_colour: ColourField = '#DDB21D'
    coin_sep: NumberField = 5
    coin_gap: NumberField = 15

    answers_font: FontField = ('Black', 12)
    answers_colour: ColourField = '#FFFFFF'
    answers_height: ComputedField = lambda skin: skin.answers_font.getsize('ANSWERS')[1]
    answers_gap: NumberField = 10
    attendance_font: FontField = answers_font
    attendance_colour: ColourField = answers_colour
    attendance_icon_happy: AssetField = 'profile/attendance_happy.png'
    attendance_icon_sad: AssetField = 'profile/attendance_sad.png'
    attendance_threshold: NumberField = FieldDesc(NumberField, 0.8, scaled=False, integer=False)

    col1_size: ComputedField = lambda skin: (
        skin.avatar_size[0],
        skin.avatar_size[1] + skin.avatar_gap
        + skin.coin_icon.height + skin.coin_gap
        + skin.answers_height + skin.answers_gap
        + skin.attendance_icon_happy.height
    )

    column_sep: NumberField = 20

    # Column 2
    subheader_font: FontField = ('Black', 27)
    subheader_colour: ColourField = '#DDB21D'
    subheader_height: ComputedField = lambda skin: skin.subheader_font.getsize('PROFILE')[1]
    subheader_gap: NumberField = 15

    col2_size: ComputedField = lambda skin: (
        skin.container_size[0] - skin.col1_size[0] - skin.column_sep,
        skin.container_size[1] - skin.header_gap - skin.header_height
    )

    col2_sep: NumberField = 40  # Minimum separation between profile and achievements

    # Achievement section
    achievement_active_path: AssetPathField = 'profile/achievements_active/'
    achievement_inactive_path: AssetPathField = 'profile/achievements_inactive/'
    achievement_icon_size: PointField = (115, 96)  # Individual achievement box size
    achievement_gap: NumberField = 10
    achievement_sep: NumberField = 0
    achievement_size: ComputedField = lambda skin: (
        4 * skin.achievement_icon_size[0] + 3 * skin.achievement_sep,
        skin.subheader_height + skin.subheader_gap
        + 2 * skin.achievement_icon_size[1] + 1 * skin.achievement_gap
    )

    # Profile section
    badge_end_blob: AssetField = 'profile/badge_end.png'
    badge_font: FontField = ('Black', 13)
    badge_text_colour: ColourField = '#FFFFFF'
    badge_blob_colour: ColourField = '#1473A2'
    badge_gap: NumberField = 5
    badge_min_sep: NumberField = 5
    profile_size: ComputedField = lambda skin: (
        skin.col2_size[0] - skin.achievement_size[0] - skin.col2_sep,
        skin.subheader_height + skin.subheader_gap
        + 4 * skin.badge_end_blob.height + 3 * skin.badge_gap
    )

    # Rank section
    rank_name_font: FontField = ('Black', 23)
    rank_name_colour: ColourField = '#DDB21D'
    rank_name_height: ComputedField = lambda skin: skin.rank_name_font.getsize('VAMPIRE')[1]
    rank_hours_font: FontField = ('Light', 18)
    rank_hours_colour: ColourField = '#FFFFFF'

    bar_gap: NumberField = 5
    bar_full: AssetField = 'profile/progress_full.png'
    bar_empty: AssetField = 'profile/progress_empty.png'

    next_rank_font: FontField = ('Italic', 15)
    next_rank_colour: ColourField = '#FFFFFF'
    next_rank_height: ComputedField = lambda skin: skin.next_rank_font.getsize('NEXT RANK:')[1]

    rank_size: ComputedField = lambda skin: (
        skin.col2_size[0],
        skin.rank_name_height + skin.bar_gap
        + skin.bar_full.height + skin.bar_gap
        + skin.next_rank_height + skin.next_rank_height // 2  # Adding skin.height skin.for skin.taller skin.glyphs
    )


class ProfileCard(Card):
    server_route = 'profile_card'

    def __init__(self, name, discrim,
                 coins, time, answers, attendance,
                 avatar,
                 badges=(),
                 achievements=(),
                 current_rank=None,
                 next_rank=None,
                 draft=False, **kwargs):

        self.draft = draft

        self.skin = ProfileSkin().load()

        self.data_name = name
        self.data_discrim = discrim

        self.data_avatar = avatar

        self.data_coins = coins
        self.data_time = time
        self.data_hours = self.data_time / 3600
        self.data_answers = answers
        self.data_attendance = attendance

        self.data_badges = badges
        self.data_achievements = achievements

        self.data_current_rank = current_rank
        self.data_next_rank = next_rank

        self.image: Image = None  # Final Image

    @classmethod
    async def card_route(cls, executor, args, kwargs):
        kwargs['avatar'] = await avatar_manager().get_avatar(*kwargs['avatar'], 256)
        return await super().card_route(executor, args, kwargs)

    @classmethod
    def _execute(cls, *args, **kwargs):
        with BytesIO(kwargs['avatar']) as image_data:
            with Image.open(image_data).convert('RGBA') as avatar_image:
                kwargs['avatar'] = avatar_image
                return super()._execute(*args, **kwargs)

    def draw(self):
        # Load/copy background
        image = self.skin.bg_path

        # Draw inner container
        inner_container = self.draw_inner_container()

        # Paste inner container on background
        image.alpha_composite(inner_container, self.skin.container_position)

        self.image = image
        return image

    def draw_inner_container(self) -> Image:
        container = Image.new('RGBA', self.skin.container_size)
        draw = ImageDraw.Draw(container)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.container_size[0]-1, self.skin.container_size[1]-1)))

        position = 0

        # Draw header
        xposition = 0
        draw.text(
            (xposition, position),
            self.data_name,
            font=self.skin.header_font,
            fill=self.skin.header_colour_1
        )
        xposition += self.skin.header_font.getlength(self.data_name + ' ')
        draw.text(
            (xposition, position),
            self.data_discrim,
            font=self.skin.header_font,
            fill=self.skin.header_colour_2
        )
        position += self.skin.header_height + self.skin.header_gap

        # Draw column 1
        col1 = self.draw_column_1()
        container.alpha_composite(col1, (0, position))

        # Draw column 2
        col2 = self.draw_column_2()
        container.alpha_composite(col2, (container.width - col2.width, position))

        return container

    def draw_column_1(self) -> Image:
        # Create new image for column 1
        col1 = Image.new('RGBA', self.skin.col1_size)
        draw = ImageDraw.Draw(col1)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.col1_size[0]-1, self.skin.col1_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Draw avatar
        _avatar = self.data_avatar

        # Mask the avatar image to the desired shape
        _avatar.paste((0, 0, 0, 0), mask=self.skin.avatar_mask)

        # Place the image on a larger canvas
        avatar_image = Image.new('RGBA', (264, 264))
        avatar_image.paste(_avatar, (3, 4))

        # Add the outline over the masked avatar
        avatar_image.alpha_composite(self.skin.avatar_outline)

        # Paste onto column
        col1.alpha_composite(
            avatar_image,
            (0, position)
        )
        position += self.skin.avatar_size[1] + self.skin.avatar_gap

        # Draw coins
        xposition = 0
        col1.alpha_composite(
            self.skin.coin_icon,
            (0, position)
        )
        xposition += self.skin.coin_icon.width + self.skin.coin_sep
        draw.text(
            (xposition, position + self.skin.coin_icon.height // 2),
            "{:,}".format(self.data_coins),
            font=self.skin.coin_font,
            fill=self.skin.coin_colour,
            anchor='lm'
        )
        position += self.skin.coin_icon.height + self.skin.coin_gap

        # Draw answers
        draw.text(
            (0, position),
            "ANSWERS: {}".format(self.data_answers or 'N/A'),
            font=self.skin.answers_font,
            fill=self.skin.answers_colour,
            anchor='lm'
        )
        position += self.skin.answers_height + self.skin.answers_gap

        # Draw attendance
        xposition = 0
        text = "ATTENDANCE: "
        draw.text(
            (0, position),
            text,
            font=self.skin.attendance_font,
            fill=self.skin.attendance_colour,
            anchor='lm'
        )
        xposition += int(self.skin.attendance_font.getlength(text))
        if self.data_attendance is None:
            draw.text(
                (xposition, position),
                'N/A',
                font=self.skin.attendance_font,
                fill=self.skin.attendance_colour,
                anchor='lm'
            )
        else:
            if self.data_attendance > self.skin.attendance_threshold:
                icon = self.skin.attendance_icon_happy
            else:
                icon = self.skin.attendance_icon_sad

            col1.alpha_composite(
                icon,
                (xposition, position - icon.height // 2)
            )

        return col1

    def draw_column_2(self) -> Image:
        # Create new image for column 1
        col2 = Image.new('RGBA', self.skin.col2_size)
        draw = ImageDraw.Draw(col2)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.col2_size[0]-1, self.skin.col2_size[1]-1)))

        # Tracking current drawing position
        position = 0
        xposition = 0

        # Draw Profile box
        profile = self.draw_profile()
        col2.paste(
            profile,
            (xposition, position)
        )
        xposition += profile.width + self.skin.col2_sep

        # Draw Achievements box
        achievements = self.draw_achievements()
        col2.paste(
            achievements,
            (xposition, position)
        )

        # Draw ranking box
        position = self.skin.col2_size[1] - self.skin.rank_size[1]

        ranking = self.draw_rank()
        col2.alpha_composite(
            ranking,
            (0, position)
        )

        return col2

    def draw_profile(self) -> Image:
        profile = Image.new('RGBA', self.skin.profile_size)
        draw = ImageDraw.Draw(profile)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.profile_size[0]-1, self.skin.profile_size[1]-1)))

        position = 0

        # Draw subheader
        draw.text(
            (0, position),
            'PROFILE',
            font=self.skin.subheader_font,
            fill=self.skin.subheader_colour
        )
        position += self.skin.subheader_height + self.skin.subheader_gap

        # Draw badges
        # TODO: Nicer/Smarter layout
        xposition = 0
        max_x = self.skin.profile_size[0]

        badges = [self.draw_badge(text) for text in self.data_badges]
        for badge in badges:
            if badge.width + xposition > max_x:
                xposition = 0
                position += badge.height + self.skin.badge_gap
            profile.paste(
                badge,
                (xposition, position)
            )
            xposition += badge.width + self.skin.badge_min_sep

        return profile

    def draw_badge(self, text) -> Image:
        """
        Draw a single profile badge, with the given text.
        """
        text_length = self.skin.badge_font.getsize(text)[0]

        height = self.skin.badge_end_blob.height
        width = text_length + self.skin.badge_end_blob.width

        badge = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))

        # Add blobs to ends
        badge.paste(
            self.skin.badge_end_blob,
            (0, 0)
        )
        badge.paste(
            self.skin.badge_end_blob,
            (width - self.skin.badge_end_blob.width, 0)
        )

        # Add rectangle to middle
        draw = ImageDraw.Draw(badge)
        draw.rectangle(
            (
                (self.skin.badge_end_blob.width // 2, 0),
                (width - self.skin.badge_end_blob.width // 2, height),
            ),
            fill=self.skin.badge_blob_colour,
            width=0
        )

        # Write badge text
        draw.text(
            (self.skin.badge_end_blob.width // 2, height // 2),
            text,
            font=self.skin.badge_font,
            fill=self.skin.badge_text_colour,
            anchor='lm'
        )

        return badge

    def draw_achievements(self) -> Image:
        achievements = Image.new('RGBA', self.skin.achievement_size)
        draw = ImageDraw.Draw(achievements)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.achievement_size[0]-1, self.skin.achievement_size[1]-1)))

        position = 0

        # Draw subheader
        draw.text(
            (0, position),
            'ACHIEVEMENTS',
            font=self.skin.subheader_font,
            fill=self.skin.subheader_colour
        )
        position += self.skin.subheader_height + self.skin.subheader_gap
        xposition = 0

        for i in range(0, 8):
            # Top left corner of grid box
            nxpos = (i % 4) * (self.skin.achievement_icon_size[0] + self.skin.achievement_sep)
            nypos = (i // 4) * (self.skin.achievement_icon_size[1] + self.skin.achievement_gap)

            # Choose the active or inactive icon as given by data
            icon_path = "{}{}.png".format(
                self.skin.achievement_active_path if (i in self.data_achievements) else self.skin.achievement_inactive_path,
                i + 1
            )
            icon = Image.open(icon_path).convert('RGBA')

            # Offset to top left corner of pasted icon
            xoffset = (self.skin.achievement_icon_size[0] - icon.width) // 2
            # xoffset = 0
            yoffset = self.skin.achievement_icon_size[1] - icon.height

            # Paste the icon
            achievements.alpha_composite(
                icon,
                (xposition + nxpos + xoffset, position + nypos + yoffset)
            )

        return achievements

    def draw_rank(self) -> Image:
        rank = Image.new('RGBA', self.skin.rank_size)
        draw = ImageDraw.Draw(rank)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.rank_size[0]-1, self.skin.rank_size[1]-1)))

        position = 0

        # Draw the current rank
        if self.data_current_rank:
            rank_name, hour_1, hour_2 = self.data_current_rank

            xposition = 0
            draw.text(
                (xposition, position),
                rank_name,
                font=self.skin.rank_name_font,
                fill=self.skin.rank_name_colour,
            )
            name_size = self.skin.rank_name_font.getsize(rank_name + ' ')
            position += name_size[1]
            xposition += name_size[0]

            if hour_2:
                progress = (self.data_hours - hour_1) / (hour_2 - hour_1)
                if hour_1:
                    hour_str = '{} - {}h'.format(hour_1, hour_2)
                else:
                    hour_str = '≤{}h'.format(hour_2)
            else:
                progress = 1
                hour_str = '≥{}h'.format(hour_1)

            draw.text(
                (xposition, position),
                hour_str,
                font=self.skin.rank_hours_font,
                fill=self.skin.rank_hours_colour,
                anchor='lb'
            )
            position += self.skin.bar_gap
        else:
            draw.text(
                (0, position),
                'UNRANKED',
                font=self.skin.rank_name_font,
                fill=self.skin.rank_name_colour,
            )
            position += self.skin.rank_name_height + self.skin.bar_gap
            progress = 0

        # Draw rankbar
        rankbar = self.draw_rankbar(progress)
        rank.alpha_composite(
            rankbar,
            (0, position)
        )
        position += rankbar.height + self.skin.bar_gap

        # Draw next rank text
        if self.data_next_rank:
            rank_name, hour_1, hour_2 = self.data_next_rank
            if hour_2:
                if hour_1:
                    hour_str = '{} - {}h'.format(hour_1, hour_2)
                else:
                    hour_str = '≤{}h'.format(hour_2)
            else:
                hour_str = '≥{}h'.format(hour_1)
            rank_str = "NEXT RANK: {} {}".format(rank_name, hour_str)
        else:
            if self.data_current_rank:
                rank_str = "YOU HAVE REACHED THE MAXIMUM RANK!"
            else:
                rank_str = "NO RANKS AVAILABLE!"

        draw.text(
            (0, position),
            rank_str,
            font=self.skin.next_rank_font,
            fill=self.skin.next_rank_colour,
        )

        return rank

    def draw_rankbar(self, progress: float) -> Image:
        """
        Draw the rank progress bar with the given progress filled.
        `progress` should be given as a proportion between `0` and `1`.
        """
        # Ensure sane values
        progress = min(progress, 1)
        progress = max(progress, 0)

        if progress == 0:
            return self.skin.bar_empty
        elif progress == 1:
            return self.skin.bar_full
        else:
            _bar = self.skin.bar_empty.copy()
            x = -1 * int((1 - progress) * self.skin.bar_full.width)
            _bar.alpha_composite(
                self.skin.bar_full,
                (x, 0)
            )
            bar = Image.composite(_bar, self.skin.bar_empty, self.skin.bar_empty)
            return bar
