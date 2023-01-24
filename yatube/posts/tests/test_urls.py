from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.no_author = User.objects.create_user(username='notauthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текстовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = Client()
        self.authorized_client.force_login(PostURLTest.no_author)
        self.author.force_login(PostURLTest.user)

    def test_pages_for_all(self):
        """Доступность страниц для любого пользователя."""
        list_of_pages = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user}/',
            f'/posts/{self.post.id}/'
        )
        for page in list_of_pages:
            with self.subTest(address=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_post_page(self):
        """Доступность страницы редактирования для автора поста."""
        response = self.author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_create_page(self):
        """
        Доступность страницы создания поста.
        Для авторизованного пользователя.
        """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_for_noautor(self):
        """Тест страницы редактирования и редиректа для не автора поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': PostURLTest.post.pk}))

    def test_404_page(self):
        """Тест ошибки 404 для несуществующей страницы."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_redirect_to_login(self):
        """Тест редиректа гостя на страницу авторизации."""
        redirected_pages = (
            '/create/',
            f'/posts/{self.post.id}/edit/',
            f'/profile/{self.post.author}/follow',
            f'/profile/{self.post.author}/unfollow'
        )
        for page in redirected_pages:
            with self.subTest(address=page):
                response = self.guest_client.get(page)
                self.assertRedirects(response,
                                     reverse('login') + '?next=' + page)

    def test_urls_used_correct_template_for_all(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html'

        }
        for address, template in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)
