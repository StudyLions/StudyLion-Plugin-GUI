import math
from PIL import Image, ImageDraw
from datetime import timedelta

from .Card import Card
from .Skin import fielded, Skin
from .Skin import AssetField, RGBAAssetField, NumberField, FontField, ColourField, ComputedField, RawField, StringField

from ..utils import asset_path


@fielded
class WeeklyStatsSkin(Skin):
    _card_id = "weekly_stats"

    _env = {
        'scale': 1  # General size scale to match background resolution
    }

    background: AssetField = 'weekly/background.png'

    # Header
    title_pre_gap: NumberField = 40
    title_text: StringField = "STUDY HOURS"
    title_font: FontField = ('ExtraBold', 76)
    title_size: ComputedField = lambda skin: skin.title_font.getsize(skin.title_text)
    title_colour: ColourField = '#DDB21D'
    title_underline_gap: NumberField = 10
    title_underline_width: NumberField = 5
    title_gap: NumberField = 50

    # Top
    top_grid_x: NumberField = 150
    top_grid_y: NumberField = 100

    top_hours_font: FontField = ('Bold', 36.35)
    top_hours_colour: ColourField = '#FFFFFF'
    top_hours_bg: AssetField = 'weekly/top/hours_bg.png'
    top_hours_sep: NumberField = 100

    top_line_width: NumberField = 10
    top_line_colour: ColourField = '#042231'

    top_weekday_pre_gap: NumberField = 20
    top_weekday_font: FontField = ('Bold', 36.35)
    top_weekday_colour: ColourField = '#FFFFFF'
    top_weekday_height: ComputedField = lambda skin: skin.top_weekday_font.getsize('MTWTFSS')[1]
    top_weekday_gap: NumberField = 5
    top_date_font: FontField = ('SemiBold', 30)
    top_date_colour: ColourField = '#808080'
    top_date_height: ComputedField = lambda skin: skin.top_date_font.getsize('8/8')[1]

    top_this_top: RGBAAssetField = 'weekly/top/this_top.png'
    top_this_colour: ColourField = '#DDB21D'
    top_this_btm: RGBAAssetField = 'weekly/top/this_bottom.png'

    top_last_top: RGBAAssetField = 'weekly/top/last_top.png'
    top_last_colour: ColourField = '#377689CC'
    top_last_btm: RGBAAssetField = 'weekly/top/last_bottom.png'

    top_gap: NumberField = 80

    weekdays: RawField = ('M', 'T', 'W', 'T', 'F', 'S', 'S')

    # Bottom
    btm_weekly_background: AssetField = 'weekly/bottom/weekday_bg.png'

    btm_this_end: AssetField = 'weekly/bottom/this_end.png'
    btm_this_colour: ColourField = '#DDB21D'

    btm_last_end: AssetField = 'weekly/bottom/last_end.png'
    btm_last_colour: ColourField = '#5E6C747F'

    btm_horiz_width: ComputedField = lambda skin: skin.btm_this_end.height
    btm_sep: ComputedField = lambda skin: (skin.btm_weekly_background.height - 7 * skin.btm_horiz_width) // 6

    btm_vert_width: NumberField = 10

    btm_grid_x: NumberField = 48
    btm_grid_y: ComputedField = lambda skin: skin.btm_horiz_width + skin.btm_sep

    btm_weekday_font: FontField = ('Bold', 36.35)
    btm_weekday_colour: ColourField = '#FFFFFF'

    btm_day_font: FontField = ('SemiBold', 31)
    btm_day_colour: ColourField = '#FFFFFF'
    btm_day_height: ComputedField = lambda skin: skin.btm_day_font.getsize('88')[1]
    btm_day_gap: NumberField = 15

    btm_bar_horiz_colour: ColourField = "#052B3B93"
    btm_bar_vert_colour: ColourField = "#042231B2"
    btm_bar_weekday_colour: ColourField = "#F9CDB77F"

    # TODO: These should be better exposed to the skin
    btm_emojis: ComputedField = lambda skin: {
        state: Image.open(asset_path(f'weekly/bottom/emojis/{state}.png')).convert('RGBA')
        for state in ('very_happy', 'happy', 'neutral', 'sad', 'shocked')
    }

    # Summary
    summary_pre_gap: NumberField = 50

    this_week_image: AssetField = 'weekly/summary_this.png'
    this_week_font: FontField = ('Light', 23)
    this_week_colour: ColourField = '#BABABA'

    summary_sep: NumberField = 300

    last_week_image: AssetField = 'weekly/summary_last.png'
    last_week_font: FontField = ('Light', 23)
    last_week_colour: ColourField = '#BABABA'

    # Date text
    date_font: FontField = ('Bold', 28)
    date_colour: ColourField = '#6f6e6f'
    date_gap: NumberField = 50


