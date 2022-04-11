import math
import calendar
from collections import defaultdict
from PIL import Image, ImageDraw
from datetime import timedelta
import datetime

from .Card import Card
from .Skin import fielded, Skin, FieldDesc
from .Skin import AssetField, NumberField, FontField, ColourField, PointField, ComputedField, RawField, StringField
from .Skin import AssetPathField


@fielded
class MonthlyStatsSkin(Skin):
    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    background: AssetField = 'monthly/background.png'

    # Header
    title_pre_gap: NumberField = 40
    title_text: StringField = "STUDY HOURS"
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: skin.title_font.getsize(skin.title_text)
    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 5
    title_gap: NumberField = 10

    # Top
    top_grid_x: NumberField = 37
    top_grid_y: NumberField = 100

    top_hours_font: FontField = ('Black', 36)
    top_hours_colour: ColourField = '#FFFFFF'
    top_hours_bg: AssetField = 'monthly/top/hours_bg.png'
    top_hours_sep: NumberField = 100

    top_line_width: NumberField = 10
    top_line_colour: ColourField = '#042231'

    top_date_pre_gap: NumberField = 20
    top_date_font: FontField = ('Light', 25)
    top_date_colour: ColourField = '#FFFFFF'
    top_date_height: ComputedField = lambda skin: skin.top_date_font.getsize('31')[1]

    top_this_end: AssetField = 'monthly/top/this_end.png'
    top_this_colour: ColourField = '#DDB21D'

    top_last_end: AssetField = 'monthly/top/last_end.png'
    top_last_colour: ColourField = '#377689'

    top_this_hours_font: FontField = ('Light', 20)
    top_this_hours_colour: ColourField = '#DDB21D'

    top_time_bar_sep: NumberField = 7
    top_time_sep: NumberField = 5

    top_last_hours_font: FontField = ('Light', 20)
    top_last_hours_colour: ColourField = '#5F91A1'

    top_gap: NumberField = 40

    weekdays: RawField = ('M', 'T', 'W', 'T', 'F', 'S', 'S')

    # Summary
    summary_pre_gap: NumberField = 50

    this_month_image: AssetField = 'monthly/summary_this.png'
    this_month_font: FontField = ('Light', 23)
    this_month_colour: ColourField = '#BABABA'

    summary_sep: NumberField = 300

    last_month_image: AssetField = 'monthly/summary_last.png'
    last_month_font: FontField = ('Light', 23)
    last_month_colour: ColourField = '#BABABA'

    summary_gap: NumberField = 50

    # Bottom
    bottom_frame: AssetField = 'monthly/bottom/frame.png'
    bottom_margins: PointField = (100, 100)

    heatmap_mask: AssetField = 'monthly/bottom/blob.png'
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

    weekday_background: AssetField = 'monthly/bottom/weekday.png'
    weekday_font: FontField = ('Black', 26.85)
    weekday_colour: ColourField = '#FFFFFF'
    weekday_sep: NumberField = 20

    month_background: AssetField = 'monthly/bottom/month_bg.png'
    month_font: FontField = ('Bold', 25.75)
    month_colour: ColourField = '#FFFFFF'
    month_sep: ComputedField = lambda skin: (
        skin.bottom_frame.width - 2 * skin.bottom_margins[0]
        - skin.weekday_background.width
        - skin.weekday_sep
        - 4 * skin.month_background.width
    ) // 3
    month_gap: NumberField = 25

    btm_frame: AssetField = 'monthly/bottom/frame.png'
    btm_grid_x: ComputedField = lambda skin: (skin.month_background.width - skin.heatmap_mask.width) // 5
    btm_grid_y: ComputedField = lambda skin: skin.btm_grid_x

    # Stats
    stats_key_font: FontField = ('Medium', 23.65)
    stats_key_colour: ColourField = '#FFFFFF'
    stats_value_font: FontField = ('Light', 23.65)
    stats_value_colour: ColourField = '#808080'
    stats_sep: ComputedField = lambda skin: (
        skin.month_background.width + skin.month_sep + (skin.weekday_background.width + skin.weekday_sep) // 3
    )

    # Date text
    date_font: FontField = ('Bold', 28)
    date_colour: ColourField = '#6f6e6f'
    date_gap: NumberField = 50


