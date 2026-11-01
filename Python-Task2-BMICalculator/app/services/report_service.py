"""Prepare reports through existing services; no rendering or SQL here."""
from dataclasses import replace
from datetime import datetime, time, timezone
from app.core.validator import ValidationError
from app.reports.report_models import ReportData, ReportOptions
from app.services.analytics_service import prepare_history
from app.services.profile_service import ProfileService
from app.services.history_service import HistoryService

class ReportService:
    def __init__(self, profiles: ProfileService, history: HistoryService):
        self.profiles=profiles
        self.history=history

    def prepare(self, profile_id: int, options: ReportOptions,
                now: datetime | None = None) -> ReportData:
        """Capture sorted records; custom end dates include their complete UTC day."""
        if not isinstance(options,ReportOptions):
            raise ValidationError('Choose valid report options.')
        now=now or datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValidationError('Report time must include a timezone.')
        now=now.astimezone(timezone.utc)
        profile=self.profiles.get(profile_id)
        records=self.history.history(profile_id)
        if options.period=='Custom dates':
            start=datetime.combine(options.start_date,time.min,timezone.utc)
            end=datetime.combine(options.end_date,time.max,timezone.utc)
            all_data=prepare_history(records,profile_id,now=now)
            selected=[r for r,d in zip(all_data.records,all_data.dates) if start<=d<=end]
            data=replace(prepare_history(selected,profile_id,now=now),period='Custom dates',start=start,end=end)
        else:
            data=prepare_history(records,profile_id,options.period,now)
        return ReportData(profile,options,data,now,len(records))