class WeeklyStatsPage(Card):
    server_route = 'weekly_card'

    def __init__(self, name, discrim, sessions, date):
        """
        `sessions` is a list of study sessions from the last two weeks.
        """
        self.skin = WeeklyStatsSkin().load()

        self.data_sessions = sessions
        self.data_date = date

        self.data_name = name
        self.data_discrim = discrim

        self.week_start = date - timedelta(days=date.weekday())
        self.last_week_start = self.week_start - timedelta(days=7)

        periods = []
        times = []

        day_start = self.last_week_start
        day_time = 0
        day_periods = []
        current_period = []
        i = 0
        while i < len(sessions):
            start, end = sessions[i]
            i += 1

            day_end = day_start + timedelta(hours=24)

            if end < day_start:
                continue

            if start < day_start:
                start = day_start
            elif start >= day_end:
                if current_period:
                    day_periods.append(current_period)
                periods.append(day_periods)
                times.append(day_time)
                current_period = []
                day_periods = []
                day_time = 0
                day_start = day_end
                i -= 1
                continue

            if (ended_after := (end - day_end).total_seconds()) > 0:
                if ended_after > 60 * 20:
                    end = day_end
                else:
                    end = day_end - timedelta(minutes=1)

            day_time += (end - start).total_seconds()
            if not current_period:
                current_period = [start, end]
            elif (start - current_period[1]).total_seconds() < 60 * 60:
                current_period[1] = end
            else:
                day_periods.append(current_period)
                current_period = [start, end]

            if ended_after > 0:
                if current_period:
                    day_periods.append(current_period)
                periods.append(day_periods)
                times.append(day_time)
                current_period = []
                day_periods = []
                day_time = 0
                day_start = day_end

                if ended_after > 60 * 20:
                    i -= 1

        if current_period:
            day_periods.append(current_period)
        periods.append(day_periods)
        times.append(day_time)

        self.data_periods = periods
        for i in range(len(periods), 14):
            periods.append([])
        self.data_hours = [time / 3600 for time in times]
        for i in range(len(self.data_hours), 14):
            self.data_hours.append(0)

        self.date_labels = [
            (self.week_start + timedelta(days=i)).strftime('%d/%m')
            for i in range(0, 7)
        ]

        self.max_hour_label = (4 * math.ceil(max(self.data_hours) / 4)) or 4

        self.image = None

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
        ypos -= self.skin.date_gap
        date_text = self.data_date.strftime(
            "Weekly Statistics • As of %d %b • {} {}".format(self.data_name, self.data_discrim)
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
        this_week_text = " THIS WEEK: {} Hours".format(int(sum(self.data_hours[7:])))
        this_week_length = int(self.skin.this_week_font.getlength(this_week_text))
        last_week_text = " LAST WEEK: {} Hours".format(int(sum(self.data_hours[:7])))
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

    def draw_top(self) -> Image:
        size_x = (
            self.skin.top_hours_bg.width // 2 + self.skin.top_hours_sep
            + 6 * self.skin.top_grid_x + self.skin.top_this_top.width // 2
            + self.skin.top_hours_bg.width // 2
        )
        size_y = (
            self.skin.top_hours_bg.height // 2 + 4 * self.skin.top_grid_y + self.skin.top_weekday_pre_gap
            + self.skin.top_weekday_height + self.skin.top_weekday_gap + self.skin.top_date_height
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        x0 = self.skin.top_hours_bg.width // 2 + self.skin.top_hours_sep
        y0 = self.skin.top_hours_bg.height // 2 + 4 * self.skin.top_grid_y

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
        for i, (last_hours, this_hours) in enumerate(zip(self.data_hours[:7], self.data_hours[7:])):
            day = i % 7
            xpos = x0 + day * self.skin.top_grid_x

            for draw_last in (last_hours > this_hours, not last_hours > this_hours):
                hours = last_hours if draw_last else this_hours
                height = (4 * self.skin.top_grid_y) * (hours / self.max_hour_label)
                height = int(height)

                if height >= 2 * self.skin.top_this_top.height:
                    bar = self.draw_vert_bar(height, last=draw_last)
                    image.alpha_composite(
                        bar,
                        (xpos - bar.width // 2, y0 - bar.height)
                    )

        return image

    def draw_vert_bar(self, height, last=False) -> Image:
        image = Image.new('RGBA', (self.skin.top_this_top.width - 2, height))

        if last:
            top = self.skin.top_last_top
            bottom = self.skin.top_last_btm
            colour = self.skin.top_last_colour
        else:
            top = self.skin.top_this_top
            bottom = self.skin.top_this_btm
            colour = self.skin.top_this_colour

        image.alpha_composite(
            top,
            ((image.width - top.width) // 2, 0)
        )
        image.alpha_composite(
            bottom,
            ((image.width - bottom.width) // 2, height - bottom.height)
        )
        ImageDraw.Draw(image).rectangle(
            (
                ((image.width - top.width) // 2, top.height - 1),
                (top.width, height - bottom.height),
            ),
            fill=colour,
            width=0
        )
        return image

    def draw_bottom(self) -> Image:
        size_x = int(
            self.skin.btm_weekly_background.width
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
        x0 = self.skin.btm_weekly_background.width + self.skin.btm_vert_width // 2 + self.skin.btm_grid_x
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
        xpos = self.skin.btm_weekly_background.width // 2
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
        seconds_in_day = 60 * 60 * 24
        day_width = 24 * self.skin.btm_grid_x
        for i, day in enumerate(reversed(self.data_periods)):
            last = (i // 7)
            ypos = y0 + (6 - i % 7) * self.skin.btm_grid_y

            for start, end in day:
                day_start = start.replace(hour=0, minute=0, second=0, microsecond=0)

                flat_start = (start == day_start)
                duration = (end - start).total_seconds()
                xpos = x0 + int((start - day_start).total_seconds() / seconds_in_day * day_width)

                flat_end = (end == day_start + timedelta(days=1))

                if flat_end:
                    width = image.width - xpos
                else:
                    width = int(duration / seconds_in_day * day_width)

                bar = self.draw_horizontal_bar(
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
        average_study = sum(self.data_hours[7:]) / 7
        for i, hours in enumerate(self.data_hours[7:]):
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

    def draw_horizontal_bar(self, width, last=False, flat_start=False, flat_end=False) -> Image:
        if last:
            end = self.skin.btm_last_end
            colour = self.skin.btm_last_colour
        else:
            end = self.skin.btm_this_end
            colour = self.skin.btm_this_colour

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
        draw.rectangle(
            ((rstart, 0), (rend, image.height)),
            fill=colour,
            width=0
        )

        return image
