from . import views

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'posts'

urlpatterns = [
    # Профайл пользователя
    path('profile/<str:username>/', views.profile, name='profile'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
    # Главная страница
    path('', views.index, name='index'),
    path('group/<slug:slug>/', views.posts_group, name='posts_group'),
    # Просмотр записи
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    # Создание поста
    path('create/', views.post_create, name='post_create'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('follow/', views.follow_index, name='follow_index'),
]
# Эта колдограмма будет работать,
# когда ваш сайт в режиме отладки.
# Он позволяет обращаться к файлам в директории,
# указанной в MEDIA_ROOT по имени, через префикс MEDIA_URL.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
