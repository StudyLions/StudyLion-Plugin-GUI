from PIL import Image, ImageFont, ImageDraw
from ..utils import asset_path, inter_font


class ProfileCard:
    # Drawing constant or default values
    scale = 2  # General size scale to match background resolution

    # Background images
    bg_path = asset_path("profile/background.png")

    # Inner container
    container_position = (70, 50)  # Position of top left corner
    container_size = (1400, 575)  # Size of the inner container

    # Header
    header_font = inter_font('BlackItalic', size=int(scale*28))
    header_colour_1 = '#DDB21D'
    header_colour_2 = '#BABABA'
    header_gap = int(scale * 35)
    header_height = header_font.getsize("USERNAME #0000")[1]

    # Column 1
    avatar_mask = Image.open(asset_path('profile/avatar_mask.png'))
    avatar_outline = Image.open(asset_path('profile/avatar_outline.png'))
    avatar_size = avatar_outline.size
    avatar_gap = int(scale * 10)

    coin_icon = Image.open(asset_path('profile/coin.png'))
    coin_font = inter_font('Black', size=int(scale*14))
    coin_colour = '#DDB21D'
    coin_sep = int(scale * 5)
    coin_gap = int(scale * 15)

    answers_font = inter_font('Black', size=int(scale*12))
    answers_colour = '#FFFFFF'
    answers_height = answers_font.getsize('ANSWERS')[1]
    answers_gap = int(scale * 10)
    attendance_font = answers_font
    attendance_colour = answers_colour
    attendance_icon_happy = Image.open(asset_path('profile/attendance_happy.png'))
    attendance_icon_sad = Image.open(asset_path('profile/attendance_sad.png'))
    attendance_threshold = 0.8

    col1_size = (
        avatar_size[0],
        avatar_size[1] + avatar_gap
        + coin_icon.height + coin_gap
        + answers_height + answers_gap
        + attendance_icon_happy.height
    )

    column_sep = int(scale * 20)

    # Column 2
    subheader_font = inter_font('Black', size=int(scale*27))
    subheader_colour = '#DDB21D'
    subheader_height = subheader_font.getsize('PROFILE')[1]
    subheader_gap = int(scale * 15)

    col2_size = (
        container_size[0] - col1_size[0] - column_sep,
        container_size[1] - header_gap - header_height
    )

    col2_sep = int(scale * 40)  # Minimum separation between profile and achievements

    # Achievement section
    achievement_active_path = asset_path('profile/achievements_active/')
    achievement_inactive_path = asset_path('profile/achievements_inactive/')
    achievement_icon_size = (115, 96)  # Individual achievement box size
    achievement_gap = int(scale * 10)
    achievement_sep = int(scale * 0)
    achievement_size = (
        4 * achievement_icon_size[0] + 3 * achievement_sep,
        subheader_height + subheader_gap
        + 2 * achievement_icon_size[1] + 1 * achievement_gap
    )

    # Profile section
    badge_end_blob = Image.open(asset_path('profile/badge_end.png'))
    badge_font = inter_font('Black', size=int(scale*13))
    badge_text_colour = '#FFFFFF'
    badge_blob_colour = '#1473A2'
    badge_gap = int(scale * 5)
    badge_min_sep = int(scale * 5)
    profile_size = (
        col2_size[0] - achievement_size[0] - col2_sep,
        subheader_height + subheader_gap
        + 4 * badge_end_blob.height + 3 * badge_gap
    )

    # Rank section
    rank_name_font = inter_font('Black', size=int(scale*23))
    rank_name_colour = '#DDB21D'
    rank_name_height = rank_name_font.getsize('VAMPIRE')[1]
    rank_hours_font = inter_font('Light', size=int(scale*18))
    rank_hours_colour = '#FFFFFF'

    bar_gap = int(scale*5)
    bar_full = Image.open(asset_path('profile/progress_full.png'))
    bar_empty = Image.open(asset_path('profile/progress_empty.png'))

    next_rank_font = inter_font('Italic', size=int(scale*15))
    next_rank_colour = '#FFFFFF'
    next_rank_height = next_rank_font.getsize('NEXT RANK:')[1]

    rank_size = (
        col2_size[0],
        rank_name_height + bar_gap
        + bar_full.height + bar_gap
        + next_rank_height + next_rank_height // 2  # Adding height for taller glyphs
    )

    def __init__(self, name, discrim, avatar,
                 coins, time, answers, attendance,
                 badges=(),
                 achievements=(),
                 current_rank=None,
                 next_rank=None,
                 draft=False, **kwargs):
        self.draft = draft

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

    def draw(self):
        # Load/copy background
        image = Image.open(self.bg_path).convert("RGBA")

        # Draw inner container
        inner_container = self.draw_inner_container()

        # Paste inner container on background
        image.alpha_composite(inner_container, self.container_position)

        self.image = image
        return image

    def draw_inner_container(self) -> Image:
        container = Image.new('RGBA', self.container_size)
        draw = ImageDraw.Draw(container)

        if self.draft:
            draw.rectangle(((0, 0), (self.container_size[0]-1, self.container_size[1]-1)))

        position = 0

        # Draw header
        xposition = 0
        draw.text(
            (xposition, position),
            self.data_name,
            font=self.header_font,
            fill=self.header_colour_1
        )
        xposition += self.header_font.getlength(self.data_name + ' ')
        draw.text(
            (xposition, position),
            self.data_discrim,
            font=self.header_font,
            fill=self.header_colour_2
        )
        position += self.header_height + self.header_gap

        # Draw column 1
        col1 = self.draw_column_1()
        container.alpha_composite(col1, (0, position))

        # Draw column 2
        col2 = self.draw_column_2()
        container.alpha_composite(col2, (container.width - col2.width, position))

        return container

    def draw_column_1(self) -> Image:
        # Create new image for column 1
        col1 = Image.new('RGBA', self.col1_size)
        draw = ImageDraw.Draw(col1)

        if self.draft:
            draw.rectangle(((0, 0), (self.col1_size[0]-1, self.col1_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Draw avatar
        _avatar = self.data_avatar.copy()

        # Mask the avatar image to the desired shape
        _avatar.paste((0, 0, 0, 0), mask=self.avatar_mask)

        # Place the image on a larger canvas
        avatar_image = Image.new('RGBA', (264, 264))
        avatar_image.paste(_avatar, (3, 4))

        # Add the outline over the masked avatar
        avatar_image.alpha_composite(self.avatar_outline)

        # Paste onto column
        col1.alpha_composite(
            avatar_image,
            (0, position)
        )
        position += self.avatar_size[1] + self.avatar_gap

        # Draw coins
        xposition = 0
        col1.alpha_composite(
            self.coin_icon,
            (0, position)
        )
        xposition += self.coin_icon.width + self.coin_sep
        draw.text(
            (xposition, position + self.coin_icon.height // 2),
            "{:,}".format(self.data_coins),
            font=self.coin_font,
            fill=self.coin_colour,
            anchor='lm'
        )
        position += self.coin_icon.height + self.coin_gap

        # Draw answers
        draw.text(
            (0, position),
            "ANSWERS: {}".format(self.data_answers or 'N/A'),
            font=self.answers_font,
            fill=self.answers_colour,
            anchor='lm'
        )
        position += self.answers_height + self.answers_gap

        # Draw attendance
        xposition = 0
        text = "ATTENDANCE: "
        draw.text(
            (0, position),
            text,
            font=self.attendance_font,
            fill=self.attendance_colour,
            anchor='lm'
        )
        xposition += int(self.attendance_font.getlength(text))
        if self.data_attendance is None:
            draw.text(
                (xposition, position),
                'N/A',
                font=self.attendance_font,
                fill=self.attendance_colour,
                anchor='lm'
            )
        else:
            if self.data_attendance > self.attendance_threshold:
                icon = self.attendance_icon_happy
            else:
                icon = self.attendance_icon_sad

            col1.alpha_composite(
                icon,
                (xposition, position - icon.height // 2)
            )

        return col1

    def draw_column_2(self) -> Image:
        # Create new image for column 1
        col2 = Image.new('RGBA', self.col2_size)
        draw = ImageDraw.Draw(col2)

        if self.draft:
            draw.rectangle(((0, 0), (self.col2_size[0]-1, self.col2_size[1]-1)))

        # Tracking current drawing position
        position = 0
        xposition = 0

        # Draw Profile box
        profile = self.draw_profile()
        col2.paste(
            profile,
            (xposition, position)
        )
        xposition += profile.width + self.col2_sep

        # Draw Achievements box
        achievements = self.draw_achievements()
        col2.paste(
            achievements,
            (xposition, position)
        )

        # Draw ranking box
        position = self.col2_size[1] - self.rank_size[1]

        ranking = self.draw_rank()
        col2.alpha_composite(
            ranking,
            (0, position)
        )

        return col2

    def draw_profile(self) -> Image:
        profile = Image.new('RGBA', self.profile_size)
        draw = ImageDraw.Draw(profile)

        if self.draft:
            draw.rectangle(((0, 0), (self.profile_size[0]-1, self.profile_size[1]-1)))

        position = 0

        # Draw subheader
        draw.text(
            (0, position),
            'PROFILE',
            font=self.subheader_font,
            fill=self.subheader_colour
        )
        position += self.subheader_height + self.subheader_gap

        # Draw badges
        # TODO: Nicer/Smarter layout
        xposition = 0
        max_x = self.profile_size[0]

        badges = [self.draw_badge(text) for text in self.data_badges]
        for badge in badges:
            if badge.width + xposition > max_x:
                xposition = 0
                position += badge.height + self.badge_gap
            profile.paste(
                badge,
                (xposition, position)
            )
            xposition += badge.width + self.badge_min_sep

        return profile

    def draw_badge(self, text) -> Image:
        """
        Draw a single profile badge, with the given text.
        """
        text_length = self.badge_font.getsize(text)[0]

        height = self.badge_end_blob.height
        width = text_length + self.badge_end_blob.width

        badge = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))

        # Add blobs to ends
        badge.paste(
            self.badge_end_blob,
            (0, 0)
        )
        badge.paste(
            self.badge_end_blob,
            (width - self.badge_end_blob.width, 0)
        )

        # Add rectangle to middle
        draw = ImageDraw.Draw(badge)
        draw.rectangle(
            (
                (self.badge_end_blob.width // 2, 0),
                (width - self.badge_end_blob.width // 2, height),
            ),
            fill=self.badge_blob_colour,
            width=0
        )

        # Write badge text
        draw.text(
            (self.badge_end_blob.width // 2, height // 2),
            text,
            font=self.badge_font,
            fill=self.badge_text_colour,
            anchor='lm'
        )

        return badge

    def draw_achievements(self) -> Image:
        achievements = Image.new('RGBA', self.achievement_size)
        draw = ImageDraw.Draw(achievements)

        if self.draft:
            draw.rectangle(((0, 0), (self.achievement_size[0]-1, self.achievement_size[1]-1)))

        position = 0

        # Draw subheader
        draw.text(
            (0, position),
            'ACHIEVEMENTS',
            font=self.subheader_font,
            fill=self.subheader_colour
        )
        position += self.subheader_height + self.subheader_gap
        xposition = 0

        for i in range(0, 8):
            # Top left corner of grid box
            nxpos = (i % 4) * (self.achievement_icon_size[0] + self.achievement_sep)
            nypos = (i // 4) * (self.achievement_icon_size[1] + self.achievement_gap)

            # Choose the active or inactive icon as given by data
            icon_path = "{}{}.png".format(
                self.achievement_active_path if (i in self.data_achievements) else self.achievement_inactive_path,
                i + 1
            )
            icon = Image.open(icon_path).convert('RGBA')

            # Offset to top left corner of pasted icon
            xoffset = (self.achievement_icon_size[0] - icon.width) // 2
            # xoffset = 0
            yoffset = self.achievement_icon_size[1] - icon.height

            # Paste the icon
            achievements.alpha_composite(
                icon,
                (xposition + nxpos + xoffset, position + nypos + yoffset)
            )

        return achievements

    def draw_rank(self) -> Image:
        rank = Image.new('RGBA', self.rank_size)
        draw = ImageDraw.Draw(rank)

        if self.draft:
            draw.rectangle(((0, 0), (self.rank_size[0]-1, self.rank_size[1]-1)))

        position = 0

        # Draw the current rank
        if self.data_current_rank:
            rank_name, hour_1, hour_2 = self.data_current_rank

            xposition = 0
            draw.text(
                (xposition, position),
                rank_name,
                font=self.rank_name_font,
                fill=self.rank_name_colour,
            )
            name_size = self.rank_name_font.getsize(rank_name + ' ')
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
                font=self.rank_hours_font,
                fill=self.rank_hours_colour,
                anchor='lb'
            )
            position += self.bar_gap
        else:
            draw.text(
                (0, position),
                'UNRANKED',
                font=self.rank_name_font,
                fill=self.rank_name_colour,
            )
            position += self.rank_name_height + self.bar_gap
            progress = 0

        # Draw rankbar
        rankbar = self.draw_rankbar(progress)
        rank.alpha_composite(
            rankbar,
            (0, position)
        )
        position += rankbar.height + self.bar_gap

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
            font=self.next_rank_font,
            fill=self.next_rank_colour,
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
            return self.bar_empty
        elif progress == 1:
            return self.bar_full
        else:
            _bar = self.bar_empty.copy()
            x = -1 * int((1 - progress) * self.bar_full.width)
            _bar.alpha_composite(
                self.bar_full,
                (x, 0)
            )
            bar = Image.composite(_bar, self.bar_empty, self.bar_empty)
            return bar
