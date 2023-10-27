import os
import math
import pytz
import logging
from PIL import Image, ImageDraw, ImageColor
from datetime import timedelta, datetime, timezone

from babel.translator import LocalBabel
from babel.utils import local_month

from ..utils import resolve_asset_path, font_height, getsize
from ..base import Card, Layout, fielded, Skin, CardMode
from ..base.Skin import (
    AssetField, RGBAAssetField, AssetPathField, BlobField, StringField, NumberField, PointField, RawField,
    FontField, ColourField, ComputedField, FieldDesc, LazyStringField
)

logger = logging.getLogger(__name__)
babel = LocalBabel('weekly-gui')
_p, _np = babel._p, babel._np

SECONDSINDAY = 60 * 60 * 24


def localise_timestamp(timestamp: int, tz: timezone):
    """
    Create a datetime object for the given UTC timestamp,
    localised into the given timezone.
    """
    time = datetime.utcfromtimestamp(timestamp)
    time = time.replace(tzinfo=timezone.utc)
    time = time.astimezone(tz)
    return time


@fielded
class WeeklyStatsSkin(Skin):
    _env = {
        'scale': 1  # General size scale to match background resolution
    }

    mode: RawField = CardMode.TEXT
    font_family: RawField = 'Inter'

    background: AssetField = 'weekly/background.png'

    # Header
    title_pre_gap: NumberField = 40

    study_title_text: LazyStringField = _p(
        'skin:weeklystats|mode:study|title',
        "STUDY HOURS"
    )
    voice_title_text: LazyStringField = _p(
        'skin:weeklystats|mode:voice|title',
        "VOICE CHANNEL ACTIVITY"
    )
    text_title_text: LazyStringField = _p(
        'skin:weeklystats|mode:text|title',
        "MESSAGE ACTIVITY"
    )
    anki_title_text: LazyStringField = _p(
        'skin::weeklystats|mode:anki|title',
        "CARDS REVIEWED"
    )
    title_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_title_text,
        CardMode.VOICE: skin.voice_title_text,
        CardMode.TEXT: skin.text_title_text,
        CardMode.ANKI: skin.anki_title_text,
    }[skin.mode]
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: getsize(skin.title_font, skin.title_text)

    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 5
    title_gap: NumberField = 50

    # Top
    top_grid_x: NumberField = 150
    top_grid_y: NumberField = 100

    top_hours_font: FontField = ('Bold', 36.35)
    top_hours_colour: ColourField = '#FFFFFF'

    top_hours_bg_mask: AssetField = 'weekly/hours_bg_mask.png'
    top_hours_bg_colour: ColourField = '#0B465E'  # TODO: Check this
    top_hours_bg_colour_override: ColourField = None
    top_hours_bg: BlobField = FieldDesc(
        BlobField,
        mask_field='top_hours_bg_mask',
        colour_field='top_hours_bg_colour',
        colour_field_override='top_hours_bg_colour_override'
    )

    top_hours_sep: NumberField = 100

    top_line_width: NumberField = 10
    top_line_colour: ColourField = '#042231'

    top_weekday_pre_gap: NumberField = 20
    top_weekday_font: FontField = ('Bold', 36.35)
    top_weekday_colour: ColourField = '#FFFFFF'
    top_weekday_height: ComputedField = lambda skin: font_height(skin.top_weekday_font)
    top_weekday_gap: NumberField = 5
    top_date_font: FontField = ('SemiBold', 30)
    top_date_colour: ColourField = '#808080'
    top_date_height: ComputedField = lambda skin: font_height(skin.top_date_font)

    top_bar_mask: RGBAAssetField = 'weekly/top_bar_mask.png'

    top_this_colour: ColourField = '#DDB21D'
    top_this_color_override: ColourField = None

    top_last_colour: ColourField = '#377689CC'
    top_last_color_override: ColourField = None

    top_this_bar_full: BlobField = FieldDesc(
        BlobField,
        mask_field='top_bar_mask',
        colour_field='top_this_colour',
        colour_field_override='top_this_colour_override'
    )

    top_last_bar_full: BlobField = FieldDesc(
        BlobField,
        mask_field='top_bar_mask',
        colour_field='top_last_colour',
        colour_field_override='top_last_colour_override'
    )

    top_gap: NumberField = 80

    weekdays_text: LazyStringField = _p(
        'skin:weeklystats|weekdays',
        "M,T,W,T,F,S,S"
    )
    weekdays: ComputedField = lambda skin: skin.weekdays_text.split(',')

    # Bottom
    btm_bar_horiz_colour: ColourField = "#052B3B93"
    btm_bar_vert_colour: ColourField = "#042231B2"
    btm_weekly_background_size: PointField = (66, 400)
    btm_weekly_background_colour: ColourField = '#06324880'
    btm_weekly_background: ComputedField = lambda skin: (
        Image.new(
            'RGBA',
            skin.btm_weekly_background_size,
            color=ImageColor.getrgb(skin.btm_weekly_background_colour)
        )
    )

    btm_timeline_end_mask: RGBAAssetField = 'weekly/timeline_end_mask.png'

    btm_this_colour: ColourField = '#DDB21D'
    btm_this_colour_override: ColourField = None
    btm_this_end: BlobField = FieldDesc(
        BlobField,
        mask_field='btm_timeline_end_mask',
        colour_field='btm_this_colour',
        colour_override_field='btm_this_colour_override'
    )

    btm_last_colour: ColourField = '#5E6C747F'
    btm_last_colour_override: ColourField = None
    btm_last_end: BlobField = FieldDesc(
        BlobField,
        mask_field='btm_timeline_end_mask',
        colour_field='btm_last_colour',
        colour_override_field='btm_last_colour_override'
    )

    btm_horiz_width: ComputedField = lambda skin: skin.btm_this_end.height
    btm_sep: ComputedField = lambda skin: (skin.btm_weekly_background_size[1] - 7 * skin.btm_horiz_width) // 6

    btm_vert_width: NumberField = 10

    btm_grid_x: NumberField = 48
    btm_grid_y: ComputedField = lambda skin: skin.btm_horiz_width + skin.btm_sep

    btm_weekday_font: FontField = ('Bold', 36.35)
    btm_weekday_colour: ColourField = '#FFFFFF'

    btm_day_font: FontField = ('SemiBold', 31)
    btm_day_colour: ColourField = '#FFFFFF'
    btm_day_height: ComputedField = lambda skin: font_height(skin.btm_day_font)
    btm_day_gap: NumberField = 15

    btm_emoji_path: StringField = "weekly/emojis"
    btm_emojis: ComputedField = lambda skin: {
        state: Image.open(
            resolve_asset_path(
                skin._env['PATH'],
                os.path.join(skin.btm_emoji_path, f"{state}.png")
            )
        ).convert('RGBA')
        for state in ('very_happy', 'happy', 'neutral', 'sad', 'shocked')
    }

    # Summary
    summary_pre_gap: NumberField = 50
    summary_mask: AssetField = 'weekly/summary_mask.png'

    study_this_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:study|summary:this_week',
        "THIS WEEK: {amount} HOURS"
    )
    voice_this_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:voice|summary:this_week',
        "THIS WEEK: {amount} HOURS"
    )
    text_this_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:text|summary:this_week',
        "THIS WEEK: {amount} MESSAGES"
    )
    anki_this_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:text|summary:this_week',
        "THIS WEEK: {amount} CARDS"
    )
    this_week_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_this_week_text,
        CardMode.VOICE: skin.voice_this_week_text,
        CardMode.TEXT: skin.text_this_week_text,
        CardMode.ANKI: skin.anki_this_week_text,
    }[skin.mode]
    this_week_font: FontField = ('Light', 23)
    this_week_colour: ColourField = '#BABABA'
    this_week_image: BlobField = FieldDesc(
        BlobField,
        mask_field='summary_mask',
        colour_field='top_this_colour',
        colour_field_override='top_this_colour_override'
    )

    summary_sep: NumberField = 300

    study_last_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:study|summary:last_week',
        "LAST WEEK: {amount} HOURS"
    )
    voice_last_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:voice|summary:last_week',
        "LAST WEEK: {amount} HOURS"
    )
    text_last_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:text|summary:last_week',
        "LAST WEEK: {amount} MESSAGES"
    )
    anki_last_week_text: LazyStringField = _p(
        'skin:weeklystats|mode:text|summary:last_week',
        "LAST WEEK: {amount} CARDS"
    )
    last_week_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_last_week_text,
        CardMode.VOICE: skin.voice_last_week_text,
        CardMode.TEXT: skin.text_last_week_text,
        CardMode.ANKI: skin.anki_last_week_text,
    }[skin.mode]
    last_week_font: FontField = ('Light', 23)
    last_week_colour: ColourField = '#BABABA'
    last_week_image: BlobField = FieldDesc(
        BlobField,
        mask_field='summary_mask',
        colour_field='top_last_colour',
        colour_field_override='top_last_colour_override'
    )

    # Date text
    footer_text: LazyStringField = _p(
        'skin:weeklystats|footer',
        "Weekly Statistics • As of {day} {month} • {name} {discrim}"
    )
    footer_font: FontField = ('Bold', 28)
    footer_colour: ColourField = '#6f6e6f'
    footer_gap: NumberField = 50


