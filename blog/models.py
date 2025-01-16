from django.db import models
from django import forms

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.snippets.models import register_snippet

from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.search import index

from django.core.paginator import Paginator
from wagtail.images.models import Image





#Blog Index Page
class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)

        # Number of posts per page
        posts_per_page = 10

        

        # Add featured posts to context
        featured_posts = BlogPage.objects.filter(is_featured=True).live().order_by('-first_published_at')[:3]
        context['featured_posts'] = featured_posts

        # list all live blog pages, ordered by date
        blogpages = self.get_children().live().order_by('-first_published_at')

        # Paginate the blog posts
        paginator = Paginator(blogpages, posts_per_page)
        page_number = request.GET.get('page', 1)  # Default to page 1
        page = paginator.get_page(page_number)

        context['blogpages'] = blogpages
        context['paginator'] = paginator
        return context


# Blog Page Tag (Snippet)
class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name = 'tagged_items',
        on_delete=models.CASCADE
    )


# Blog Post (Single)
class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    # authors (snippet)
    authors = ParentalManyToManyField('blog.Author', blank=True)

    # tag manger
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    # Featured
    is_featured = models.BooleanField(default=False, help_text="Mark this post as featured on the homepage.")

    

    # main image
    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
        # If no gallery image, return a default image
            try:
                default_image = Image.objects.filter(title="default-image").first()  
                return default_image
            except Image.DoesNotExist:
                return None  # Fallback if the default image doesn't exist
   

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('date'),
            FieldPanel('authors', widget=forms.CheckboxSelectMultiple),
            FieldPanel('tags'),
            FieldPanel('is_featured'),
        ], heading="Blog Information"),
            FieldPanel("intro"),
        FieldPanel("body"),
        InlinePanel('gallery_images', label="Gallery Images"),
    ]

class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel('image'),
        FieldPanel('caption'),
    ]


# Author model (Snippet)
@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+'
    )

    panels = [
        FieldPanel('name'),
        FieldPanel('author_image'),
    ]

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Authors'


# Defining Tag views
class BlogTagIndexPage(Page):
    def get_context(self, request):
        # Filter by tag
        tag = request.GET.get('tag')
        blogpages = BlogPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context['blogpages'] = blogpages
        return context



