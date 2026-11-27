
from datetime import datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from hrms.models import Attendance, AttendanceSession


class Command(BaseCommand):
    help = "Automatically close forgotten attendance sessions at midnight."

    def handle(self, *args, **options):
        today = timezone.localdate()
        current_timezone = timezone.get_current_timezone()

        attendance_records = Attendance.objects.filter(
            date__lt=today
        ).filter(
            Q(sessions__check_out_datetime__isnull=True) |
            Q(sessions__is_auto_closed=True)
        ).distinct()

        closed_count = 0
        recalculated_count = 0

        for attendance_id in attendance_records.values_list("id", flat=True):
            try:
                with transaction.atomic():
                    attendance = Attendance.objects.select_for_update().get(
                        id=attendance_id
                    )

                    open_sessions = list(
                        AttendanceSession.objects.select_for_update().filter(
                            attendance=attendance,
                            check_out_datetime__isnull=True
                        ).order_by("check_in_datetime")
                    )

                    day_end = timezone.make_aware(
                        datetime.combine(
                            attendance.date,
                            time(23, 59, 59)
                        ),
                        current_timezone
                    )

                    newly_closed = 0

                    for session in open_sessions:
                        if session.check_in_datetime > day_end:
                            continue

                        session.check_out_datetime = day_end
                        session.is_auto_closed = True
                        session.save(update_fields=[
                            "check_out_datetime",
                            "is_auto_closed"
                        ])
                        newly_closed += 1

                    completed_sessions = list(
                        AttendanceSession.objects.filter(
                            attendance=attendance,
                            check_out_datetime__isnull=False
                        ).order_by("check_in_datetime")
                    )

                    verified_sessions = [
                        session for session in completed_sessions
                        if not session.is_auto_closed
                    ]

                    total_work_duration = timedelta(0)
                    automatic_break_duration = timedelta(0)
                    previous_session = None

                    for session in verified_sessions:
                        duration = (
                            session.check_out_datetime -
                            session.check_in_datetime
                        )

                        if duration < timedelta(0):
                            raise ValueError(
                                "Invalid attendance session duration."
                            )

                        total_work_duration += duration

                        if previous_session:
                            gap = (
                                session.check_in_datetime -
                                previous_session.check_out_datetime
                            )

                            if gap < timedelta(0):
                                raise ValueError(
                                    "Attendance sessions cannot overlap."
                                )

                            automatic_break_duration += gap

                        previous_session = session

                    if verified_sessions:
                        daily_total_duration = (
                            verified_sessions[-1].check_out_datetime -
                            verified_sessions[0].check_in_datetime
                        )
                    else:
                        daily_total_duration = timedelta(0)

                    if completed_sessions:
                        last_session = completed_sessions[-1]

                        attendance.check_out_datetime = (
                            last_session.check_out_datetime
                        )
                        attendance.check_out_time = timezone.localtime(
                            last_session.check_out_datetime
                        ).time()
                        attendance.check_out_latitude = (
                            last_session.check_out_latitude
                        )
                        attendance.check_out_longitude = (
                            last_session.check_out_longitude
                        )

                    attendance.total_duration = daily_total_duration
                    attendance.break_duration = automatic_break_duration
                    attendance.net_work_duration = total_work_duration

                    attendance.save(update_fields=[
                        "check_out_datetime",
                        "check_out_time",
                        "check_out_latitude",
                        "check_out_longitude",
                        "total_duration",
                        "break_duration",
                        "net_work_duration"
                    ])

                    closed_count += newly_closed
                    recalculated_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Attendance {attendance.id}: "
                            f"Closed {newly_closed} session(s). "
                            f"Gross: {daily_total_duration}, "
                            f"Break: {automatic_break_duration}, "
                            f"Net: {total_work_duration}"
                        )
                    )

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Attendance {attendance_id}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Automatic closure completed. "
                f"Sessions closed: {closed_count}, "
                f"Attendance records recalculated: {recalculated_count}"
            )
        )
