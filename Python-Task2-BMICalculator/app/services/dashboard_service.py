"""Dashboard snapshots retain all-time counts separately from period statistics."""
from dataclasses import dataclass
from datetime import datetime
from app.services.analytics_service import AnalyticsData, AnalyticsService, prepare_history

@dataclass(frozen=True)
class DashboardData:
    selected: AnalyticsData
    all_time_count: int

class DashboardService:
    def __init__(self, analytics: AnalyticsService):
        self.analytics=analytics

    def snapshot(self, profile_id: int | None, period: str = 'All records',
                 now: datetime | None = None, *, all_data: AnalyticsData | None = None) -> DashboardData:
        all_data=all_data or self.analytics.snapshot(profile_id,now=now)
        if all_data.profile_id!=profile_id or all_data.period!='All records':
            from app.core.validator import ValidationError
            raise ValidationError('Dashboard requires all history for the selected profile.')
        return DashboardData(prepare_history(all_data.records,profile_id,period,all_data.end),len(all_data.records))


def describe_change(value: float | None, unit: str) -> str:
    """Describe direction neutrally; full precision determines direction."""
    if value is None:return 'No previous measurement available.'
    if value==0:return f'No change in {unit}.'
    amount=f'{abs(value):.2f}' if abs(value)>=0.005 else 'less than 0.01'
    return f'{"Increased" if value>0 else "Decreased"} by {amount} {unit}.'
