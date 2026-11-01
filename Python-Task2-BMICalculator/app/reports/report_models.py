"""Validated export options and immutable, profile-scoped report snapshots."""
from dataclasses import dataclass
from datetime import date, datetime
import re
import unicodedata
from app.core.validator import ValidationError
from app.database.models import Profile
from app.services.analytics_service import AnalyticsData, PERIODS

class ReportError(Exception):
    """An understandable export failure, without raw filesystem/rendering details."""

@dataclass(frozen=True)
class ReportOptions:
    title: str = 'BMI Measurement Summary'
    period: str = 'All records'
    include_history: bool = True
    include_charts: bool = True
    start_date: date | None = None
    end_date: date | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.title,str) or not self.title.strip() or len(self.title.strip())>100:
            raise ValidationError('Report title must contain 1 to 100 characters.')
        if any(unicodedata.category(c).startswith('C') for c in self.title):
            raise ValidationError('Report title cannot contain control characters.')
        object.__setattr__(self,'title',self.title.strip())
        if type(self.include_history) is not bool or type(self.include_charts) is not bool:
            raise ValidationError('Report inclusion options must be true or false.')
        if self.period not in (*PERIODS,'Custom dates'):
            raise ValidationError('Choose a supported reporting period.')
        if self.period=='Custom dates':
            if type(self.start_date) is not date or type(self.end_date) is not date:
                raise ValidationError('Enter both dates as YYYY-MM-DD.')
            if self.start_date>self.end_date:
                raise ValidationError('The start date must not follow the end date.')
        elif self.start_date is not None or self.end_date is not None:
            raise ValidationError('Custom dates require the Custom dates period.')

@dataclass(frozen=True)
class ReportData:
    profile: Profile
    options: ReportOptions
    analytics: AnalyticsData
    generated_at: datetime
    all_time_count: int

    def __post_init__(self) -> None:
        if self.analytics.profile_id!=self.profile.id or any(r.profile_id!=self.profile.id for r in self.analytics.records):
            raise ValidationError('Report records must belong to the selected profile.')
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValidationError('Report generation time must include a timezone.')
        if self.all_time_count<len(self.analytics.records):
            raise ValidationError('Report record counts are inconsistent.')

    @property
    def period_label(self) -> str:
        if self.options.period=='Custom dates':
            return f'{self.options.start_date.isoformat()} to {self.options.end_date.isoformat()} (inclusive UTC dates)'
        return self.options.period


def safe_filename(name: str, generated_at: datetime) -> str:
    """ASCII basename with a fixed prefix (also avoids Windows reserved names)."""
    stem=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode()
    stem=re.sub(r'[^A-Za-z0-9_-]+','_',stem).strip('_')[:45] or 'profile'
    return f'BMI_Insight_{stem}_{generated_at:%Y-%m-%d}.pdf'
