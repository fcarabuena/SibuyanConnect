from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.town import get_current_town

from .models import Post


def post_list(request):
    posts = Post.objects.published().for_town(get_current_town(request)).select_related("municipality")
    category = request.GET.get("category")
    if category:
        posts = posts.filter(category=category)
    page = Paginator(posts, 10).get_page(request.GET.get("page"))
    return render(request, "news/list.html", {
        "page": page, "categories": Post.Category.choices, "active_category": category,
    })


def post_detail(request, pk, slug):
    post = get_object_or_404(Post.objects.published(), pk=pk)
    if post.slug != slug:
        return redirect(post, permanent=True)
    return render(request, "news/detail.html", {"post": post})


class LatestPostsFeed(Feed):
    title = "SibuyanConnect - News & Updates"
    link = "/news/"
    description = "Announcements and advisories from Magdiwang, San Fernando and Cajidiocan."

    def items(self):
        return Post.objects.published()[:30]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary

    def item_pubdate(self, item):
        return item.published_at

    def item_categories(self, item):
        return [item.get_category_display()]
