__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.paginator import Paginator, Page

PAGE_RANGE_DISPLAYED = 10
MARGIN_PAGES_DISPLAYED = 1
SHOW_FIRST_PAGE_WHEN_INVALID = True


class SciPostPaginator(Paginator):
    def _get_page(self, *args, **kwargs):
        return SciPostPage(*args, **kwargs)


class SciPostPage(Page):
    def pages(self):
        """
        Custom pages set that tweaks the range of pages to be shown in the paginator.
        """
        if self.paginator.num_pages <= PAGE_RANGE_DISPLAYED:
            return range(1, self.paginator.num_pages + 1)
        result = []
        left_side = PAGE_RANGE_DISPLAYED / 2
        right_side = PAGE_RANGE_DISPLAYED - left_side
        if self.number > self.paginator.num_pages - PAGE_RANGE_DISPLAYED / 2:
            right_side = self.paginator.num_pages - self.number
            left_side = PAGE_RANGE_DISPLAYED - right_side
        elif self.number < PAGE_RANGE_DISPLAYED / 2:
            left_side = self.number
            right_side = PAGE_RANGE_DISPLAYED - left_side
        for page in range(1, self.paginator.num_pages + 1):
            if page <= MARGIN_PAGES_DISPLAYED:
                result.append(page)
                continue
            if page > self.paginator.num_pages - MARGIN_PAGES_DISPLAYED:
                result.append(page)
                continue
            if (page >= self.number - left_side) and (page <= self.number + right_side):
                result.append(page)
                continue
            if result[-1]:
                result.append(None)

        return result
