import json
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count
from django.db.utils import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import CustomUser

from .models import (Comment, CommentVoteTracking, Post, PostVoteTracking,
                     parse_site)


# logger do terminala
# TODO dodaj printy do konsoli
def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_ch = logging.StreamHandler()
    log_ch.setLevel(logging.DEBUG)
    # format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_ch.setFormatter(formatter)
    logger.addHandler(log_ch)

    return logger


log = get_logger()


def get_tracking(user, items):
    if user.id:
        if len(items) > 0:
            is_post = isinstance(items[0], Post)
            if is_post:
                return [x.post.id for x in PostVoteTracking.objects.filter(user__id=user.id)]
            else:
                return [x.comment.id for x in CommentVoteTracking.objects.filter(user__id=user.id)]
    return []


def render_index_template(request, posts, tracking, category, page, additional_context=None):
    context = {
        'posts': posts,
        'tracking': tracking,
        'page': page + 1,
        'category': category,
        'counter_init': settings.PAGE_LIMIT * (page - 1)
    }
    if additional_context:
        context.update(additional_context)
    return render(request,
                  template_name='index.html',
                  context=context)


def get_page(page):
    # jeśli strona istnieje to ją wyświetl w przeciwnym wypadku zwróć błąd
    if page:
        return page
    else:
        return 1


