"""Views for Zinnia archives"""
import datetime

from django.urls import resolve
from django.utils import timezone
from django.utils.translation import get_language_from_request
from django.views.generic.dates import BaseArchiveIndexView
from django.views.generic.dates import BaseDayArchiveView
from django.views.generic.dates import BaseMonthArchiveView
from django.views.generic.dates import BaseTodayArchiveView
from django.views.generic.dates import BaseWeekArchiveView
from django.views.generic.dates import BaseYearArchiveView

from zinnia.models.entry import Entry
from zinnia.views.mixins.archives import ArchiveMixin
from zinnia.views.mixins.archives import PreviousNextPublishedMixin
from zinnia.views.mixins.callable_queryset import CallableQuerysetMixin
from zinnia.views.mixins.prefetch_related import PrefetchCategoriesAuthorsMixin
from zinnia.views.mixins.templates import \
    EntryQuerysetArchiveTemplateResponseMixin
from zinnia.views.mixins.templates import \
    EntryQuerysetArchiveTodayTemplateResponseMixin

def apply_pagecontent_to_view(request):
    """
    Fix the missing Draft / Publish button for AppHooks
    See  https://github.com/django-cms/django-cms/issues/7909
    Fix is inspired by this comment here https://github.com/django-cms/django-cms/issues/7712#issuecomment-1844845602
    You can remove this function after you upgrade to Django CMS 5.1
    """
    if not hasattr(request, 'toolbar'):
        return
    match = resolve(request.path)
    page_content = None
    language = get_language_from_request(request, check_path=True)
    if request.current_page:
        page_content = request.current_page.pagecontent_set.get(language=language)
    if page_content:
        request.toolbar.set_object(page_content)



class EntryArchiveMixin(ArchiveMixin,
                        PreviousNextPublishedMixin,
                        PrefetchCategoriesAuthorsMixin,
                        CallableQuerysetMixin,
                        EntryQuerysetArchiveTemplateResponseMixin):
    """
    Mixin combinating:

    - ArchiveMixin configuration centralizing conf for archive views.
    - PrefetchCategoriesAuthorsMixin to prefetch related objects.
    - PreviousNextPublishedMixin for returning published archives.
    - CallableQueryMixin to force the update of the queryset.
    - EntryQuerysetArchiveTemplateResponseMixin to provide a
      custom templates for archives.
    """
    queryset = Entry.published.all


class EntryIndex(EntryArchiveMixin,
                 EntryQuerysetArchiveTodayTemplateResponseMixin,
                 BaseArchiveIndexView):
    """
    View returning the archive index.
    """
    context_object_name = 'entry_list'
    def dispatch(self, request, *args, **kwargs):
        apply_pagecontent_to_view(request)
        return super().dispatch(request, *args, **kwargs)


class EntryYear(EntryArchiveMixin, BaseYearArchiveView):
    """
    View returning the archives for a year.
    """
    make_object_list = True
    template_name_suffix = '_archive_year'


class EntryMonth(EntryArchiveMixin, BaseMonthArchiveView):
    """
    View returning the archives for a month.
    """
    template_name_suffix = '_archive_month'


class EntryWeek(EntryArchiveMixin, BaseWeekArchiveView):
    """
    View returning the archive for a week.
    """
    template_name_suffix = '_archive_week'

    def get_dated_items(self):
        """
        Override get_dated_items to add a useful 'week_end_day'
        variable in the extra context of the view.
        """
        self.date_list, self.object_list, extra_context = super(
            EntryWeek, self).get_dated_items()
        self.date_list = self.get_date_list(self.object_list, 'day')
        extra_context['week_end_day'] = extra_context[
            'week'] + datetime.timedelta(days=6)
        return self.date_list, self.object_list, extra_context


class EntryDay(EntryArchiveMixin, BaseDayArchiveView):
    """
    View returning the archive for a day.
    """
    template_name_suffix = '_archive_day'


class EntryToday(EntryArchiveMixin, BaseTodayArchiveView):
    """
    View returning the archive for the current day.
    """
    template_name_suffix = '_archive_today'

    def get_dated_items(self):
        """
        Return (date_list, items, extra_context) for this request.
        And defines self.year/month/day for
        EntryQuerysetArchiveTemplateResponseMixin.
        """
        now = timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)
        today = now.date()
        self.year, self.month, self.day = today.isoformat().split('-')
        return self._get_dated_items(today)