class WeeklyStatsPage(Layout):
    def __init__(
        self,
        skin: WeeklyStatsSkin,
        user: tuple[str, str], timezone: str,
        now: int, week: int,
        daily: list[float], sessions: list[tuple[int, int]],
        **kwargs
    ):
        """
        skin: WeeklyStatsSkin
        user: tuple[str, str]
            Name and discriminator of the user who owns this card.
        timezone: str
            A valid pytz timezone to localise the sessions.
        now: int
            The UTC timestamp at which the data was calculated.
        week: int
            The UTC timestamp of the start of the week.
        daily: list[float]
            List of 14 integers describing totals for each day of last week and this week.
        sessions: list[tuple[int, int]]
            List of (start_ts, end_ts) tuples describing each session through this and last week, in ascending order.
            This is used to create the timeline (bottom) graph.
            This is not used for summary statistics.
        """
        self.skin = skin

        # Save the raw data
        self.data_name, self.data_discrim = user
        self.data_timezone = timezone
        self.data_now = now
        self.data_week = week
        self.data_daily = daily
        self.data_sessions = sessions

        # The user's timezone
        self.timezone = pytz.timezone(timezone)
        self.now = datetime.utcfromtimestamp(now).replace(tzinfo=pytz.utc).astimezone(self.timezone)

        # The start times of each of 15 days, localised into the correct timezone, starting from last fortnight.
        week_start = datetime.utcfromtimestamp(week).replace(tzinfo=pytz.utc).astimezone(self.timezone)
        self.day_starts = [
            week_start + timedelta(days=diff)
            for diff in range(-7, 8)
        ]
        logger.debug(f"Day starts: {self.day_starts}, timezone {self.timezone}, provided {timezone}")

        self.periods = self.extract_periods()

        # Top graph labels and scale
        self.max_daily = (4 * math.ceil(max(self.data_daily) / 4)) or 4
        self.date_labels = [
            (week_start + timedelta(days=i)).strftime('%d/%m')
            for i in range(0, 7)
        ]

        # Drawing state
        self.image = None

    def extract_periods(self) -> list[list[tuple[int, int]]]:
        """
        Extract a list of daily activity periods from the session data.
        """
        # Ensure the sessions are start-time sorted
        sessions = sorted(self.data_sessions, key=lambda tup: tup[0])

        periods = [[] for _ in range(14)]
        day = 0  # Index of the current day, relative to start of fortnight, from 0 to 13
        i = 0  # Index of the current session in the session list
        last_period = None  # Previous period read for the current day

        while i < len(sessions) and day < 14:
            session = sessions[i]
            start = localise_timestamp(session[0], self.timezone)
            end = localise_timestamp(session[1], self.timezone)
            day_start, day_end = self.day_starts[day:day+2]

            if end <= day_start:
                # Prehistoric session, ignore
                i += 1
            elif start >= day_end:
                # Advance to next day
                day += 1
                last_period = None
            else:
                # We have a valid period to add in this day
                # Intersect session with day
                logger.debug(f"Adding {start} to {end}")
                period = (
                    (start.hour * 3600 + start.minute * 60 + start.second) if start > day_start else 0,
                    (end.hour * 3600 + end.minute * 60 + end.second) if end <= day_end else SECONDSINDAY
                )
                if last_period is not None and last_period[1] >= period[0] - 30 * 60:
                    period = (
                        min(last_period[0], period[0]),
                        max(last_period[1], period[1])
                    )
                    periods[day][-1] = period
                    logger.debug(f"Modified last period: {period}")
                else:
                    periods[day].append(period)
                    logger.debug(f"Added period: {period}")

                last_period = period

                if end <= day_end:
                    # Consumed this session, move to next session
                    i += 1
                else:
                    last_period = None
                    day += 1

        # Clear any periods that are under 20 minutes long
        for day_periods in periods:
            day_periods = [period for period in day_periods if period[1] - period[0] > 20 * 60]

        return periods

    def draw(self) -> Image:
        image = self.skin.background
        self.image = image

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
        ypos += self.skin.title_size[1] + self.skin.title_gap
        # ypos += title_size[1] + self.skin.title_underline_gap
        # draw.line(
        #     (xpos, ypos, xpos + title_size[0], ypos),
        #     fill=self.skin.title_colour,
        #     width=self.skin.title_underline_width
        # )
        # ypos += self.skin.title_underline_width + self.skin.title_gap

        # Draw the top box
        top = self.draw_top()
        image.alpha_composite(
            top,
            ((image.width - top.width) // 2, ypos)
        )

        ypos += top.height + self.skin.top_gap

        # Draw the bottom box
        bottom = self.draw_bottom()
        image.alpha_composite(
            bottom,
            ((image.width - bottom.width) // 2, ypos)
        )
        ypos += bottom.height + self.skin.summary_pre_gap

        # Draw the summaries
        summary_image = self.draw_summaries()
        image.alpha_composite(
            summary_image,
            ((image.width - summary_image.width) // 2, ypos)
        )

        # Draw the footer
        ypos = image.height
        ypos -= self.skin.footer_gap
        date_text = self.skin.footer_text.format(
            day=self.now.day,
            month=local_month(self.now.month, short=True),
            name=self.data_name,
            discrim=self.data_discrim
        )
        size = getsize(self.skin.footer_font, date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.skin.footer_font,
            fill=self.skin.footer_colour
        )
        return image

    def draw_summaries(self) -> Image:
        this_week_text = ' ' + self.skin.this_week_text.format(amount=int(sum(self.data_daily[7:])))
        this_week_length = int(self.skin.this_week_font.getlength(this_week_text))
        last_week_text = ' ' + self.skin.last_week_text.format(amount=int(sum(self.data_daily[:7])))
        last_week_length = int(self.skin.last_week_font.getlength(last_week_text))

        image = Image.new(
            'RGBA',
            (
                self.skin.this_week_image.width + this_week_length
                + self.skin.summary_sep
                + self.skin.last_week_image.width + last_week_length,
                self.skin.this_week_image.height
            )
        )
        draw = ImageDraw.Draw(image)

        xpos = 0
        ypos = image.height // 2
        image.alpha_composite(
            self.skin.this_week_image,
            (0, 0)
        )
        xpos += self.skin.this_week_image.width
        draw.text(
            (xpos, ypos),
            this_week_text,
            fill=self.skin.this_week_colour,
            font=self.skin.this_week_font,
            anchor='lm'
        )

        xpos += self.skin.summary_sep + this_week_length

        image.alpha_composite(
            self.skin.last_week_image,
            (xpos, 0)
        )
        xpos += self.skin.last_week_image.width
        draw.text(
            (xpos, ypos),
            last_week_text,
            fill=self.skin.last_week_colour,
            font=self.skin.last_week_font,
            anchor='lm'
        )
        return image

    def draw_hours_bg(self) -> Image:
        """
        Draw a dynamically sized blob for the background of the hours axis in the top graph.
        """
        blob = self.skin.top_hours_bg
        font = self.skin.top_hours_font

        labels = list(int(i * self.max_daily // 4) for i in range(0, 5))
        max_width = int(max(font.getlength(str(label)) for label in labels))
        window = int(blob.width * 5/8)

        if max_width > window:
            shift = max_width - window

            image = Image.new('RGBA', (blob.width + shift, blob.height))
            image.paste(blob, (0, 0))
            image.alpha_composite(blob, (shift, 0))
        else:
            image = blob

        return image

    def draw_top(self) -> Image:
        top_hours_bg = self.draw_hours_bg()
        size_x = (
            top_hours_bg.width // 2 + self.skin.top_hours_sep
            + 6 * self.skin.top_grid_x + self.skin.top_bar_mask.width // 2
            + top_hours_bg.width // 2
        )
        size_y = (
            top_hours_bg.height // 2 + 4 * self.skin.top_grid_y + self.skin.top_weekday_pre_gap
            + self.skin.top_weekday_height + self.skin.top_weekday_gap + self.skin.top_date_height
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        x0 = top_hours_bg.width // 2 + self.skin.top_hours_sep
        y0 = top_hours_bg.height // 2 + 4 * self.skin.top_grid_y

        # Draw lines and numbers
        labels = list(int(i * self.max_daily // 4) for i in range(0, 5))

        xpos = x0 - self.skin.top_hours_sep
        ypos = y0
        for label in labels:
            draw.line(
                ((xpos, ypos), (image.width, ypos)),
                width=self.skin.top_line_width,
                fill=self.skin.top_line_colour
            )

            text = str(label)
            image.alpha_composite(
                top_hours_bg,
                (xpos - top_hours_bg.width // 2, ypos - top_hours_bg.height // 2)
            )
            draw.text(
                (xpos, ypos),
                text,
                fill=self.skin.top_hours_colour,
                font=self.skin.top_hours_font,
                anchor='mm'
            )
            ypos -= self.skin.top_grid_y

        # Draw dates
        xpos = x0
        ypos = y0 + self.skin.top_weekday_pre_gap
        for letter, datestr in zip(self.skin.weekdays, self.date_labels):
            draw.text(
                (xpos, ypos),
                letter,
                fill=self.skin.top_weekday_colour,
                font=self.skin.top_weekday_font,
                anchor='mt'
            )
            draw.text(
                (xpos, ypos + self.skin.top_weekday_height + self.skin.top_weekday_gap),
                datestr,
                fill=self.skin.top_date_colour,
                font=self.skin.top_date_font,
                anchor='mt'
            )
            xpos += self.skin.top_grid_x

        # Draw bars
        for i, (last_hours, this_hours) in enumerate(zip(self.data_daily[:7], self.data_daily[7:])):
            day = i % 7
            xpos = x0 + day * self.skin.top_grid_x

            for draw_last in (last_hours > this_hours, not last_hours > this_hours):
                hours = last_hours if draw_last else this_hours
                height = (4 * self.skin.top_grid_y) * (hours / self.max_daily)
                height = int(height)

                if height >= self.skin.top_grid_y / 4:
                    bar = self.draw_vertical_bar(
                        height,
                        self.skin.top_last_bar_full if draw_last else self.skin.top_this_bar_full,
                        self.skin.top_bar_mask
                    )
                    image.alpha_composite(
                        bar,
                        (xpos - bar.width // 2, y0 - bar.height)
                    )

        return image

    def draw_vertical_bar(self, height, full_bar, mask_bar, crop=False):
        y_2 = mask_bar.height
        y_1 = height

        image = Image.new('RGBA', full_bar.size)
        image.paste(mask_bar, (0, y_2 - y_1), mask=mask_bar)
        image.paste(full_bar, mask=image)

        if crop:
            image = image.crop(
                (0, y_2 - y_1), (image.width, y_2 - y_1),
                (image.height, 0), (image.height, image.width)
            )

        return image

    def draw_horizontal_bar(self, length, full_bar, mask_bar, crop=False):
        x_2 = mask_bar.length
        x_1 = length

        image = Image.new('RGBA', full_bar.size)
        image.paste(mask_bar, (x_2 - x_1, 0), mask=mask_bar)
        image.paste(full_bar, mask=image)

        if crop:
            image = image.crop(
                (x_2 - x_1, 0), (image.width, 0),
                (x_2 - x_1, image.height), (image.width, image.height)
            )

        return image

    def draw_bottom(self) -> Image:
        size_x = int(
            self.skin.btm_weekly_background_size[0]
            + self.skin.btm_grid_x * 25
            + self.skin.btm_day_font.getlength('24') // 2
            + self.skin.btm_vert_width // 2
        )
        size_y = int(
            7 * self.skin.btm_horiz_width + 6 * self.skin.btm_sep
            + self.skin.btm_day_gap
            + self.skin.btm_day_height
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        # Grid origin
        x0 = self.skin.btm_weekly_background_size[0] + self.skin.btm_vert_width // 2 + self.skin.btm_grid_x
        y0 = self.skin.btm_day_gap + self.skin.btm_day_height + self.skin.btm_horiz_width // 2

        # Draw the hours
        ypos = y0 - self.skin.btm_horiz_width // 2 - self.skin.btm_day_gap
        for i in range(-1, 25):
            xpos = x0 + i * self.skin.btm_grid_x
            if i >= 0:
                draw.text(
                    (xpos, ypos),
                    str(i),
                    fill=self.skin.btm_day_colour,
                    font=self.skin.btm_day_font,
                    anchor='ms'
                )

            draw.line(
                (
                    (xpos, y0 - self.skin.btm_horiz_width // 2),
                    (xpos, image.height)
                ),
                fill=self.skin.btm_bar_vert_colour,
                width=self.skin.btm_vert_width
            )

        # Draw the day bars
        bar_image = Image.new(
            'RGBA',
            (image.width, self.skin.btm_horiz_width),
            self.skin.btm_bar_horiz_colour
        )
        for i in range(0, 7):
            ypos = y0 + i * self.skin.btm_grid_y - self.skin.btm_horiz_width // 2
            image.alpha_composite(
                bar_image,
                (0, ypos)
            )

        # Draw the weekday background
        image.alpha_composite(
            self.skin.btm_weekly_background,
            (0, y0 - self.skin.btm_horiz_width // 2)
        )

        # Draw the weekdays
        xpos = self.skin.btm_weekly_background_size[0] // 2
        for i, l in enumerate(self.skin.weekdays):
            ypos = y0 + i * self.skin.btm_grid_y
            draw.text(
                (xpos, ypos),
                l,
                font=self.skin.btm_weekday_font,
                fill=self.skin.btm_weekday_colour,
                anchor='mm'
            )

        # Draw the sessions
        seconds_in_day = SECONDSINDAY
        day_width = 24 * self.skin.btm_grid_x
        for i, day in enumerate(reversed(self.periods)):
            last = (i // 7)
            ypos = y0 + (6 - i % 7) * self.skin.btm_grid_y

            for start, end in day:
                flat_start = (start == 0)
                duration = end - start
                xpos = x0 + int(start * day_width / seconds_in_day)

                flat_end = (end == seconds_in_day)

                if flat_end:
                    width = image.width - xpos
                else:
                    width = int(duration * day_width / seconds_in_day)

                bar = self.draw_timeline_bar(
                    width,
                    last=last,
                    flat_start=flat_start,
                    flat_end=flat_end
                )

                image.alpha_composite(
                    bar,
                    (xpos, ypos - bar.height // 2)
                )

        # Draw the emojis
        xpos = x0 - self.skin.btm_grid_x // 2
        average_study = sum(self.data_daily[7:]) / 7
        for i, hours in enumerate(self.data_daily[7:]):
            if hours:
                ypos = y0 + i * self.skin.btm_grid_y
                relative = hours / average_study
                if relative > 1:
                    state = 'very_happy'
                elif relative > 0.75:
                    state = 'happy'
                elif relative > 0.25:
                    state = 'neutral'
                else:
                    state = 'sad'
                emoji = self.skin.btm_emojis[state]
                image.alpha_composite(
                    emoji,
                    (xpos - emoji.width // 2, ypos - emoji.height // 2)
                )
        return image

    def draw_timeline_bar(self, width, last=False, flat_start=False, flat_end=False) -> Image:
        # logger.debug(
        #     f"Drawing timeline bar with width={width}, last={last}, flat_start={flat_start}, flat_end={flat_end}"
        # )
        if last:
            end = self.skin.btm_last_end
            colour = self.skin.btm_last_colour
        else:
            end = self.skin.btm_this_end
            colour = self.skin.btm_this_colour

        if width < (end.width):
            width = end.width
            flat_start = True
            flat_end = True

        image = Image.new(
            'RGBA',
            (width, end.height)
        )
        draw = ImageDraw.Draw(image)

        # Draw endpoints
        if not flat_start:
            image.alpha_composite(
                end,
                (0, 0)
            )

        if not flat_end:
            image.alpha_composite(
                end,
                (width - end.width, 0)
            )

        # Draw the rectangle
        rstart = (not flat_start) * (end.width // 2)
        rend = width - (not flat_end) * (end.width // 2)
        if rstart < rend:
            draw.rectangle(
                ((rstart, 0), (rend, image.height)),
                fill=colour,
                width=0
            )

        return image


class WeeklyStatsCard(Card):
    route = 'weekly_stats_card'
    card_id = 'weekly_stats'

    layout = WeeklyStatsPage
    skin = WeeklyStatsSkin

    display_name = _p(
        'card:weekly_stats|display_name',
        "Weekly Stats"
    )

    @classmethod
    async def sample_args(cls, ctx, **kwargs):
        import random
        sessions = []
        now = datetime.now(tz=timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = day_start - timedelta(days=day_start.weekday())
        day_start -= timedelta(hours=24) * 14
        for day in range(0, 14):
            day_start += timedelta(hours=24)

            # start of day
            pointer = int(abs(random.normalvariate(6 * 60, 1 * 60)))
            while pointer < 20 * 60:
                session_duration = int(abs(random.normalvariate(4 * 60, 1 * 60)))
                sessions.append((
                    int((day_start + timedelta(minutes=pointer)).timestamp()),
                    int((day_start + timedelta(minutes=(pointer + session_duration))).timestamp()),
                ))
                pointer += session_duration
                pointer += int(abs(random.normalvariate(2.5 * 60, 1 * 60)))

        return {
            'user': (
                ctx.author.name if ctx else "John Doe",
                ('#' + ctx.author.discriminator) if ctx else "#0000"
            ),
            'timezone': 'UTC',
            'now': int(now.timestamp()),
            'week': int(week_start.timestamp()),
            'daily': [12 * i for i in [6, 8, 4.5, 7, 9, 2, 0, 1, 2, 5, 9, 3, 10, 10]],
            'sessions': sessions,
        }
