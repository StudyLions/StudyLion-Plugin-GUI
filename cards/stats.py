import itertools
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

from babel.translator import LocalBabel

from ..utils import font_height
from ..base import Card, Layout, fielded, Skin, CardMode
from ..base.Skin import (
    AssetField, BlobField, StringField, NumberField, RawField,
    FontField, ColourField, PointField, ComputedField, FieldDesc,
    LazyStringField
)

babel = LocalBabel('stats-gui')
_p = babel._p


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


@fielded
class StatsSkin(Skin):
    _env = {
        'scale': 2  # General size scale to match background resolution
    }

    mode: RawField = CardMode.TEXT
    font_family: RawField = 'Inter'

    # Background images
    background: AssetField = "stats/background.png"

    # Inner container
    container_position: PointField = (60, 50)  # Position of top left corner
    container_size: PointField = (1410, 800)  # Size of the inner container

    # Major (topmost) header
    header_font: FontField = ('Black', 27)
    header_colour: ColourField = '#DDB21D'
    header_gap: NumberField = 35  # Gap between header and column contents
    header_height: ComputedField = lambda skin: font_height(skin.header_font)

    # First column
    col1_header: LazyStringField = _p('skin:stats|header:col1', 'STATISTICS')
    col1_header_height: ComputedField = lambda skin: font_height(skin.header_font)
    stats_subheader_leaderboard: LazyStringField = _p(
        'skin:stats|subheader:leaderboard', 'LEADERBOARD POSITION'
    )
    study_stats_subheader_study: LazyStringField = _p(
        'skin:stats|mode:study|subheader:study',
        'STUDY TIME'
    )
    voice_stats_subheader_study: LazyStringField = _p(
        'skin:stats|mode:voice|subheader:study',
        'VOICE TIME'
    )
    text_stats_subheader_study: LazyStringField = _p(
        'skin:stats|mode:text|subheader:study',
        'MESSAGES'
    )
    anki_stats_subheader_study: LazyStringField = _p(
        'skin:stats|mode:anki|subheader:study',
        'CARDS REVIEWED'
    )
    stats_subheader_study: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_stats_subheader_study,
        CardMode.VOICE: skin.voice_stats_subheader_study,
        CardMode.TEXT: skin.text_stats_subheader_study,
        CardMode.ANKI: skin.anki_stats_subheader_study,
    }[skin.mode]

    stats_subheader_workouts: LazyStringField = _p(
        'skin:stats|subheader:workouts',
        'WORKOUTS'
    )
    stats_subheader_pregap: NumberField = 8
    stats_subheader_font: FontField = ('Black', 21)
    stats_subheader_colour: ColourField = '#FFFFFF'
    stats_subheader_bbox: ComputedField = lambda skin: (
        skin.stats_subheader_font.getbbox(skin.stats_subheader_leaderboard)
    )
    stats_subheader_size: ComputedField = lambda skin: (
        skin.stats_subheader_bbox[2] - skin.stats_subheader_bbox[0],
        skin.stats_subheader_bbox[3] - skin.stats_subheader_bbox[1],
    )
    stats_text_gap: NumberField = 13  # Gap between stat lines
    stats_text_font: FontField = ('SemiBold', 19)
    stats_text_daily: LazyStringField = _p(
        'skin:stats|field:daily',
        'DAILY'
    )
    stats_text_weekly: LazyStringField = _p(
        'skin:stats|field:weekly',
        'WEEKLY'
    )
    stats_text_monthly: LazyStringField = _p(
        'skin:stats|field:monthly',
        'MONTHLY'
    )
    stats_text_alltime: LazyStringField = _p(
        'skin:stats|field:alltime',
        'ALL TIME'
    )
    stats_text_time: LazyStringField = _p(
        'skin:stats|field:time',
        'TIME'
    )
    stats_text_anki: LazyStringField = _p(
        'skin:stats|field:anki',
        'ANKI: COMING SOON'
    )
    stats_text_height: ComputedField = lambda skin: font_height(skin.stats_text_font)
    stats_text_colour: ColourField = '#BABABA'

    col1_size: ComputedField = lambda skin: (
        skin.stats_subheader_size[0],
        skin.col1_header_height + skin.header_gap
        + 3 * skin.stats_subheader_size[1]
        + 2 * skin.stats_subheader_pregap
        + 6 * skin.stats_text_height
        + 8 * skin.stats_text_gap
    )

    # Second column
    study_col2_header: LazyStringField = _p(
        'skin:stats|mode:study|header:col2',
        "STUDY STREAK"
    )
    voice_col2_header: LazyStringField = _p(
        'skin:stats|mode:voice|header:col2',
        "VOICE STREAK"
    )
    text_col2_header: LazyStringField = _p(
        'skin:stats|mode:text|header:col2',
        "ACTIVITY STREAK"
    )
    anki_col2_header: LazyStringField = _p(
        'skin:stats|mode:anki|header:col2',
        "ANKI REVIEW STREAK"
    )
    col2_header: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_col2_header,
        CardMode.VOICE: skin.voice_col2_header,
        CardMode.TEXT: skin.text_col2_header,
        CardMode.ANKI: skin.anki_col2_header,
    }[skin.mode]
    col2_date_font: FontField = ('Black', 21)
    col2_date_colour: ColourField = '#FFFFFF'

    study_col2_hours_text: LazyStringField = _p(
        'skin:stats|mode:study|field:col2_summary',
        "{amount} HRS"
    )
    voice_col2_hours_text: LazyStringField = _p(
        'skin:stats|mode:voice|field:col2_summary',
        "{amount} HRS"
    )
    text_col2_hours_text: LazyStringField = _p(
        'skin:stats|mode:text|field:col2_summary',
        "{amount} XP"
    )
    anki_col2_hours_text: LazyStringField = _p(
        'skin:stats|mode:anki|field:col2_summary',
        "{amount} CARDS"
    )
    col2_hours_text: ComputedField = lambda skin: {
        CardMode.STUDY: skin.study_col2_hours_text,
        CardMode.VOICE: skin.voice_col2_hours_text,
        CardMode.TEXT: skin.text_col2_hours_text,
        CardMode.ANKI: skin.anki_col2_hours_text,
    }[skin.mode]
    col2_hours_colour: ColourField = '#1473A2'
    col2_date_gap: NumberField = 25  # Gap between date line and calender
    col2_subheader_height: ComputedField = lambda skin: font_height(skin.col2_date_font)
    cal_column_sep: NumberField = 35
    cal_weekday_font: FontField = ('ExtraBold', 21)
    cal_weekday_colour: ColourField = '#FFFFFF'
    cal_weekday_height: ComputedField = lambda skin: font_height(skin.cal_weekday_font)
    cal_weekday_gap: NumberField = 23
    cal_number_font: FontField = ('Medium', 20)
    cal_number_end_colour: ColourField = '#BABABA'
    cal_number_colour: ColourField = '#BABABA'
    cal_number_gap: NumberField = 28
    alt_cal_number_gap: NumberField = 20
    cal_number_bbox: ComputedField = lambda skin: skin.cal_number_font.getbbox('88')
    cal_number_size: ComputedField = lambda skin: (
        skin.cal_number_bbox[2] - skin.cal_number_bbox[0],
        skin.cal_number_bbox[3] - skin.cal_number_bbox[1],
    )

    cal_streak_mask: AssetField = 'stats/streak_mask.png'

    cal_weekday_text: LazyStringField = _p(
        'skin:stats|cal|weekdays',
        "S,M,T,W,T,F,S"
    )
    cal_month_names: LazyStringField = _p(
        'skin:stats|cal|months',
        "JANUARY,FEBRUARY,MARCH,APRIL,MAY,JUNE,JULY,AUGUST,SEPTEMBER,OCTOBER,NOVEMBER,DECEMBER"
    )

    cal_streak_end_colour: ColourField = '#1473A2'
    cal_streak_end_colour_override: ColourField = None
    cal_streak_end: BlobField = FieldDesc(
        BlobField,
        mask_field='cal_streak_mask',
        colour_field='cal_streak_end_colour',
        colour_override_field='cal_streak_end_colour_override'
    )

    cal_streak_middle_colour: ColourField = '#1B3343'
    cal_streak_middle_colour_override: ColourField = None
    cal_streak_middle: BlobField = FieldDesc(
        BlobField,
        mask_field='cal_streak_mask',
        colour_field='cal_streak_middle_colour',
        colour_override_field='cal_streak_middle_colour_override'
    )

    cal_size: ComputedField = lambda skin: (
        7 * skin.cal_number_size[0] + 6 * skin.cal_column_sep + skin.cal_streak_end.width // 2,
        5 * skin.cal_number_size[1] + 4 * skin.cal_number_gap
        + skin.cal_weekday_height + skin.cal_weekday_gap
        + skin.cal_streak_end.height // 2
    )

    alt_cal_size: ComputedField = lambda skin: (
        7 * skin.cal_number_size[0] + 6 * skin.cal_column_sep + skin.cal_streak_end.width // 2,
        6 * skin.cal_number_size[1] + 5 * skin.alt_cal_number_gap
        + skin.cal_weekday_height + skin.cal_weekday_gap
        + skin.cal_streak_end.height // 2
    )

    col2_size: ComputedField = lambda skin: (
        skin.cal_size[0],
        skin.header_height + skin.header_gap
        + skin.col2_subheader_height + skin.col2_date_gap
        + skin.cal_size[1]
    )

    alt_col2_size: ComputedField = lambda skin: (
        skin.alt_cal_size[0],
        skin.header_height + skin.header_gap
        + skin.col2_subheader_height + skin.col2_date_gap
        + skin.alt_cal_size[1]
    )


