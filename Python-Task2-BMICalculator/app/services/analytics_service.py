"""Pure time filtering/statistics and a profile-scoped history service adapter."""
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import fmean
from app.core.validator import ValidationError
from app.database.models import Measurement
from .history_service import HistoryService

PERIODS = ('Last 30 days', 'Last 3 months', 'Last 6 months', 'Last 12 months', 'All records')

@dataclass(frozen=True)
class Statistics:
    count: int
    latest: Measurement | None = None
    previous: Measurement | None = None
    bmi_change: float | None = None
    weight_change: float | None = None
    bmi_change_from_first: float | None = None
    weight_change_from_first: float | None = None
    highest_bmi: float | None = None
    lowest_bmi: float | None = None
    average_bmi: float | None = None

@dataclass(frozen=True)
class AnalyticsData:
    profile_id: int | None
    period: str
    records: tuple[Measurement, ...]
    dates: tuple[datetime, ...]
    statistics: Statistics
    start: datetime | None
    end: datetime

    @property
    def bmi_values(self) -> tuple[float, ...]:
        return tuple(record.bmi_value for record in self.records)

    @property
    def weight_values(self) -> tuple[float, ...]:
        return tuple(record.weight_kg for record in self.records)


def period_start(period: str, now: datetime) -> datetime | None:
    """Rolling UTC 30 days or calendar months; month ends clamp to valid dates."""
    if period not in PERIODS:
        raise ValidationError('Choose a supported measurement period.')
    if period == 'All records': return None
    if period == 'Last 30 days': return now-timedelta(days=30)
    months = {'Last 3 months':3,'Last 6 months':6,'Last 12 months':12}[period]
    index=now.year*12+now.month-1-months
    year,month=divmod(index,12);month+=1
    return now.replace(year=year,month=month,day=min(now.day,monthrange(year,month)[1]))


def prepare_history(records: list[Measurement] | tuple[Measurement, ...], profile_id: int | None,
                    period: str = 'All records', now: datetime | None = None) -> AnalyticsData:
    """Sort without dropping ties; every statistic uses the selected-period subset."""
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValidationError('Analytics time must include a timezone.')
    now=now.astimezone(timezone.utc)
    start=period_start(period,now)
    if any(r.profile_id != profile_id for r in records):
        raise ValidationError('History contains records from a different profile.')
    dated=[]
    for record in records:
        try:
            date=datetime.fromisoformat(record.measured_at)
            if date.tzinfo is None or date.utcoffset() is None: raise ValueError()
            date=date.astimezone(timezone.utc)
        except (ValueError,TypeError) as error:
            raise ValidationError('A stored measurement timestamp is invalid.') from error
        if start is None or start <= date <= now: dated.append((date,record))
    dated.sort(key=lambda item:(item[0],item[1].id))
    ordered=tuple(record for _,record in dated)
    stats=Statistics(0)
    if ordered:
        latest=ordered[-1];previous=ordered[-2] if len(ordered)>1 else None
        stats=Statistics(len(ordered),latest,previous,
            latest.bmi_value-previous.bmi_value if previous else None,
            latest.weight_kg-previous.weight_kg if previous else None,
            latest.bmi_value-ordered[0].bmi_value if previous else None,
            latest.weight_kg-ordered[0].weight_kg if previous else None,
            max(r.bmi_value for r in ordered),min(r.bmi_value for r in ordered),
            fmean(r.bmi_value for r in ordered))
    return AnalyticsData(profile_id,period,ordered,tuple(date for date,_ in dated),stats,start,now)


class AnalyticsService:
    def __init__(self, history: HistoryService):
        self.history=history

    def snapshot(self, profile_id: int | None, period: str = 'All records',
                 now: datetime | None = None) -> AnalyticsData:
        """One repository-backed history read per requested snapshot, never raw GUI SQL."""
        records=[] if profile_id is None else self.history.history(profile_id)
        return prepare_history(records,profile_id,period,now)
