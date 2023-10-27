import math
import calendar
import logging
from collections import defaultdict
import pytz
from PIL import Image, ImageDraw
from datetime import timedelta, datetime, timezone

from babel.translator import LocalBabel
from babel.utils import local_month

from ..base import Card, Layout, fielded, Skin, CardMode
from ..base.Skin import (
    FieldDesc,
    AssetField, RGBAAssetField, BlobField, StringField, NumberField, RawField,
    FontField, ColourField, PointField, ComputedField, LazyStringField
)

logger = logging.getLogger(__name__)
babel = LocalBabel('monthly-gui')
_p, _np = babel._p, babel._np


@fielded
class MonthlyStatsSkin(Skin):
    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    mode: RawField = CardMode.TEXT
    font_family: RawField = "Inter"

    background: AssetField = 'monthly/background.png'

    # Header
    title_pre_gap: NumberField = 40

    study_title_text: LazyStringField = _p(
        'skin:monthlystats|mode:study|title',
        "STUDY HOURS"
    )
    voice_title_text: LazyStringField = _p(
        'skin:monthlystats|mode:voice|title',
        "VOICE CHANNEL ACTIVITY"
    )
    text_title_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|title',
        "MESSAGE ACTIVITY"
    )
    anki_title_text: LazyStringField = _p(
        'skin::monthlystats|mode:anki|title',
        "CARDS REVIEWED"
    )
    title_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_title_text,
        CardMode.VOICE: skin.voice_title_text,
        CardMode.TEXT: skin.text_title_text,
        CardMode.ANKI: skin.anki_title_text,
    }[skin.mode]
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: skin.title_font.getbbox(skin.title_text)[2:]

    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 0
    title_gap: NumberField = 10

    # Top
    top_grid_x: NumberField = 37
    top_grid_y: NumberField = 100

    top_hours_font: FontField = ('Black', 36)
    top_hours_colour: ColourField = '#FFFFFF'

    top_hours_bg_mask: AssetField = 'monthly/hours_bg_mask.png'
    top_hours_bg_colour: ColourField = '#0B465E'
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

    top_date_pre_gap: NumberField = 20
    top_date_font: FontField = ('Light', 25)
    top_date_colour: ColourField = '#FFFFFF'
    top_date_height: ComputedField = lambda skin: skin.top_date_font.getbbox('31')[-1]

    top_bar_mask: RGBAAssetField = 'monthly/bar_mask.png'

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

    study_top_hours_text: LazyStringField = _p(
        'ui:monthlystats|mode:study|bar_value',
        "{value} H"
    )
    voice_top_hours_text: LazyStringField = _p(
        'ui:monthlystats|mode:voice|bar_value',
        "{value} H"
    )
    text_top_hours_text: LazyStringField = _p(
        'ui:monthlystats|mode:text|bar_value',
        "{value} M"
    )
    anki_top_hours_text: LazyStringField = _p(
        'ui:monthlystats|mode:anki|bar_value',
        "{value} C"
    )
    top_hours_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_top_hours_text,
        CardMode.VOICE: skin.voice_top_hours_text,
        CardMode.TEXT: skin.text_top_hours_text,
        CardMode.ANKI: skin.anki_top_hours_text,
    }[skin.mode]

    top_this_hours_font: FontField = ('Medium', 20)
    top_this_hours_colour: ColourField = '#DDB21D'

    top_time_bar_sep: NumberField = 7
    top_time_sep: NumberField = 5

    top_last_hours_font: FontField = ('Medium', 20)
    top_last_hours_colour: ColourField = '#5F91A1'

    top_gap: NumberField = 40

    weekdays_text: LazyStringField = _p(
        'skin:monthlystats|weekdays',
        "M,T,W,T,F,S,S"
    )
    weekdays: ComputedField = lambda skin: skin.weekdays_text.split(',')

    # Summary
    summary_pre_gap: NumberField = 50
    summary_mask: AssetField = 'monthly/summary_mask.png'

    study_this_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:study|summary:this_month',
        "THIS MONTH: {amount} HOURS"
    )
    voice_this_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:voice|summary:this_month',
        "THIS MONTH: {amount} HOURS"
    )
    text_this_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|summary:this_month',
        "THIS MONTH: {amount} MESSAGES"
    )
    anki_this_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|summary:this_month',
        "THIS MONTH: {amount} CARDS"
    )
    this_month_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_this_month_text,
        CardMode.VOICE: skin.voice_this_month_text,
        CardMode.TEXT: skin.text_this_month_text,
        CardMode.ANKI: skin.anki_this_month_text,
    }[skin.mode]

    this_month_image: BlobField = FieldDesc(
        BlobField,
        mask_field='summary_mask',
        colour_field='top_this_colour',
        colour_field_override='top_this_colour_override'
    )
    this_month_font: FontField = ('Light', 23)
    this_month_colour: ColourField = '#BABABA'

    summary_sep: NumberField = 300

    study_last_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:study|summary:last_month',
        "LAST MONTH: {amount} HOURS"
    )
    voice_last_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:voice|summary:last_month',
        "LAST MONTH: {amount} HOURS"
    )
    text_last_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|summary:last_month',
        "LAST MONTH: {amount} MESSAGES"
    )
    anki_last_month_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|summary:last_month',
        "LAST MONTH: {amount} CARDS"
    )
    last_month_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_last_month_text,
        CardMode.VOICE: skin.voice_last_month_text,
        CardMode.TEXT: skin.text_last_month_text,
        CardMode.ANKI: skin.anki_last_month_text,
    }[skin.mode]
    last_month_font: FontField = ('Light', 23)
    last_month_colour: ColourField = '#BABABA'
    last_month_image: BlobField = FieldDesc(
        BlobField,
        mask_field='summary_mask',
        colour_field='top_last_colour',
        colour_field_override='top_last_colour_override'
    )

    summary_gap: NumberField = 50

    # Bottom
    bottom_frame: AssetField = 'monthly/bottom_frame.png'
    bottom_margins: PointField = (100, 100)

    heatmap_mask: AssetField = 'monthly/heatmap_blob_mask.png'
    heatmap_empty_colour: ColourField = "#082534"
    heatmap_empty_colour_override: ColourField = None
    heatmap_empty: BlobField = FieldDesc(
        BlobField,
        mask_field='heatmap_mask',
        colour_field='heatmap_empty_colour',
        colour_field_override='heatmap_empty_colour_override'
    )
    heatmap_colours: RawField = [
        '#0E2A77',
        '#15357D',
        '#1D3F82',
        '#244A88',
        '#2C548E',
        '#335E93',
        '#3B6998',
        '#43729E',
        '#4B7CA3',
        '#5386A8',
        '#5B8FAD',
        '#6398B2',
        '#6BA1B7',
        '#73A9BC',
        '#7CB1C1',
        '#85B9C5',
    ]
    heatmap_colours.reverse()

    weekday_background_mask: AssetField = 'monthly/weekday_mask.png'
    weekday_background_colour: ColourField = '#60606038'
    weekday_background_colour_override: ColourField = None
    weekday_background: BlobField = FieldDesc(
        BlobField,
        mask_field='weekday_background_mask',
        colour_field='weekday_background_colour',
        colour_field_override='weekday_background_colour_override'
    )

    weekday_font: FontField = ('Black', 26.85)
    weekday_colour: ColourField = '#FFFFFF'
    weekday_sep: NumberField = 20

    month_background_mask: AssetField = 'monthly/month_mask.png'
    month_background_colour: ColourField = '#60606038'
    month_background_colour_override: ColourField = None
    month_background: BlobField = FieldDesc(
        BlobField,
        mask_field='month_background_mask',
        colour_field='month_background_colour',
        colour_field_override='month_background_colour_override'
    )
    month_font: FontField = ('Bold', 25.75)
    month_colour: ColourField = '#FFFFFF'
    month_sep: ComputedField = lambda skin: (
        skin.bottom_frame.width - 2 * skin.bottom_margins[0]
        - skin.weekday_background.width
        - skin.weekday_sep
        - 4 * skin.month_background.width
    ) // 3
    month_gap: NumberField = 25

    btm_grid_x: ComputedField = lambda skin: (skin.month_background.width - skin.heatmap_mask.width) // 5
    btm_grid_y: ComputedField = lambda skin: skin.btm_grid_x

    # Stats
    current_streak_key_text: LazyStringField = _p(
        'ui:monthlystats|stats:current_streak|key',
        "Current Streak:"
    )
    current_streak_value_text: LazyStringField = _p(
        'ui:monthlystats|stats:current_streak|value',
        "{count} days"
    )
    longest_streak_key_text: LazyStringField = _p(
        'ui:monthlystats|stats:longest_streak|key',
        "Longest Streak:"
    )
    longest_streak_value_text: LazyStringField = _p(
        'ui:monthlystats|stats:longest_streak|value',
        "{count} days"
    )
    daily_average_key_text: LazyStringField = _p(
        'ui:monthlystats|stats:daily_average|key',
        "Daily Average:"
    )
    study_daily_average_value_text: LazyStringField = _p(
        'skin:monthlystats|mode:study|stats:daily_average|value',
        "{count} hours"
    )
    voice_daily_average_value_text: LazyStringField = _p(
        'skin:monthlystats|mode:voice|stats:daily_average|value',
        "{count} hours"
    )
    text_daily_average_value_text: LazyStringField = _p(
        'skin:monthlystats|mode:text|stats:daily_average|value',
        "{count} msgs"
    )
    anki_daily_average_value_text: LazyStringField = _p(
        'skin:monthlystats|mode:anki|stats:daily_average|value',
        "{count} cards"
    )
    daily_average_value_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_daily_average_value_text,
        CardMode.VOICE: skin.voice_daily_average_value_text,
        CardMode.TEXT: skin.text_daily_average_value_text,
        CardMode.ANKI: skin.anki_daily_average_value_text,
    }[skin.mode]
    days_active_key_text: LazyStringField = _p(
        'ui:monthlystats|stats:days_active|key',
        "Days Active:"
    )
    days_active_value_text: LazyStringField = _p(
        'ui:monthlystats|stats:days_active|value',
        "{count} days"
    )
    stats_key_font: FontField = ('Medium', 23.65)
    stats_key_colour: ColourField = '#FFFFFF'
    stats_value_font: FontField = ('Light', 23.65)
    stats_value_colour: ColourField = '#808080'
    stats_sep: ComputedField = lambda skin: (
        skin.month_background.width + skin.month_sep + (skin.weekday_background.width + skin.weekday_sep) // 3
    )

    # Date text
    footer_text: LazyStringField = _p(
        'skin:monthlystats|footer',
        "Monthly Statistics • As of {day} {month} • {name} {discrim}"
    )
    footer_font: FontField = ('Bold', 28)
    footer_colour: ColourField = '#6f6e6f'
    footer_gap: NumberField = 50