class StatsLayout(Layout):
    """
    Parameters
    ----------
    skin: StatsSkin
    lb_data: tuple[Optional[int], Optional[int]]
        Describes the position on the activity and coin leaderboards, respectively.
    period_activity: tuple[str, str, str, str]
        Strings representing activity over daily, weekly, monthly, and total periods.
    month_activity: str
        String to display for total month activity.
    workouts: int
        Number of workout sessions complete (deprecated)
    streak_data: list[tuple[int, int]]
        List of streak day ranges.
    date: Optional[datetime]
        date to show for month and year
    draft: bool
        Whether to render the card in 'draft' mode.
        Draws explicit bounding boxes around each section.
    """
    def __init__(self, skin,
                 lb_data,
                 period_activity,
                 month_activity,
                 workouts,
                 streak_data,
                 date=None,
                 draft=False, **kwargs):
        self.draft = draft

        self.skin = skin

        self.data_lb_time = lb_data[0]  # Position on time leaderboard, or None
        self.data_lb_lc = lb_data[1]  # Position on coin leaderboard, or None

        self.data_time: tuple[str, str, str, str] = period_activity
        self.data_month: str = month_activity

        self.data_workouts = workouts  # Number of workout sessions
        self.data_streaks = streak_data  # List of streak day ranges to show

        # Extract date info
        date = date if date else datetime.today()  # Date to show for month/year
        month_first_day = date.replace(day=1)
        month_days = (month_first_day.replace(month=(month_first_day.month % 12) + 1) - timedelta(days=1)).day

        self.date = date
        self.month = self.skin.cal_month_names.split(',')[date.month - 1].upper()
        self.first_weekday = month_first_day.weekday()  # Which weekday the month starts on
        self.month_days = month_days
        self.alt_layout = (month_days + self.first_weekday + 1) > 35  # Whether to use the alternate layout

        if self.alt_layout:
            self.skin.fields['cal_number_gap'].value = self.skin.alt_cal_number_gap
            self.skin.fields['cal_size'].value = self.skin.alt_cal_size
            self.skin.fields['col2_size'].value = self.skin.alt_col2_size

        self.image: Image = None  # Final Image

    def draw(self):
        # Load/copy background
        image = self.skin.background

        # Draw inner container
        inner_container = self.draw_inner_container()

        # Paste inner container on background
        image.alpha_composite(inner_container, self.skin.container_position)

        self.image = image
        return image

    def draw_inner_container(self):
        container = Image.new('RGBA', self.skin.container_size)

        col1 = self.draw_column_1()
        col2 = self.draw_column_2()

        container.alpha_composite(col1)
        container.alpha_composite(col2, (container.width - col2.width, 0))

        if self.draft:
            draw = ImageDraw.Draw(container)
            draw.rectangle(((0, 0), (self.skin.container_size[0]-1, self.skin.container_size[1]-1)))

        return container

    def draw_column_1(self) -> Image:
        # Create new image for column 1
        col1 = Image.new('RGBA', self.skin.col1_size)
        draw = ImageDraw.Draw(col1)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.col1_size[0]-1, self.skin.col1_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Write header
        draw.text(
            (0, position),
            self.skin.col1_header,
            font=self.skin.header_font,
            fill=self.skin.header_colour
        )
        position += self.skin.header_height + self.skin.header_gap

        # Leaderboard
        draw.text(
            (0, position),
            self.skin.stats_subheader_leaderboard,
            font=self.skin.stats_subheader_font,
            fill=self.skin.stats_subheader_colour
        )
        position += self.skin.col2_subheader_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            f"{self.skin.stats_text_time}: {format_lb(self.data_lb_time)}",
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            self.skin.stats_text_anki,
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        position += self.skin.stats_subheader_pregap
        # Study time
        draw.text(
            (0, position),
            self.skin.stats_subheader_study,
            font=self.skin.stats_subheader_font,
            fill=self.skin.stats_subheader_colour
        )
        position += self.skin.col2_subheader_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            f'{self.skin.stats_text_daily}: {self.data_time[0]}',
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            f'{self.skin.stats_text_weekly}: {self.data_time[1]}',
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            f'{self.skin.stats_text_monthly}: {self.data_time[2]}',
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        draw.text(
            (0, position),
            f'{self.skin.stats_text_alltime}: {self.data_time[3]}',
            font=self.skin.stats_text_font,
            fill=self.skin.stats_text_colour
        )
        position += self.skin.stats_text_height + self.skin.stats_text_gap

        position += self.skin.stats_subheader_size[1] // 2

        position += self.skin.stats_subheader_pregap
        # Workouts
        # Hidden as a deactivated feature
        # workout_text = f"{self.skin.stats_subheader_workouts}: "
        # draw.text(
        #     (0, position),
        #     workout_text,
        #     font=self.skin.stats_subheader_font,
        #     fill=self.skin.stats_subheader_colour,
        #     anchor='lm'
        # )
        # xposition = self.skin.stats_subheader_font.getlength(workout_text)
        # draw.text(
        #     (xposition, position),
        #     str(self.data_workouts),
        #     font=self.skin.stats_text_font,
        #     fill=self.skin.stats_subheader_colour,
        #     anchor='lm'
        # )

        return col1

    def draw_column_2(self) -> Image:
        # Create new image for column 1
        col2 = Image.new('RGBA', self.skin.col2_size)
        draw = ImageDraw.Draw(col2)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.col2_size[0]-1, self.skin.col2_size[1]-1)))

        # Tracking current drawing height
        position = 0

        # Write header
        draw.text(
            (0, position),
            self.skin.col2_header,
            font=self.skin.header_font,
            fill=self.skin.header_colour
        )
        position += self.skin.header_height + self.skin.header_gap

        # Draw date line
        month_text = "{}: ".format(self.month)
        draw.text(
            (0, position),
            month_text,
            font=self.skin.col2_date_font,
            fill=self.skin.col2_date_colour
        )
        xposition = self.skin.col2_date_font.getlength(month_text)
        draw.text(
            (xposition, position),
            self.data_month,
            font=self.skin.col2_date_font,
            fill=self.skin.col2_hours_colour
        )
        year_text = str(self.date.year)
        xposition = col2.width - self.skin.col2_date_font.getlength(year_text)
        draw.text(
            (xposition, position),
            year_text,
            font=self.skin.col2_date_font,
            fill=self.skin.col2_date_colour
        )
        position += self.skin.col2_subheader_height + self.skin.col2_date_gap

        # Draw calendar
        cal = self.draw_calendar()

        col2.alpha_composite(cal, (0, position))

        return col2

    def draw_calendar(self) -> Image:
        cal = Image.new('RGBA', self.skin.cal_size)
        draw = ImageDraw.Draw(cal)

        if self.draft:
            draw.rectangle(((0, 0), (self.skin.cal_size[0]-1, self.skin.cal_size[1]-1)))

        xpos, ypos = (0, 0)  # Approximate position of top left corner to draw on

        # Constant offset to mid basepoint of text
        xoffset = self.skin.cal_streak_end.width // 2
        yoffset = self.skin.cal_number_size[1] // 2

        # Draw the weekdays
        for i, l in enumerate(self.skin.cal_weekday_text.split(',')):
            draw.text(
                (xpos + xoffset, ypos + yoffset),
                l,
                font=self.skin.cal_weekday_font,
                fill=self.skin.cal_weekday_colour,
                anchor='mm'
            )
            xpos += self.skin.cal_number_size[0] + self.skin.cal_column_sep
        ypos += self.skin.cal_weekday_height + self.skin.cal_weekday_gap
        xpos = 0

        streak_starts = list(itertools.chain(*self.data_streaks))
        streak_middles = list(itertools.chain(*(range(i+1, j) for i, j in self.data_streaks)))
        streak_pairs = set(i for i, j in self.data_streaks if j-i == 1)

        # Draw the days of the month
        num_diff_x = self.skin.cal_number_size[0] + self.skin.cal_column_sep
        num_diff_y = self.skin.cal_number_size[1] + self.skin.cal_number_gap
        offset = (self.first_weekday + 1) % 7

        centres = [
            (xpos + xoffset + (i + offset) % 7 * num_diff_x,
             ypos + yoffset + (i + offset) // 7 * num_diff_y)
            for i in range(0, self.month_days)
        ]

        for day in streak_middles:
            if day < 1:
                continue
            i = day - 1
            if i >= len(centres):
                # Shouldn't happen, but ignore
                continue
            x, y = centres[i]
            week_day = (i + offset) % 7

            top = y - self.skin.cal_streak_end.height // 2
            bottom = y + self.skin.cal_streak_end.height // 2 - 1

            # Middle of streak on edges
            if week_day == 0 or i == 0:
                # Draw end bobble
                cal.paste(
                    self.skin.cal_streak_middle,
                    (x - self.skin.cal_streak_end.width // 2, top)
                )
                if week_day != 6:
                    # Draw rectangle forwards
                    draw.rectangle(
                        ((x, top), (x + num_diff_x, bottom)),
                        fill=self.skin.cal_streak_middle_colour,
                        width=0
                    )
            elif week_day == 6 or i == self.month_days - 1:
                # Draw end bobble
                cal.paste(
                    self.skin.cal_streak_middle,
                    (x - self.skin.cal_streak_end.width // 2, top)
                )
                if week_day != 0:
                    # Draw rectangle backwards
                    draw.rectangle(
                        ((x - num_diff_x, top), (x, bottom)),
                        fill=self.skin.cal_streak_middle_colour,
                        width=0
                    )
            else:
                # Draw rectangle on either side
                draw.rectangle(
                    ((x - num_diff_x, top), (x + num_diff_x, bottom)),
                    fill=self.skin.cal_streak_middle_colour,
                    width=0
                )

        for i, (x, y) in enumerate(centres):
            # Streak endpoint
            if i + 1 in streak_starts:
                if i + 1 in streak_pairs and (i + offset) % 7 != 6:
                    # Draw rectangle forwards
                    top = y - self.skin.cal_streak_end.height // 2
                    bottom = y + self.skin.cal_streak_end.height // 2 - 1
                    draw.rectangle(
                        ((x, top), (x + num_diff_x, bottom)),
                        fill=self.skin.cal_streak_middle_colour,
                        width=0
                    )
                cal.alpha_composite(
                    self.skin.cal_streak_end,
                    (x - self.skin.cal_streak_end.width // 2, y - self.skin.cal_streak_end.height // 2)
                )

        for i, (x, y) in enumerate(centres):
            numstr = str(i + 1)

            draw.text(
                (x, y),
                numstr,
                font=self.skin.cal_number_font,
                fill=self.skin.cal_number_end_colour if (i+1 in streak_starts) else self.skin.cal_number_colour,
                anchor='mm'
            )

        return cal


class StatsCard(Card):
    route = 'stats_card'
    card_id = 'stats'

    layout = StatsLayout
    skin = StatsSkin

    display_name = _p(
        'card:stats|display_name',
        "User Stats"
    )

    @classmethod
    async def sample_args(cls, ctx, **kwargs):
        return {
            'lb_data': (21, 123),
            'period_activity': (
                "01:00",
                "10:00",
                "36:25",
                "57:30",
            ),
            'month_activity': "36 hours",
            'workouts': 50,
            'streak_data': [(1, 3), (7, 8), (10, 10), (12, 16), (18, 25), (27, 31)],
            'date': datetime(2022, 2, 1)
        }