def get_best(page):
    now = timezone.now()
    return Post.objects.filter(
        insert_date__range=(now - timedelta(days=settings.HOTTEST_DAY_LIMIT), now)). \
               annotate(num_comments=Count('comment')). \
               order_by('-num_comments', '-votes', '-user__karma')[
           (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]


def index(request, page=None):
    page = get_page(page)
    posts = get_best(page)
    tracking = get_tracking(request.user, posts)
    return render_index_template(request, posts, tracking, '', page)


def profile(request, user_id):
    user_query = CustomUser.objects.filter(id=user_id)

    if user_query:
        user = user_query[0]

        if user.id == request.user.id:
            context = {
                'user_id': user_id,
                'username': user.username,
                'karma': user.karma,
                'about': user.about,
                'email': user.email,
                'own_user': True
            }
        else:
            context = {
                'user_id': user_id,
                'username': user.username,
                'karma': user.karma,
                'about': user.about,
                'own_user': False
            }
        return render(request, 'user/profile.html', context=context)
    else:
        return redirect('index')


def validate_user_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        #  niepoprawny mail
        return False


def update_profile(request, user_id):
    if request.method == 'POST':
        body = request.POST

        user = request.user
        if 'about' in body:
            user.about = body['about']
        if 'email' in body and validate_user_email(body['email']):
            user.email = body['email']
        user.save()

        context = {
            'user_id': user_id,
            'username': user.username,
            'karma': user.karma,
            'about': user.about,
            'email': user.email,
            'own_user': True
        }
        return render(request, 'user/profile.html', context=context)


def check_submission(title, url, text):
    if not title:
        return False
    elif title == '':
        return False
    elif not url and not text:
        return False
    elif url:
        try:
            parse_site(url)
            return True
        except IndexError:
            return False
    else:
        return True


def submit(request):
    if request.method == 'POST':

        title = request.POST['title'].strip()
        url = request.POST['url']
        text = request.POST['text'].strip()

        if not check_submission(title, url, text):
            return render(request, 'posts/submit.html', context={'errors': True})

        user = request.user
        user.karma += 1
        user.save()

        current_post = Post(title=title, url=url, user=user)
        current_post.save()

        if text:
            current_comment = Comment(content=text, user=user, post=current_post)
            current_comment.save()

        return redirect('new')

    else:
        return render(request, 'posts/submit.html')


def post(request, post_id, error=None):
    if request.method == 'GET':

        current_post = Post.objects.get(pk=post_id)
        current_comments = current_post.comment_set.filter(reply=None).order_by('-insert_date')

        context = {'post': current_post,
                   'post_tracking': get_tracking(request.user, [current_post]),
                   'tracking': get_tracking(request.user, current_comments),
                   'root_comments': current_comments,
                   'error': error}

        return render(request, 'posts/post.html', context=context)

    else:
        return HttpResponse('ERROR')


def post_comment(request, post_id):
    if request.method == 'GET':
        return redirect('post', post_id=post_id)

    # komenarz w poście
    elif request.method == 'POST':

        content = request.POST['text'].strip()

        # na wypadek gdyby komentarz był pusty
        # ustaw flagę 'empty_comment' aby wyświetlić
        # ostrzeżenie
        if content == '':
            error = 'empty_comment'
            request.method = 'GET'
            return post(request=request,
                        post_id=post_id,
                        error=error)

        else:
            current_post = Post.objects.get(pk=post_id)
            current_comment = Comment(user=request.user,
                                      post=current_post,
                                      reply=None,
                                      content=content)
            current_comment.save()
            return redirect('post', post_id=current_post.id)

    else:
        return redirect('post', post_id=post_id)


def post_edit(request, post_id, errors=False):
    current_post = Post.objects.get(pk=post_id)
    if request.user != current_post.user:
        return redirect('post', post_id=post_id)

    if request.method == 'GET':
        context = {'post': current_post}
        if errors:
            context.update({'errors': True})
        return render(request, 'posts/post_edit.html', context=context)

    elif request.method == 'POST':
        title = request.POST['title'].strip()
        if title == '':
            request.method = 'GET'
            return post_edit(request=request,
                             post_id=post_id,
                             errors=True)
        else:
            current_post.title = title
            current_post.save()
            return redirect('post', post_id=current_post.id)


def post_delete(request, post_id, errors=False, deleted=False):
    current_post = Post.objects.get(pk=post_id)
    if request.user != current_post.user:
        return redirect('post', post_id=post_id)

    if request.method == 'GET':
        if not deleted:
            context = {'post': current_post, 'errors': errors}
            return render(request, 'posts/post_delete.html', context=context)
        else:
            current_post.delete()
            context = {'deleted': deleted}
            return render(request, 'posts/post_delete.html', context=context)

    elif request.method == 'POST':
        delete = request.POST['delete']
        if delete == 'Tak':
            try:
                request.method = 'GET'
                return post_delete(request, post_id, errors=False, deleted=True)

            except Exception as ex:
                log.error(ex)
                request.method = 'GET'
                return post_delete(request, post_id, errors=True, deleted=False)
        else:
            request.method = 'GET'
            return post_edit(request=request,
                             post_id=post_id)


def comment(request, comment_id, error=None):
    current_comment = Comment.objects.get(pk=comment_id)

    if request.method == 'GET':
        current_replies = current_comment.comment_set.all().order_by('-insert_date')
        context = {'comment': current_comment,
                   'comment_tracking': get_tracking(request.user, [current_comment]),
                   'tracking': get_tracking(request.user, current_replies),
                   'root_comments': current_replies,
                   'error': error}
        return render(request, 'comments/comment.html', context=context)


def comment_reply(request, comment_id):
    if request.method == 'POST':

        content = request.POST['text'].strip()

        if content == '':
            request.method = 'GET'
            return comment(request=request,
                           comment_id=comment_id,
                           error='empty_comment')

        else:
            current_comment = Comment.objects.get(pk=comment_id)
            current_comment = Comment(user=request.user,
                                      post=current_comment.post,
                                      reply=current_comment,
                                      content=content)
            current_comment.save()
            return redirect('comment', comment_id=comment_id)

    else:
        return redirect('comment', comment_id=comment_id)


def comment_edit(request, comment_id, error=None):

    current_comment = Comment.objects.get(pk=comment_id)
    if request.user != current_comment.user:
        return redirect('comment', comment_id=comment_id)

    if request.method == 'GET':
        context = {'comment': current_comment}
        if error:
            context.update({'error': error})
        return render(request, 'comments/comment_edit.html', context=context)

    elif request.method == 'POST':

        content = request.POST['text'].strip()

        if content == '':
            return redirect('comment_edit', comment_id=comment_id)

        else:

            current_comment.content = content
            current_comment.save()
            return redirect('comment_edit', comment_id=comment_id)


def comment_delete(request, comment_id, error=None):

    current_comment = Comment.objects.get(pk=comment_id)
    if request.user != current_comment.user:
        return redirect('comment', comment_id=comment_id)

    if request.method == 'GET':
        context = {'comment': current_comment, 'error': error}
        return render(request, 'comments/comment_delete.html', context=context)

    elif request.method == 'POST':
        delete = request.POST['delete']

        # czyta wartość/value z pola input w templacie comment_delete.html
        if delete == 'Tak':

            if current_comment.reply_id:
                parent_id = current_comment.reply_id
                current_comment.delete()
                return redirect('comment', comment_id=parent_id)
            else:
                parent_id = current_comment.post_id
                current_comment.delete()
                return redirect('post', post_id=parent_id)

        else:
            return redirect('comment', comment_id=comment_id)


    else:
        return redirect('comment', comment_id=comment_id)


def upvote_post(request):
    return upvote(request, 'post')


def upvote_comment(request):
    return upvote(request, 'comment')


def upvote(request, item_str):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        if request.user.id:
            user = CustomUser.objects.filter(id=request.user.id)[0]
            if item_str == 'post':
                item = Post.objects.filter(id=body['id'])[0]
                tracking = PostVoteTracking(user=user, post=item)
            else:
                item = Comment.objects.filter(id=body['id'])[0]
                tracking = CommentVoteTracking(user=user, comment=item)

            try:
                tracking.save()

                # zwiększenie karmy
                item.user.karma += 1
                item.user.save()
                item.votes += 1
                item.save()

            except IntegrityError:
                return JsonResponse({'success': False, 'redirect': False})

            return JsonResponse({'success': True, 'redirect': False})
        else:
            return JsonResponse({'success': False, 'redirect': True})


def site(request, site, page=None):
    if request.method == 'GET':
        page = get_page(page)

        posts = Post.objects.filter(site=site). \
                    order_by('-insert_date')[
                (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]
        tracking = get_tracking(request.user, posts)

        return render_index_template(request, posts, tracking, 'site', page, {'site': site})


# nowe posty posortowane wg daty dodania
def new(request, page=None):
    if request.method == 'GET':
        page = get_page(page)

        posts = Post.objects. \
                    order_by('-insert_date')[
                (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]
        tracking = get_tracking(request.user, posts)

        return render_index_template(request, posts, tracking, 'new', page)


# nalepsze posty posortowane wg wyniku
def best(request, page=None):
    if request.method == 'GET':
        page = get_page(page)

        posts = Post.objects. \
                    order_by('-votes', '-user__karma')[
                (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]
        tracking = get_tracking(request.user, posts)

        return render_index_template(request, posts, tracking, 'best', page)


def submissions(request, user_id, page=None):
    if request.method == 'GET':
        page = get_page(page)

        posts = Post.objects.filter(user__id=user_id). \
                    order_by('-insert_date')[
                (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]
        tracking = get_tracking(request.user, posts)

        return render_index_template(request, posts, tracking, 'submissions', page,
                                     {'user_id': user_id})


def comments(request, user_id, page=None):
    if request.method == 'GET':
        page = get_page(page)

        current_comments = Post.objects.filter(user__id=user_id). \
                    order_by('-insert_date')[
                (page - 1) * settings.PAGE_LIMIT:settings.PAGE_LIMIT * page]

        context = {'tracking': get_tracking(request.user, current_comments),
                   'root_comments': current_comments,
                   'user_id': user_id,
                   'page': page + 1}

        return render(request, 'comments/comment_profile.html', context=context)

# TODO zmień na angielskie nazwy funkcji
# change to english
def wbudowie(request):
    return render(request, 'common/wbudowie.html')
