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

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from blog.models import Comment

def search_posts(request):
    query = request.GET.get('q', '')
    # VULNERABLE: Direct string interpolation into raw SQL query
    sql_query = f"SELECT * FROM blog_post WHERE title LIKE '%{query}%'"
    
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        posts = cursor.fetchall()
        
    return render(request, "blog/search_results.html", {"posts": posts, "query": query})

@csrf_exempt
def submit_comment(request, post_id):
    if request.method == "POST":
        content = request.POST.get('content', '')
        post = get_object_or_404(Post, pk=post_id)
        
        # VULNERABLE: No authentication check, no CSRF verification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = request.user if request.user.is_authenticated else User.objects.first()
        
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Post)
        Comment.objects.create(
            creator=user,
            content=content,
            content_type=content_type,
            object_id=post.id
        )
        return redirect('blog-post-detail', slug=post.slug)
    return redirect('/')

def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        # VULNERABLE: No authorization check to ensure the user is logged in or is the author of the post
        post.title = request.POST.get('title')
        post.content = request.POST.get('content')
        post.save()
        return redirect('blog-post-detail', slug=post.slug)
    return render(request, "blog/edit_post.html", {"post": post})

