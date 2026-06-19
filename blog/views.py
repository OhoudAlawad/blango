from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from blog.models import Post
from blog.forms import CommentForm
import logging
# from django.views.decorators.cache import cache_page
# from django.views.decorators.vary import vary_on_cookie

logger = logging.getLogger(__name__)

# Create your views here.
# @cache_page(300)
# @vary_on_cookie
def index(request):
  # from django.http import HttpResponse
  # logger.debug("Index function is called!")
  # return HttpResponse(str(request.user).encode("ascii"))
  posts = Post.objects.filter(published_at__lte=timezone.now()).select_related("author")
  logger.debug("Got %d posts", len(posts))
  return render(request, "blog/index.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user.is_active:
        if request.method == "POST":
            comment_form = CommentForm(request.POST)

            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.content_object = post
                comment.creator = request.user
                comment.save()
                logger.info("Created comment on Post %d for user %s", post.pk, request.user)

                return redirect(request.path_info)
        else:
            comment_form = CommentForm()
    else:
        comment_form = None

    return render(
        request, "blog/post-detail.html", {"post": post, "comment_form": comment_form}
    )

def get_ip(request):
  from django.http import HttpResponse
  return HttpResponse(request.META['REMOTE_ADDR'])

from blog.models import Comment
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied

def search_posts(request):
    query = request.GET.get('q', '')
    # SECURE: Django ORM parameterizes variables and prevents SQL injection
    posts = Post.objects.filter(title__icontains=query)
    return render(request, "blog/search_results.html", {"posts": posts, "query": query})

@login_required
@csrf_protect
def submit_comment(request, post_id):
    if request.method == "POST":
        content = request.POST.get('content', '')
        post = get_object_or_404(Post, pk=post_id)
        
        # SECURE: Explicitly enforce CSRF verification and ensure authentication
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Post)
        Comment.objects.create(
            creator=request.user,
            content=content,
            content_type=content_type,
            object_id=post.id
        )
        return redirect('blog-post-detail', slug=post.slug)
    return redirect('/')

@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # SECURE: Verified user session and strict ownership checks
    if post.author != request.user and not request.user.is_superuser:
        raise PermissionDenied("You do not have permission to edit this post.")
        
    if request.method == "POST":
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        return redirect('blog-post-detail', slug=post.slug)
    return render(request, "blog/edit_post.html", {"post": post})

