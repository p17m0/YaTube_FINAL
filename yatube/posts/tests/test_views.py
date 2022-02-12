import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.paginator import Page
from yatube.settings import QUANTITY
from django.core.cache import cache

from ..models import Post, Group, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug=3
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:posts_group', kwargs={'slug': self.group.slug})):
                'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': self.user.username})):
                'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id': PagesTests.post.pk})):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit',
                     kwargs={'post_id': PagesTests.post.pk})):
                'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_show_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': PagesTests.post.pk}))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }

        # Проверяем, что типы полей
        # формы в словаре context соответствуют ожиданиям
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    # Проверяем, что словарь context страницы /posts
    # в первом элементе списка object_list содержит ожидаемые значения
    def test_posts_group_show_correct_context(self):
        """Шаблон task_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:posts_group', kwargs={'slug': self.group.slug}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        objecta = response.context.get('group')
        page_obj = response.context.get('page_obj')
        title_0 = objecta.title
        description_0 = objecta.description
        slug_0 = objecta.slug
        self.assertEqual(title_0, self.group.title)
        self.assertEqual(description_0, self.group.description)
        self.assertEqual(slug_0, str(self.group.slug))
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj), 1)

    # Проверяем, что словарь context страницы task/test-slug
    # содержит ожидаемые значения
    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PagesTests.post.pk})))
        self.assertEqual(response.context.get('post').text, self.post.text)

    def test_profile(self):
        """Шаблон profile проверка контекста."""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})))
        page_obj = response.context.get('page_obj')
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(response.context.get('author').username,
                         self.user.username)

    def test_index(self):
        """Проверка view index."""
        response = self.client.get(reverse('posts:index'))
        page_obj = response.context.get('page_obj')
        self.assertIsInstance(page_obj, Page)
        self.assertEqual(len(page_obj), 1)
        self.assertIsInstance(page_obj[0], Post)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PaginationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(PaginationTest, cls).setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug=3
        )
        for i in range(15):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'{i}',
                group=cls.group
            )
        cls.posts_count = Post.objects.count()
        cls.second_quantity = cls.posts_count - QUANTITY

    def test_index_pagina(self):
        """Проверка view index pagina."""
        # Проверка не работает при кешировании
        response = self.client.get(reverse('posts:index'))
        cache.clear()
        tm = response.context.get('page_obj')
        self.assertEqual(len(tm), QUANTITY)

    def test_index_second_page_contains_five_records(self):
        """Проверка: на второй странице должно быть три поста."""
        # Проверка не работает при кешировании
        response = self.client.get(reverse('posts:index') + '?page=2')
        tm = response.context.get('page_obj')
        self.assertEqual(len(tm),
                         self.second_quantity)

    def test_profile(self):
        """Шаблон profile проверка контекста."""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})))
        page_obj = response.context.get('page_obj')
        self.assertEqual(len(page_obj), QUANTITY)

    def test_profile_second_page_contains_five_records(self):
        # Проверка: на второй странице должно быть три поста.
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2'))
        self.assertEqual(len(response.context.get('page_obj')),
                         self.second_quantity)

    def test_group_list_paginator(self):
        response = self.authorized_client.get(
            reverse('posts:posts_group', kwargs={'slug': self.group.slug}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        page_obj = response.context.get('page_obj')
        self.assertEqual(len(page_obj), QUANTITY)

    def test_group_list_paginator_second_page(self):
        response = self.authorized_client.get(
            reverse('posts:posts_group',
                    kwargs={'slug': self.group.slug}) + '?page=2')
        page_obj = response.context.get('page_obj')
        self.assertEqual(len(page_obj), self.second_quantity)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(CacheTest, cls).setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug=3
        )
        for i in range(15):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'{i}',
                group=cls.group
            )

    def setUp(self):
        cache.clear()

    def test_cache_index_page(self):
        '''Тест для проверки кеша index'''
        self.post2 = Post.objects.create(
            author=self.user,
            text='Тестовая группа',
            group=self.group,
        )
        pozt = self.post2
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj_1 = response.context.get('page_obj').object_list
        self.assertIn(pozt, page_obj_1)
        pozt.delete()
        page_obj_2 = response.context.get('page_obj').object_list
        self.assertEqual(page_obj_1, page_obj_2)
        cache.clear()
        page_obj_2 = response.context.get('page_obj').object_list
        self.assertEqual(page_obj_1, page_obj_2)


class FollowTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='HasNoName1')
        self.user2 = User.objects.create_user(username='HasNoName2')

        self.authorized_client1 = Client()
        self.authorized_client2 = Client()

        self.authorized_client1.force_login(self.user1)
        self.authorized_client2.force_login(self.user2)

    def test_follow(self):
        count_before = Follow.objects.count()
        response = self.authorized_client1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user2.username}))
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        page_obj = response.context.get('page_obj').object_list

        self.assertEqual(len(page_obj), 1)
        self.assertEqual(response.status_code, 302)
        s = len(Follow.objects.all())
        self.assertEqual(s, 1)
        count_after = Follow.objects.count()
        self.assertNotEqual(count_before, count_after)

    def test_unfollow(self):
        Follow.objects.create(author=self.user2, user=self.user1)
        count_before = Follow.objects.count()
        self.authorized_client1.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user2.username}))

        response1 = self.authorized_client1.get(reverse('posts:follow_index'))
        page_obj = response1.context.get('page_obj').object_list

        self.assertEqual(len(page_obj), 0)
        count_after = Follow.objects.count()
        self.assertNotEqual(count_before, count_after)

    def test_follow_post(self):
        self.post = Post.objects.create(
            author=self.user2,
            text='TEST FALLOWERZ',
            group=None
        )
        Follow.objects.create(author=self.user2, user=self.user1)
        response1 = self.authorized_client1.get(reverse('posts:follow_index'))
        page_obj = response1.context.get('page_obj').object_list

        self.assertEqual(len(page_obj), 1)
        s = len(Follow.objects.all())
        self.assertEqual(s, 1)

    def test_guest_follow(self):
        self.post = Post.objects.create(
            author=self.user2,
            text='TEST FALLOWERZ',
            group=None
        )
        response1 = self.authorized_client1.get(reverse('posts:follow_index'))
        page_obj = response1.context.get('page_obj').object_list

        self.assertEqual(len(page_obj), 0)