class MonthlyStatsPage(Layout):
    def __init__(
        self,
        skin: MonthlyStatsSkin,
        user: tuple[str, str], timezone: str,
        now: int, month: int,
        monthly: list[list[float]],
        current_streak: int, longest_streak: int,
        **kwargs
    ):
        """
        Parameters
        ----------
        skin: MonthlyStatsSkin
        user: tuple[str, str]
            Name and discriminator of the user who owns this card.
        timezone: str
            A valid pytz timezone to localise the timestamps.
        now: int
            The UTC timestamp at which the data was calculated.
        month: int
            The UTC timestamp of the start of the (local) week.
        monthly: list[list[float]]
            A list of day activity totals for the last 4 months (inclusive of the current month).
        current_streak: int
            The user's current activity streak.
            (Provided as an argument in case the current streak is longer than the provided daily data.)
        longest_streak: int
            The user's all-time activity streak.
        """
        self.skin = skin

        # The provided raw data
        self.data_name, self.data_discrim = user
        self.data_timezone = timezone
        self.data_now = now
        self.data_month = month
        self.data_monthly = monthly
        self.data_current_streak = current_streak
        self.data_longest_streak = longest_streak

        # Computed data
        self.timezone = pytz.timezone(timezone)
        self.now = datetime.utcfromtimestamp(now).replace(tzinfo=pytz.utc).astimezone(self.timezone)
        self.month_start = datetime.utcfromtimestamp(month).replace(tzinfo=pytz.utc).astimezone(self.timezone)

        self.this_month = self.data_monthly[-1]
        self.last_month = self.data_monthly[-2]

        self.months = [self.month_start]
        for i in range(0, 3):
            self.months.append((self.months[-1] - timedelta(days=1)).replace(day=1))
        self.months.reverse()

        max_hours = max(*self.this_month, *self.last_month)
        self.max_hour_label = (4 * math.ceil(max_hours / 4)) or 4
        self.max_day_label = max(len(self.this_month), len(self.last_month))

        if self.now.year == self.month_start.year and self.now.month == self.month_start.month:
            avg_end = self.now.day
        else:
            avg_end = len(self.this_month)
        self.daily_average = sum(self.this_month) / avg_end

        nonzero = [day for month in self.data_monthly for day in month if day]

        self.days_active = len(nonzero)
        self.graph_average = (sum(nonzero) / len(nonzero)) if nonzero else 0

        # Drawing state
        self.image = None

    def draw(self) -> Image:
        image = self.image = self.skin.background
        draw = ImageDraw.Draw(image)

        xpos, ypos = 0, 0

        # Draw header text
        title_size = self.skin.title_size
        xpos = (image.width - title_size[0]) // 2
        ypos += self.skin.title_pre_gap
        draw.text(
            (xpos, ypos),
            self.skin.title_text,
            fill=self.skin.title_colour,
            font=self.skin.title_font
        )

        # Underline it
        ypos += title_size[1] + self.skin.title_underline_gap
        # draw.line(
        #     (xpos, ypos, xpos + title_size[0], ypos),
        #     fill=self.skin.title_colour,
        #     width=self.skin.title_underline_width
        # )
        ypos += self.skin.title_underline_width + self.skin.title_gap

        # Draw the top box
        top = self.draw_top()
        image.alpha_composite(
            top,
            ((image.width - top.width) // 2, ypos)
        )

        ypos += top.height + self.skin.top_gap

        # Draw the summaries
        summary_image = self.draw_summaries()
        image.alpha_composite(
            summary_image,
            ((image.width - summary_image.width) // 2, ypos)
        )
        ypos += summary_image.height + self.skin.summary_gap

        # Draw the bottom box
        bottom = self.draw_bottom()
        image.alpha_composite(
            bottom,
            ((image.width - bottom.width) // 2, ypos)
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
        size = self.skin.footer_font.getbbox(date_text)[2:]
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.skin.footer_font,
            fill=self.skin.footer_colour
        )
        return image

    def draw_summaries(self) -> Image:
        this_month_text = ' ' + self.skin.this_month_text.format(amount=int(sum(self.data_monthly[-1])))
        this_month_length = int(self.skin.this_month_font.getlength(this_month_text))
        last_month_text = ' ' + self.skin.last_month_text.format(amount=int(sum(self.data_monthly[-2])))
        last_month_length = int(self.skin.last_month_font.getlength(last_month_text))

        image = Image.new(
            'RGBA',
            (
                self.skin.this_month_image.width + this_month_length
                + self.skin.summary_sep
                + self.skin.last_month_image.width + last_month_length,
                self.skin.this_month_image.height
            )
        )
        draw = ImageDraw.Draw(image)

        xpos = 0
        ypos = image.height // 2
        image.alpha_composite(
            self.skin.this_month_image,
            (0, 0)
        )
        xpos += self.skin.this_month_image.width
        draw.text(
            (xpos, ypos),
            this_month_text,
            fill=self.skin.this_month_colour,
            font=self.skin.this_month_font,
            anchor='lm'
        )

        xpos += self.skin.summary_sep + this_month_length

        image.alpha_composite(
            self.skin.last_month_image,
            (xpos, 0)
        )
        xpos += self.skin.last_month_image.width
        draw.text(
            (xpos, ypos),
            last_month_text,
            fill=self.skin.last_month_colour,
            font=self.skin.last_month_font,
            anchor='lm'
        )
        return image

    def draw_top(self) -> Image:
        top_hours_bg = self.draw_hours_bg()
        size_x = (
            top_hours_bg.width // 2 + self.skin.top_hours_sep
            + (self.max_day_label - 1) * self.skin.top_grid_x + self.skin.top_bar_mask.width // 2
            + top_hours_bg.width // 2
        )
        size_y = (
            top_hours_bg.height // 2 + 4 * self.skin.top_grid_y + self.skin.top_date_pre_gap
            + self.skin.top_date_height
            + self.skin.top_time_bar_sep + int(self.skin.top_this_hours_font.getlength('240 H  240 H'))
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        x0 = top_hours_bg.width // 2 + self.skin.top_hours_sep
        y0 = top_hours_bg.height // 2 + 4 * self.skin.top_grid_y
        y0 += self.skin.top_time_bar_sep + int(self.skin.top_this_hours_font.getlength('24 H  24 H'))

        # Draw lines and numbers
        labels = list(int(i * self.max_hour_label // 4) for i in range(0, 5))

        xpos = x0 - self.skin.top_hours_sep
        ypos = y0
        for label in labels:
            draw.line(
                ((xpos, ypos), (image.width, ypos)),
                width=self.skin.top_line_width,
                fill=self.skin.top_line_colour
            )

            image.alpha_composite(
                top_hours_bg,
                (xpos - top_hours_bg.width // 2, ypos - top_hours_bg.height // 2)
            )
            text = str(label)
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
        ypos = y0 + self.skin.top_date_pre_gap
        for i in range(1, self.max_day_label + 1):
            draw.text(
                (xpos, ypos),
                str(i),
                fill=self.skin.top_date_colour,
                font=self.skin.top_date_font,
                anchor='mt'
            )
            xpos += self.skin.top_grid_x

        # Draw bars
        this_pad = (0 for _ in range(len(self.this_month), self.max_day_label))
        last_pad = (0 for _ in range(len(self.last_month), self.max_day_label))
        pairs = zip((*self.last_month, *last_pad), (*self.this_month, *this_pad))
        for i, (last_hours, this_hours) in enumerate(pairs):
            xpos = x0 + i * self.skin.top_grid_x

            if not (last_hours or this_hours):
                continue

            bar_height = 0
            for draw_last in (last_hours > this_hours, not last_hours > this_hours):
                hours = last_hours if draw_last else this_hours
                height = (4 * self.skin.top_grid_y) * (hours / self.max_hour_label)
                height = int(height)

                if height >= self.skin.top_bar_mask.width:
                    bar = self.draw_vertical_bar(
                        height,
                        self.skin.top_last_bar_full if draw_last else self.skin.top_this_bar_full,
                        self.skin.top_bar_mask
                    )
                    bar_height = max(height, bar_height)
                    image.alpha_composite(
                        bar,
                        (xpos - bar.width // 2, y0 - bar.height)
                    )

            # Draw text
            if bar_height:
                text = [
                    self.skin.top_hours_text.format(value=int(hours)) for hours in (last_hours, this_hours) if hours
                ]
                left, top, right, btm = self.skin.top_this_hours_font.getbbox('  '.join(text))
                text_size = (right, btm)
                text_image = Image.new(
                    'RGBA',
                    text_size
                )
                text_draw = ImageDraw.Draw(text_image)
                txpos = 0
                if last_hours:
                    last_text = self.skin.top_hours_text.format(value=int(last_hours)) + ' '
                    text_draw.text(
                        (txpos, 0), last_text,
                        fill=self.skin.top_last_hours_colour,
                        font=self.skin.top_last_hours_font
                    )
                    txpos += self.skin.top_last_hours_font.getlength(last_text)
                if this_hours:
                    this_text = self.skin.top_hours_text.format(value=int(this_hours))
                    text_draw.text(
                        (txpos, 0), this_text,
                        fill=self.skin.top_this_hours_colour,
                        font=self.skin.top_this_hours_font
                    )

                text_image = text_image.rotate(90, expand=True)
                text_image = text_image.crop(text_image.getbbox())

                image.alpha_composite(
                    text_image,
                    (xpos - text_image.width // 2,
                     y0 - bar_height - self.skin.top_time_bar_sep - text_image.height)
                )

        return image

    def draw_hours_bg(self) -> Image:
        """
        Draw a dynamically sized blob for the background of the hours axis in the top graph.
        """
        blob = self.skin.top_hours_bg
        font = self.skin.top_hours_font

        labels = list(int(i * self.max_hour_label // 4) for i in range(0, 5))
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

    def draw_bottom(self) -> Image:
        image = self.skin.bottom_frame
        draw = ImageDraw.Draw(image)

        xpos, ypos = self.skin.bottom_margins

        # Draw the weekdays
        y0 = self.skin.month_background.height + self.skin.month_gap
        for i, weekday in enumerate(self.skin.weekdays):
            y = y0 + i * self.skin.btm_grid_y
            image.alpha_composite(
                self.skin.weekday_background,
                (xpos, ypos + y)
            )
            draw.text(
                (xpos + self.skin.weekday_background.width // 2, ypos + y + self.skin.weekday_background.height // 2),
                weekday,
                fill=self.skin.weekday_colour,
                font=self.skin.weekday_font,
                anchor='mm'
            )

        # Draw the months
        x0 = self.skin.weekday_background.width + self.skin.weekday_sep
        for i, date in enumerate(self.months):
            name = local_month(date.month, short=False).upper()

            x = x0 + i * (self.skin.month_background.width + self.skin.month_sep)
            image.alpha_composite(
                self.skin.month_background,
                (xpos + x, ypos)
            )
            draw.text(
                (xpos + x + self.skin.month_background.width // 2,
                 ypos + self.skin.month_background.height // 2),
                name,
                fill=self.skin.month_colour,
                font=self.skin.month_font,
                anchor='mm'
            )

            heatmap = self.draw_month_heatmap(i)
            image.alpha_composite(
                heatmap,
                (xpos + x + self.skin.month_background.width // 2 - heatmap.width // 2, ypos + y0)
            )

        # Draw the streak and stats information
        x = xpos + self.skin.weekday_background.width // 2
        y = image.height - self.skin.bottom_margins[1]

        key_text = self.skin.current_streak_key_text
        key_len = self.skin.stats_key_font.getlength(key_text + ' ')
        value_text = self.skin.current_streak_value_text.format(count=self.data_current_streak)
        draw.text(
            (x, y),
            key_text,
            font=self.skin.stats_key_font,
            fill=self.skin.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.skin.stats_value_font,
            fill=self.skin.stats_value_colour
        )
        x += self.skin.stats_sep

        key_text = self.skin.longest_streak_key_text
        key_len = self.skin.stats_key_font.getlength(key_text + ' ')
        value_text = self.skin.longest_streak_value_text.format(count=self.data_longest_streak)
        draw.text(
            (x, y),
            key_text,
            font=self.skin.stats_key_font,
            fill=self.skin.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.skin.stats_value_font,
            fill=self.skin.stats_value_colour
        )
        x += self.skin.stats_sep

        key_text = self.skin.daily_average_key_text
        key_len = self.skin.stats_key_font.getlength(key_text + ' ')
        value_text = self.skin.daily_average_value_text.format(count=int(self.daily_average))
        draw.text(
            (x, y),
            key_text,
            font=self.skin.stats_key_font,
            fill=self.skin.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.skin.stats_value_font,
            fill=self.skin.stats_value_colour
        )
        x += self.skin.stats_sep

        key_text = self.skin.days_active_key_text
        key_len = self.skin.stats_key_font.getlength(key_text + ' ')
        value_text = self.skin.days_active_value_text.format(count=self.days_active)
        draw.text(
            (x, y),
            key_text,
            font=self.skin.stats_key_font,
            fill=self.skin.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.skin.stats_value_font,
            fill=self.skin.stats_value_colour
        )
        x += self.skin.stats_sep

        return image

    def draw_month_heatmap(self, index) -> Image:
        month_start = self.months[index]
        month_data = self.data_monthly[index]
        cal = calendar.monthcalendar(month_start.year, month_start.month)
        print(self.month_start)
        print(cal)
        columns = len(cal)

        size_x = (
            (columns - 1) * self.skin.btm_grid_x
            + self.skin.heatmap_mask.width
        )
        size_y = (
            6 * self.skin.btm_grid_y + self.skin.heatmap_mask.height
        )

        image = Image.new('RGBA', (size_x, size_y))

        x0 = self.skin.heatmap_mask.width // 2
        y0 = self.skin.heatmap_mask.height // 2

        for (i, week) in enumerate(cal):
            xpos = x0 + i * self.skin.btm_grid_x
            print(week)
            for (j, day) in enumerate(week):
                if day:
                    ypos = y0 + j * self.skin.btm_grid_y
                    time = month_data[day-1]
                    bubble = self.draw_bubble(time)
                    image.alpha_composite(
                        bubble,
                        (xpos - bubble.width // 2, ypos - bubble.width // 2)
                    )

        return image

    def draw_bubble(self, time):
        # Calculate colour level
        if time == 0:
            image = self.skin.heatmap_empty
            colour = self.skin.heatmap_empty_colour
        else:
            amount = min((time / self.graph_average) if self.graph_average else 0, 2) / 2
            index = math.ceil(amount * len(self.skin.heatmap_colours)) - 1
            colour = self.skin.heatmap_colours[index]

            image = Image.new('RGBA', self.skin.heatmap_mask.size)
            image.paste(colour, mask=self.skin.heatmap_mask)
        return image


class MonthlyStatsCard(Card):
    route = "monthly_stats_card"
    card_id = "monthly_stats"

    layout = MonthlyStatsPage
    skin = MonthlyStatsSkin

    display_name = _p(
        'card:monthly_stats|display_name',
        "Monthly Stats"
    )

    @classmethod
    async def sample_args(cls, ctx, **kwargs):
        import random
        from datetime import timezone, datetime, timedelta

        current = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        month = current.replace(day=1)

        months = [month]
        for i in range(3):
            months.append((months[-1] - timedelta(days=1)).replace(day=1))
        months.reverse()

        streak = 0
        longest_streak = 0
        monthly = [[], [], [], []]
        for i, month in enumerate(months):
            day_count = ((month + timedelta(days=32)).replace(day=1) - timedelta(days=1)).day
            for j in range(day_count):
                if (i == 3 and j >= current.day) or random.randint(0, 30) == 0:
                    longest_streak = max(streak, longest_streak)
                    streak = 0
                    value = 0
                else:
                    streak += 1
                    value = abs(random.normalvariate(800, 200))
                monthly[i].append(value)
        longest_streak = max(streak, longest_streak)

        return {
            'user': (
                ctx.author.name if ctx else "John Doe",
                ('#' + ctx.author.discriminator) if ctx else "#0000"
            ),
            'timezone': 'utc',
            'now': int(datetime.now(tz=timezone.utc).timestamp()),
            'month': int(month.timestamp()),
            'monthly': monthly,
            'current_streak': streak,
            'longest_streak': longest_streak
        }
