import math
import calendar
from collections import defaultdict
from PIL import Image, ImageDraw
from datetime import timedelta
import datetime


from ..utils import asset_path, inter_font


class MonthlyStatsPage:
    scale = 2

    background = Image.open(asset_path('monthly/background.png')).convert('RGBA')

    # Header
    title_pre_gap = int(scale * 40)
    title_text = "STUDY HOURS"
    title_font = inter_font('ExtraBold', size=int(scale * 76))
    title_size = title_font.getsize(title_text)
    title_colour = '#DDB21D'
    title_underline_gap = int(scale * 10)
    title_underline_width = int(scale * 5)
    title_gap = int(scale * 10)

    # Top
    top_grid_x = int(scale*37)
    top_grid_y = int(scale*100)

    top_hours_font = inter_font('Black', size=int(scale*36))
    top_hours_colour = '#FFFFFF'
    top_hours_bg = Image.open(asset_path('monthly/top/hours_bg.png')).convert('RGBA')
    top_hours_sep = int(scale * 100)

    top_line_width = 20
    top_line_colour = '#042231'

    top_date_pre_gap = int(scale * 20)
    top_date_font = inter_font('Light', size=int(scale*25))
    top_date_colour = '#FFFFFF'
    top_date_height = top_date_font.getsize('31')[1]

    top_this_end = Image.open(asset_path('monthly/top/this_end.png')).convert('RGBA')
    top_this_colour = '#DDB21D'

    top_last_end = Image.open(asset_path('monthly/top/last_end.png')).convert('RGBA')
    top_last_colour = '#377689'

    top_this_hours_font = inter_font('Light', size=int(scale * 20))
    top_this_hours_colour = '#DDB21D'

    top_time_bar_sep = int(scale * 7)
    top_time_sep = int(scale * 5)

    top_last_hours_font = inter_font('Light', size=int(scale * 20))
    top_last_hours_colour = '#5F91A1'

    top_gap = int(scale * 40)

    weekdays = ('M', 'T', 'W', 'T', 'F', 'S', 'S')

    # Summary
    summary_pre_gap = int(scale * 50)

    this_month_image = Image.open(asset_path('monthly/summary_this.png'))
    this_month_font = inter_font('Light', size=int(scale*23))
    this_month_colour = '#BABABA'

    summary_sep = int(scale * 300)

    last_month_image = Image.open(asset_path('monthly/summary_last.png'))
    last_month_font = inter_font('Light', size=int(scale*23))
    last_month_colour = '#BABABA'

    summary_gap = int(scale * 50)

    # Bottom
    bottom_frame = Image.open(asset_path('monthly/bottom/frame.png'))
    bottom_margins = (100, 100)

    heatmap_mask = Image.open(asset_path('monthly/bottom/blob.png')).convert('RGBA')
    heatmap_colours = [
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

    weekday_background = Image.open(asset_path('monthly/bottom/weekday.png'))
    weekday_font = inter_font('Black', size=int(scale*26.85))
    weekday_colour = '#FFFFFF'
    weekday_sep = int(scale * 20)

    month_background = Image.open(asset_path('monthly/bottom/month_bg.png'))
    month_font = inter_font('Bold', size=int(scale*25.75))
    month_colour = '#FFFFFF'
    month_sep = (
        bottom_frame.width - 2 * bottom_margins[0]
        - weekday_background.width
        - weekday_sep
        - 4 * month_background.width
    ) // 3
    month_gap = int(scale * 25)

    btm_frame = Image.open(asset_path('monthly/bottom/frame.png')).convert('RGBA')
    btm_grid_x = (month_background.width - heatmap_mask.width) // 5
    btm_grid_y = btm_grid_x

    # Stats
    stats_key_font = inter_font('Medium', size=int(scale*23.65))
    stats_key_colour = '#FFFFFF'
    stats_value_font = inter_font('Light', size=int(scale*23.65))
    stats_value_colour = '#808080'
    stats_sep = month_background.width + month_sep + (weekday_background.width + weekday_sep) // 3

    # Date text
    date_font = inter_font('Bold', size=int(scale * 28))
    date_colour = '#6f6e6f'
    date_gap = int(scale * 50)

    def __init__(self, name, discrim, sessions, date, current_streak, longest_streak, first_session_start):
        """
        `sessions` is a list of study sessions from the last two weeks.
        """
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
        image = self.image = self.background.copy()
        draw = ImageDraw.Draw(image)

        xpos, ypos = 0, 0

        # Draw header text
        xpos = (image.width - self.title_size[0]) // 2
        ypos += self.title_pre_gap
        draw.text(
            (xpos, ypos),
            self.title_text,
            fill=self.title_colour,
            font=self.title_font
        )

        # Underline it
        title_size = self.title_font.getsize(self.title_text)
        ypos += title_size[1] + self.title_underline_gap
        draw.line(
            (xpos, ypos, xpos + title_size[0], ypos),
            fill=self.title_colour,
            width=self.title_underline_width
        )
        ypos += self.title_underline_width + self.title_gap

        # Draw the top box
        top = self.draw_top()
        image.alpha_composite(
            top,
            ((image.width - top.width) // 2, ypos)
        )

        ypos += top.height + self.top_gap

        # Draw the summaries
        summary_image = self.draw_summaries()
        image.alpha_composite(
            summary_image,
            ((image.width - summary_image.width) // 2, ypos)
        )
        ypos += summary_image.height + self.summary_gap

        # Draw the bottom box
        bottom = self.draw_bottom()
        image.alpha_composite(
            bottom,
            ((image.width - bottom.width) // 2, ypos)
        )

        # Draw the footer
        ypos = image.height
        ypos -= self.date_gap
        date_text = self.data_date.strftime(
            "Monthly Statistics • As of %d %b • {} {}".format(self.data_name, self.data_discrim)
        )
        size = self.date_font.getsize(date_text)
        ypos -= size[1]
        draw.text(
            ((image.width - size[0]) // 2, ypos),
            date_text,
            font=self.date_font,
            fill=self.date_colour
        )
        return image

    def draw_summaries(self) -> Image:
        this_month_text = " THIS MONTH: {} Hours".format(int(sum(self.hours_this_month)))
        this_month_length = int(self.this_month_font.getlength(this_month_text))
        last_month_text = " LAST MONTH: {} Hours".format(int(sum(self.hours_last_month)))
        last_month_length = int(self.last_month_font.getlength(last_month_text))

        image = Image.new(
            'RGBA',
            (
                self.this_month_image.width + this_month_length
                + self.summary_sep
                + self.last_month_image.width + last_month_length,
                self.this_month_image.height
            )
        )
        draw = ImageDraw.Draw(image)

        xpos = 0
        ypos = image.height // 2
        image.alpha_composite(
            self.this_month_image,
            (0, 0)
        )
        xpos += self.this_month_image.width
        draw.text(
            (xpos, ypos),
            this_month_text,
            fill=self.this_month_colour,
            font=self.this_month_font,
            anchor='lm'
        )

        xpos += self.summary_sep + this_month_length

        image.alpha_composite(
            self.last_month_image,
            (xpos, 0)
        )
        xpos += self.last_month_image.width
        draw.text(
            (xpos, ypos),
            last_month_text,
            fill=self.last_month_colour,
            font=self.last_month_font,
            anchor='lm'
        )
        return image

    def draw_top(self) -> Image:
        size_x = (
            self.top_hours_bg.width // 2 + self.top_hours_sep
            + (self.this_month_days - 1) * self.top_grid_x + self.top_this_end.width // 2
            + self.top_hours_bg.width // 2
        )
        size_y = (
            self.top_hours_bg.height // 2 + 4 * self.top_grid_y + self.top_date_pre_gap
            + self.top_date_height
            + self.top_time_bar_sep + int(self.top_this_hours_font.getlength('24 H  24 H'))
        )
        image = Image.new('RGBA', (size_x, size_y))
        draw = ImageDraw.Draw(image)

        x0 = self.top_hours_bg.width // 2 + self.top_hours_sep
        y0 = self.top_hours_bg.height // 2 + 4 * self.top_grid_y
        y0 += self.top_time_bar_sep + int(self.top_this_hours_font.getlength('24 H  24 H'))

        # Draw lines and numbers
        labels = list(int(i * self.max_hour_label // 4) for i in range(0, 5))

        xpos = x0 - self.top_hours_sep
        ypos = y0
        for label in labels:
            draw.line(
                ((xpos, ypos), (image.width, ypos)),
                width=self.top_line_width,
                fill=self.top_line_colour
            )

            image.alpha_composite(
                self.top_hours_bg,
                (xpos - self.top_hours_bg.width // 2, ypos - self.top_hours_bg.height // 2)
            )
            text = str(label)
            draw.text(
                (xpos, ypos),
                text,
                fill=self.top_hours_colour,
                font=self.top_hours_font,
                anchor='mm'
            )
            ypos -= self.top_grid_y

        # Draw dates
        xpos = x0
        ypos = y0 + self.top_date_pre_gap
        for i in range(1, self.this_month_days + 1):
            draw.text(
                (xpos, ypos),
                str(i),
                fill=self.top_date_colour,
                font=self.top_date_font,
                anchor='mt'
            )
            xpos += self.top_grid_x

        # Draw bars
        for i, (last_hours, this_hours) in enumerate(zip(self.hours_last_month, self.hours_this_month)):
            xpos = x0 + i * self.top_grid_x

            if not (last_hours or this_hours):
                continue

            bar_height = 0
            for draw_last in (last_hours > this_hours, not last_hours > this_hours):
                hours = last_hours if draw_last else this_hours
                height = (4 * self.top_grid_y) * (hours / self.max_hour_label)
                height = int(height)

                if height >= self.top_this_end.height:
                    bar = self.draw_vert_bar(height, last=draw_last)
                    bar_height = max(bar.height, bar_height)
                    image.alpha_composite(
                        bar,
                        (xpos - bar.width // 2, y0 - bar.height)
                    )

            # Draw text
            if bar_height:
                text = ['{} H'.format(hours) for hours in (last_hours, this_hours) if hours]
                text_size = self.top_this_hours_font.getsize('  '.join(text))
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
                        fill=self.top_last_hours_colour,
                        font=self.top_last_hours_font
                    )
                    txpos += self.top_last_hours_font.getlength('  '.join(text))
                if this_hours:
                    this_text = "{} H  ".format(int(this_hours))
                    text_draw.text(
                        (txpos, 0), this_text,
                        fill=self.top_this_hours_colour,
                        font=self.top_this_hours_font
                    )

                text_image = text_image.rotate(90, expand=True)
                text_image = text_image.crop(text_image.getbbox())

                image.alpha_composite(
                    text_image,
                    (xpos - text_image.width // 2,
                     y0 - bar_height - self.top_time_bar_sep - text_image.height)
                )

        return image

    def draw_vert_bar(self, height, last=False) -> Image:
        image = Image.new('RGBA', (self.top_this_end.width - 1, height))

        if last:
            end = self.top_last_end
            colour = self.top_last_colour
        else:
            end = self.top_this_end
            colour = self.top_this_colour

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
        image = self.btm_frame.copy()
        draw = ImageDraw.Draw(image)

        xpos, ypos = self.bottom_margins

        # Draw the weekdays
        y0 = self.month_background.height + self.month_gap
        for i, weekday in enumerate(self.weekdays):
            y = y0 + i * self.btm_grid_y
            image.alpha_composite(
                self.weekday_background,
                (xpos, ypos + y)
            )
            draw.text(
                (xpos + self.weekday_background.width // 2, ypos + y + self.weekday_background.height // 2),
                weekday,
                fill=self.weekday_colour,
                font=self.weekday_font,
                anchor='mm'
            )

        # Draw the months
        x0 = self.weekday_background.width + self.weekday_sep
        for i, date in enumerate(self.months):
            name = date.strftime('%B').upper()

            x = x0 + i * (self.month_background.width + self.month_sep)
            image.alpha_composite(
                self.month_background,
                (xpos + x, ypos)
            )
            draw.text(
                (xpos + x + self.month_background.width // 2,
                 ypos + self.month_background.height // 2),
                name,
                fill=self.month_colour,
                font=self.month_font,
                anchor='mm'
            )

            heatmap = self.draw_month_heatmap(date)
            image.alpha_composite(
                heatmap,
                (xpos + x + self.month_background.width // 2 - heatmap.width // 2, ypos + y0)
            )

        # Draw the streak and stats information
        x = xpos + self.weekday_background.width // 2
        y = image.height - self.bottom_margins[1]

        key_text = "Current streak: "
        key_len = self.stats_key_font.getlength(key_text)
        value_text = "{} day{}".format(
            self.current_streak,
            's' if self.current_streak != 1 else ''
        )
        draw.text(
            (x, y),
            key_text,
            font=self.stats_key_font,
            fill=self.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.stats_value_font,
            fill=self.stats_value_colour
        )
        x += self.stats_sep

        key_text = "Daily average: "
        key_len = self.stats_key_font.getlength(key_text)
        value_text = "{} hour{}".format(
            (hours := int(self.average_time // 3600)),
            's' if hours != 1 else ''
        )
        draw.text(
            (x, y),
            key_text,
            font=self.stats_key_font,
            fill=self.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.stats_value_font,
            fill=self.stats_value_colour
        )
        x += self.stats_sep

        key_text = "Longest streak: "
        key_len = self.stats_key_font.getlength(key_text)
        value_text = "{} day{}".format(
            self.longest_streak,
            's' if self.current_streak != 1 else ''
        )
        draw.text(
            (x, y),
            key_text,
            font=self.stats_key_font,
            fill=self.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.stats_value_font,
            fill=self.stats_value_colour
        )
        x += self.stats_sep

        key_text = "Days learned: "
        key_len = self.stats_key_font.getlength(key_text)
        value_text = "{}%".format(
            int((100 * self.days_learned) // self.days_since_start)
        )
        draw.text(
            (x, y),
            key_text,
            font=self.stats_key_font,
            fill=self.stats_key_colour
        )
        draw.text(
            (x + key_len, y),
            value_text,
            font=self.stats_value_font,
            fill=self.stats_value_colour
        )
        x += self.stats_sep

        return image

    def draw_month_heatmap(self, month_start) -> Image:
        cal = calendar.monthcalendar(month_start.year, month_start.month)
        columns = len(cal)

        size_x = (
            (columns - 1) * self.btm_grid_x
            + self.heatmap_mask.width
        )
        size_y = (
            6 * self.btm_grid_y + self.heatmap_mask.height
        )

        image = Image.new('RGBA', (size_x, size_y))

        x0 = self.heatmap_mask.width // 2
        y0 = self.heatmap_mask.height // 2

        for (i, week) in enumerate(cal):
            xpos = x0 + i * self.btm_grid_x
            for (j, day) in enumerate(week):
                if day:
                    ypos = y0 + j * self.btm_grid_y
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
            return self.heatmap_mask
        else:
            amount = min(time / self.average_time, 2) / 2
            index = math.ceil(amount * len(self.heatmap_colours)) - 1
            colour = self.heatmap_colours[index]

            image = Image.new('RGBA', self.heatmap_mask.size)
            image.paste(colour, mask=self.heatmap_mask)
            return image