class MonthlyStatsPage(Card):
    server_route = 'monthly_card'

    def __init__(self, name, discrim, sessions, date, current_streak, longest_streak, first_session_start):
        """
        `sessions` is a list of study sessions from the last two weeks.
        """
        self.skin = MonthlyStatsSkin().load()

        self.data_sessions = sessions
        self.data_date = date

        self.data_name = name
        self.data_discrim = discrim

        self.current_streak = current_streak
        self.longest_streak = longest_streak

        self.month_start = date.replace(day=1)

        self.data_time = defaultdict(int)

        for start, end in sessions:
            day_start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(hours=24)

            if end > day_end:
                self.data_time[day_start.date()] += (day_end - start).total_seconds()
                self.data_time[day_end.date()] += (end - day_end).total_seconds()
            else:
                self.data_time[day_start.date()] += (end - start).total_seconds()

        self.this_month_days = calendar.monthrange(self.month_start.year, self.month_start.month)[1]
        self.hours_this_month = [
            self.data_time[self.month_start + timedelta(days=i)] / 3600
            for i in range(0, self.this_month_days)
        ]

        self.months = [self.month_start]
        for i in range(0, 3):
            self.months.append((self.months[-1] - timedelta(days=1)).replace(day=1))

        self.months.reverse()

        last_month_start = self.months[-2]
        last_month_days = calendar.monthrange(last_month_start.year, last_month_start.month)[1]
        self.hours_last_month = [
            self.data_time[last_month_start + timedelta(days=i)] / 3600
            for i in range(0, last_month_days)
        ][:self.this_month_days]  # Truncate to this month length

        max_hours = max(*self.hours_this_month, *self.hours_last_month)

        self.max_hour_label = (4 * math.ceil(max_hours / 4)) or 4

        self.days_learned = sum(val != 0 for val in self.data_time.values())
        self.total_days = sum(
            calendar.monthrange(month.year, month.month)[1]
            for month in self.months
        )
        self.days_since_start = min(
            (date - first_session_start.date()).days,
            (date - self.months[0]).days
        ) + 1
        self.average_time = sum(self.data_time.values()) / self.days_learned

        self.image = None

    def draw(self) -> Image:
        image = self.image = self.skin.background
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
        title_size = self.skin.title_font.getsize(self.skin.title_text)
        ypos += title_size[1] + self.skin.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
            fill=self.skin.title_colour,
            width=self.skin.title_underline_width
        )
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
        ypos -= self.skin.date_gap
        date_text = self.data_date.strftime(
            "Monthly Statistics • As of %d %b • {} {}".format(self.data_name, self.data_discrim)
        )
        size = self.skin.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.skin.date_font,
            fill=self.skin.date_colour
        )
        return image

    def draw_summaries(self) -> Image:
        this_month_text = " THIS MONTH: {} Hours".format(int(sum(self.hours_this_month)))
        this_month_length = int(self.skin.this_month_font.getlength(this_month_text))
        last_month_text = " LAST MONTH: {} Hours".format(int(sum(self.hours_last_month)))
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
        size_x = (
            self.skin.top_hours_bg.width // 2 + self.skin.top_hours_sep
            + (self.this_month_days - 1) * self.skin.top_grid_x + self.skin.top_this_end.width // 2
            + self.skin.top_hours_bg.width // 2
        )
        size_y = (
            self.skin.top_hours_bg.height // 2 + 4 * self.skin.top_grid_y + self.skin.top_date_pre_gap
            + self.skin.top_date_height
            + self.skin.top_time_bar_sep + int(self.skin.top_this_hours_font.getlength('24 H  24 H'))
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        x0 = self.skin.top_hours_bg.width // 2 + self.skin.top_hours_sep
        y0 = self.skin.top_hours_bg.height // 2 + 4 * self.skin.top_grid_y
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
                self.skin.top_hours_bg,
                (xpos - self.skin.top_hours_bg.width // 2, ypos - self.skin.top_hours_bg.height // 2)
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
        for i in range(1, self.this_month_days + 1):
            draw.text(
                (xpos, ypos),
                str(i),
                fill=self.skin.top_date_colour,
                font=self.skin.top_date_font,
                anchor='mt'
            )
            xpos += self.skin.top_grid_x

        # Draw bars
        for i, (last_hours, this_hours) in enumerate(zip(self.hours_last_month, self.hours_this_month)):
            xpos = x0 + i * self.skin.top_grid_x

            if not (last_hours or this_hours):
                continue

            bar_height = 0
            for draw_last in (last_hours > this_hours, not last_hours > this_hours):
                hours = last_hours if draw_last else this_hours
                height = (4 * self.skin.top_grid_y) * (hours / self.max_hour_label)
                height = int(height)

                if height >= self.skin.top_this_end.height:
                    bar = self.draw_vert_bar(height, last=draw_last)
                    bar_height = max(bar.height, bar_height)
                    image.alpha_composite(
                        bar,
                        (xpos - bar.width // 2, y0 - bar.height)
                    )

            # Draw text
            if bar_height:
                text = ['{} H'.format(hours) for hours in (last_hours, this_hours) if hours]
                text_size = self.skin.top_this_hours_font.getsize('  '.join(text))
                text_image = Image.new(
                    'RGBA',
                    text_size
                )
                text_draw = ImageDraw.Draw(text_image)
                txpos = 0
                if last_hours:
                    last_text = "{} H  ".format(int(last_hours))
                    text_draw.text(
                        (txpos, 0), last_text,
                        fill=self.skin.top_last_hours_colour,
                        font=self.skin.top_last_hours_font
                    )
                    txpos += self.skin.top_last_hours_font.getlength('  '.join(text))
                if this_hours:
                    this_text = "{} H  ".format(int(this_hours))
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

    def draw_vert_bar(self, height, last=False) -> Image:
        image = Image.new('RGBA', (self.skin.top_this_end.width - 1, height))

        if last:
            end = self.skin.top_last_end
            colour = self.skin.top_last_colour
        else:
            end = self.skin.top_this_end
            colour = self.skin.top_this_colour

        image.paste(
            end,
            ((image.width - end.width) // 2, 0)
        )
        image.paste(
            end,
            ((image.width - end.width) // 2, height - end.height)
        )
        ImageDraw.Draw(image).rectangle(
            (
                ((image.width - end.width) // 2, end.height // 2),
                (end.width, height - end.height // 2),
            ),
            fill=colour,
            width=0
        )
        return image

    def draw_bottom(self) -> Image:
        image = self.skin.btm_frame
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
            name = date.strftime('%B').upper()

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

            heatmap = self.draw_month_heatmap(date)
            image.alpha_composite(
                heatmap,
                (xpos + x + self.skin.month_background.width // 2 - heatmap.width // 2, ypos + y0)
            )

        # Draw the streak and stats information
        x = xpos + self.skin.weekday_background.width // 2
        y = image.height - self.skin.bottom_margins[1]

        key_text = "Current streak: "
        key_len = self.skin.stats_key_font.getlength(key_text)
        value_text = "{} day{}".format(
            self.current_streak,
            's' if self.current_streak != 1 else ''
        )
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

        key_text = "Daily average: "
        key_len = self.skin.stats_key_font.getlength(key_text)
        value_text = "{} hour{}".format(
            (hours := int(self.average_time // 3600)),
            's' if hours != 1 else ''
        )
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

        key_text = "Longest streak: "
        key_len = self.skin.stats_key_font.getlength(key_text)
        value_text = "{} day{}".format(
            self.longest_streak,
            's' if self.current_streak != 1 else ''
        )
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

        key_text = "Days learned: "
        key_len = self.skin.stats_key_font.getlength(key_text)
        value_text = "{}%".format(
            int((100 * self.days_learned) // self.days_since_start)
        )
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

    def draw_month_heatmap(self, month_start) -> Image:
        cal = calendar.monthcalendar(month_start.year, month_start.month)
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
            for (j, day) in enumerate(week):
                if day:
                    ypos = y0 + j * self.skin.btm_grid_y
                    date = datetime.date(month_start.year, month_start.month, day)
                    time = self.data_time[date]
                    bubble = self.draw_bubble(time)
                    image.alpha_composite(
                        bubble,
                        (xpos - bubble.width // 2, ypos - bubble.width // 2)
                    )

        return image

    def draw_bubble(self, time):
        # Calculate colour level
        if time == 0:
            return self.skin.heatmap_mask
        else:
            amount = min(time / self.average_time, 2) / 2
            index = math.ceil(amount * len(self.skin.heatmap_colours)) - 1
            colour = self.skin.heatmap_colours[index]

            image = Image.new('RGBA', self.skin.heatmap_mask.size)
            image.paste(colour, mask=self.skin.heatmap_mask)
            return image
