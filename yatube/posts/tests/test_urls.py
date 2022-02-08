# Каждый логический набор тестов — это класс,
# который наследуется от базового класса TestCase
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности адреса task/test-slug/
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug=3
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
            group=cls.group
        )

    def test_urls_uses_correct_template_authorized_client(self):
        """URL-адрес пользователя использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{URLTests.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{URLTests.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = URLTests.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    @unittest.skip
    def test_urls_uses_correct_template_guest_client(self):
        """URL-адрес гостя использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{URLTests.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{URLTests.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = URLTests.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_correct_code_guest_client(self):
        """Проверка переадресации гостя."""
        templates_url_names = {
            '/create/': 302,
            f'/posts/{URLTests.post.pk}/edit/': 302,
        }
        for address, code in templates_url_names.items():
            with self.subTest(address=address):
                response = URLTests.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_correct_code_authorized_client(self):
        """Проверка переадресации пользователя."""
        # Шаблоны по адресам
        templates_url_names = {
            '/': 200,
            f'/group/{self.post.group.slug}/': 200,
            f'/profile/{self.user.username}/': 200,
            f'/posts/{URLTests.post.pk}/': 200,
            '/create/': 200,
            f'/posts/{URLTests.post.pk}/edit/': 200,
        }
        for address, code in templates_url_names.items():
            with self.subTest(address=address):
                response = URLTests.authorized_client.get(address)
                self.assertEqual(response.status_code, code)
