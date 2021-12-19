import itertools
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

from .utils import asset_path, inter_font


def format_lb(pos):
    """
    Format a leaderboard position into a string.
    """
    if pos is None:
        return 'Unranked'

    if pos % 10 == 1 and pos % 100 != 11:
        return f"{pos}ST"

    if pos % 10 == 2 and pos % 100 != 12:
        return f"{pos}ND"

    if pos % 10 == 3 and pos % 100 != 13:
        return f"{pos}RD"

    return f"{pos}TH"


class StatsCard:
    # Drawing constant or default values
    scale = 2  # General size scale to match background resolution

    # Background images
    bg_path = asset_path("stats/5_row_bg.png")
    alt_bg_path = asset_path("stats/6_row_bg.png")

    # Inner container
    container_position = (60, 50)  # Position of top left corner
    container_size = (1410, 675)  # Size of the inner container
    alt_container_size = (1410, 800)  # Size of the inner container

    # Major (topmost) header
    header_font = inter_font('Black', size=int(27*scale))
    header_colour = '#DDB21D'
    header_gap = int(35*scale)  # Gap between header and column contents
    header_height = header_font.getsize('STATISTICS')[1]

    # First column
    col1_header = 'STATISTICS'
    stats_subheader_font = inter_font('Black', size=int(21*scale))
    stats_subheader_colour = '#FFFFFF'
    stats_subheader_size = stats_subheader_font.getsize('LEADERBOARD POSITION')
    stats_text_gap = int(12*scale)  # Gap between stat lines
    alt_stats_text_gap = int(16*scale)  # Gap between stat lines
    stats_text_font = inter_font('SemiBold', size=int(19*scale))
    stats_text_height = stats_text_font.getsize('DAILY')[1]
    stats_text_colour = '#BABABA'

    col1_size = (
        stats_subheader_size[0],
        header_height + header_gap
        + 3 * stats_subheader_size[1]
        + 6 * stats_text_height
        + 8 * stats_text_gap
    )

    alt_col1_size = (
        stats_subheader_size[0],
        header_height + header_gap
        + 3 * stats_subheader_size[1]
        + 6 * stats_text_height
        + 8 * alt_stats_text_gap
    )

    # Second column
    col2_header = 'STUDY STREAK'
    col2_date_font = inter_font('Black', size=int(21*scale))
    col2_date_colour = '#FFFFFF'
    col2_hours_colour = '#1473A2'
    col2_date_gap = int(25*scale)  # Gap between date line and calender
    col2_subheader_height = col2_date_font.getsize('JANUARY')[1]
    cal_column_sep = int(35*scale)
    cal_weekday_text = ('S', 'M', 'T', 'W', 'T', 'F', 'S')
    cal_weekday_font = inter_font('ExtraBold', size=int(21*scale))
    cal_weekday_colour = '#FFFFFF'
    cal_weekday_height = cal_weekday_font.getsize('S')[1]
    cal_weekday_gap = int(23*scale)
    cal_number_font = inter_font('Medium', size=int(20*scale))
    cal_number_colour = '#BABABA'
    cal_number_gap = int(20*scale)
    cal_number_size = cal_number_font.getsize('88')
    cal_streak_end = Image.open(asset_path('stats/streak_endpoint.png')).convert("RGBA")
    cal_streak_middle = Image.open(asset_path('stats/streak_middle.png')).convert("RGBA")
    cal_streak_middle_colour = '#1B3343'

    cal_size = (
        7 * cal_number_size[0] + 6 * cal_column_sep + cal_streak_end.width // 2,
        5 * cal_number_size[1] + 4 * cal_number_gap
        + cal_weekday_height + cal_weekday_gap
        + cal_streak_end.height // 2
    )

    alt_cal_size = (
        7 * cal_number_size[0] + 6 * cal_column_sep + cal_streak_end.width // 2,
        6 * cal_number_size[1] + 5 * cal_number_gap
        + cal_weekday_height + cal_weekday_gap
        + cal_streak_end.height // 2
    )

    col2_size = (
        cal_size[0],
        header_height + header_gap
        + col2_subheader_height + col2_date_gap
        + cal_size[1]
    )

    alt_col2_size = (
        alt_cal_size[0],
        header_height + header_gap
        + col2_subheader_height + col2_date_gap
        + alt_cal_size[1]
    )

    def __init__(self, lb_data, time_data, workouts, streak_data, date=None, draft=False, **kwargs):
        self.draft = draft

        self.data_lb_time = lb_data[0]  # Position on time leaderboard, or None
        self.data_lb_lc = lb_data[1]  # Position on coin leaderboard, or None

        self.data_time_daily = int(time_data[0])  # Daily time in seconds
        self.data_time_weekly = int(time_data[1])  # Weekly time in seconds
        self.data_time_monthly = int(time_data[2])  # Monthly time in seconds
        self.data_time_all = int(time_data[3])  # All time in seconds

        self.data_workouts = workouts  # Number of workout sessions
        self.data_streaks = streak_data  # List of streak day ranges to show

        # Extract date info
        date = date if date else datetime.today()  # Date to show for month/year
        month_first_day = date.replace(day=1)
        month_days = (month_first_day.replace(month=(month_first_day.month % 12) + 1) - timedelta(days=1)).day

        self.date = date
        self.month = date.strftime('%B').upper()
        self.first_weekday = month_first_day.weekday()  # Which weekday the month starts on
        self.month_days = month_days
        self.alt_layout = (month_days + self.first_weekday + 1) > 35  # Whether to use the alternate layout

        if self.alt_layout:
            self.bg_path = self.alt_bg_path
            self.container_size = self.alt_container_size
            self.cal_size = self.alt_cal_size
            self.col2_size = self.alt_col2_size
            self.stats_text_gap = self.alt_stats_text_gap
            self.col1_size = self.alt_col1_size

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

    def draw_inner_container(self):
        container = Image.new('RGBA', self.container_size)

        col1 = self.draw_column_1()
        col2 = self.draw_column_2()

        if col1.width + col2.width > container.width:
            # TODO: Error
            print("Warning: Container overflow! Columns are too wide.")

        container.alpha_composite(col1)
        container.alpha_composite(col2, (container.width - col2.width, 0))

        if self.draft:
            draw = ImageDraw.Draw(container)
            draw.rectangle(((0, 0), (self.container_size[0]-1, self.container_size[1]-1)))

        return container

    def draw_column_1(self) -> Image:
        # Create new image for column 1
        col1 = Image.new('RGBA', self.col1_size)
        draw = ImageDraw.Draw(col1)

        if self.draft:
            draw.rectangle(((0, 0), (self.col1_size[0]-1, self.col1_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Write header
        draw.text(
            (0, position),
            self.col1_header,
            font=self.header_font,
            fill=self.header_colour
        )
        position += self.header_height + self.header_gap

        # Leaderboard
        draw.text(
            (0, position),
            'LEADERBOARD POSITION',
            font=self.stats_subheader_font,
            fill=self.stats_subheader_colour
        )
        position += self.col2_subheader_height + self.stats_text_gap

        draw.text(
            (0, position),
            f"TIME: {format_lb(self.data_lb_time)}",
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        draw.text(
            (0, position),
            f"LC: {format_lb(self.data_lb_lc)}",
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        # Study time
        draw.text(
            (0, position),
            'STUDY TIME',
            font=self.stats_subheader_font,
            fill=self.stats_subheader_colour
        )
        position += self.col2_subheader_height + self.stats_text_gap

        draw.text(
            (0, position),
            f'DAILY: {self.data_time_daily // 3600} H',
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        draw.text(
            (0, position),
            f'MONTHLY: {self.data_time_monthly // 3600} H',
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        draw.text(
            (0, position),
            f'WEEKLY: {self.data_time_weekly // 3600} H',
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        draw.text(
            (0, position),
            f'ALL TIME: {self.data_time_all // 3600} H',
            font=self.stats_text_font,
            fill=self.stats_text_colour
        )
        position += self.stats_text_height + self.stats_text_gap

        position += self.stats_subheader_size[1] // 2

        # Workouts
        workout_text = "WORKOUTS: "
        draw.text(
            (0, position),
            workout_text,
            font=self.stats_subheader_font,
            fill=self.stats_subheader_colour,
            anchor='lm'
        )
        xposition = self.stats_subheader_font.getlength(workout_text)
        draw.text(
            (xposition, position),
            str(self.data_workouts),
            font=self.stats_text_font,
            fill=self.stats_subheader_colour,
            anchor='lm'
        )

        return col1

    def draw_column_2(self) -> Image:
        # Create new image for column 1
        col2 = Image.new('RGBA', self.col2_size)
        draw = ImageDraw.Draw(col2)

        if self.draft:
            draw.rectangle(((0, 0), (self.col2_size[0]-1, self.col2_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Write header
        draw.text(
            (0, position),
            self.col2_header,
            font=self.header_font,
            fill=self.header_colour
        )
        position += self.header_height + self.header_gap

        # Draw date line
        month_text = "{}: ".format(self.month)
        draw.text(
            (0, position),
            month_text,
            font=self.col2_date_font,
            fill=self.col2_date_colour
        )
        xposition = self.col2_date_font.getlength(month_text)
        draw.text(
            (xposition, position),
            f"{self.data_time_monthly // 3600} HRS",
            font=self.col2_date_font,
            fill=self.col2_hours_colour
        )
        year_text = str(self.date.year)
        xposition = col2.width - self.col2_date_font.getlength(year_text)
        draw.text(
            (xposition, position),
            year_text,
            font=self.col2_date_font,
            fill=self.col2_date_colour
        )
        position += self.col2_subheader_height + self.col2_date_gap

        # Draw calendar
        cal = self.draw_calendar()

        col2.alpha_composite(cal, (0, position))

        return col2

    def draw_calendar(self) -> Image:
        cal = Image.new('RGBA', self.cal_size)
        draw = ImageDraw.Draw(cal)

        if self.draft:
            draw.rectangle(((0, 0), (self.cal_size[0]-1, self.cal_size[1]-1)))

        xpos, ypos = (0, 0)  # Approximate position of top left corner to draw on

        # Constant offset to mid basepoint of text
        xoffset = self.cal_streak_end.width // 2
        yoffset = self.cal_number_size[1] // 2

        # Draw the weekdays
        for i, l in enumerate(self.cal_weekday_text):
            draw.text(
                (xpos + xoffset, ypos + yoffset),
                l,
                font=self.cal_weekday_font,
                fill=self.cal_weekday_colour,
                anchor='mm'
            )
            xpos += self.cal_number_size[0] + self.cal_column_sep
        ypos += self.cal_weekday_height + self.cal_weekday_gap
        xpos = 0

        streak_starts = list(itertools.chain(*self.data_streaks))
        streak_middles = list(itertools.chain(*(range(i+1, j) for i, j in self.data_streaks)))
        streak_pairs = set(i for i, j in self.data_streaks if j-i == 1)

        # Draw the days of the month
        num_diff_x = self.cal_number_size[0] + self.cal_column_sep
        num_diff_y = self.cal_number_size[1] + self.cal_number_gap
        offset = (self.first_weekday + 1) % 7

        centres = [
            (xpos + xoffset + (i + offset) % 7 * num_diff_x,
             ypos + yoffset + (i + offset) // 7 * num_diff_y)
            for i in range(0, self.month_days)
        ]

        for day in streak_middles:
            i = day - 1
            if i >= len(centres):
                # Shouldn't happen, but ignore
                continue
            x, y = centres[i]
            week_day = (i + offset) % 7

            top = y - self.cal_streak_end.height // 2
            bottom = y + self.cal_streak_end.height // 2 - 1

            # Middle of streak on edges
            if week_day == 0 or i == 0:
                # Draw end bobble
                cal.paste(
                    self.cal_streak_middle,
                    (x - self.cal_streak_end.width // 2, top)
                )
                if week_day != 6:
                    # Draw rectangle forwards
                    draw.rectangle(
                        ((x, top), (x + num_diff_x, bottom)),
                        fill=self.cal_streak_middle_colour,
                        width=0
                    )
            elif week_day == 6 or i == self.month_days - 1:
                # Draw end bobble
                cal.paste(
                    self.cal_streak_middle,
                    (x - self.cal_streak_end.width // 2, top)
                )
                if week_day != 0:
                    # Draw rectangle backwards
                    draw.rectangle(
                        ((x - num_diff_x, top), (x, bottom)),
                        fill=self.cal_streak_middle_colour,
                        width=0
                    )
            else:
                # Draw rectangle on either side
                draw.rectangle(
                    ((x - num_diff_x, top), (x + num_diff_x, bottom)),
                    fill=self.cal_streak_middle_colour,
                    width=0
                )

        for i, (x, y) in enumerate(centres):
            numstr = str(i + 1)

            # Streak endpoint
            if i + 1 in streak_starts:
                if i + 1 in streak_pairs and (i + offset) % 7 != 6:
                    # Draw rectangle forwards
                    top = y - self.cal_streak_end.height // 2
                    bottom = y + self.cal_streak_end.height // 2 - 1
                    draw.rectangle(
                        ((x, top), (x + num_diff_x, bottom)),
                        fill=self.cal_streak_middle_colour,
                        width=0
                    )
                cal.alpha_composite(
                    self.cal_streak_end,
                    (x - self.cal_streak_end.width // 2, y - self.cal_streak_end.height // 2)
                )

            draw.text(
                (x, y),
                numstr,
                font=self.cal_number_font,
                fill=self.cal_number_colour,
                anchor='mm'
            )

        return cal
