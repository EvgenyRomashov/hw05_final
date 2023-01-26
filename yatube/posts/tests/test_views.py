import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from random import randint
from yatube.settings import NUMBER_OF_POSTS_PER_PAGE_BY_DEFAULT

from posts.models import Group, Post, Follow
from posts.forms import PostForm, CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
PAGINATOR_TEST_POSTS = randint(13, 20)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текстовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTest.user)

    def funс_post_in_context(self, response):
        """Функция для проверки наличия поста в контексте."""
        return self.assertIn('page_obj', response.context)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_name = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.post.author})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.pk})
            ),
            'posts/create_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': self.post.pk})
            )
        }
        for template, reverse_name in templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Тест контекста передаваемого на начальную страницу"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.funс_post_in_context(response)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertGreater(response.context['page_obj'].paginator.count, 0)
        RESP_CONTEXT_0 = response.context['page_obj'][0]
        self.assertEqual(RESP_CONTEXT_0.text, self.post.text)
        self.assertEqual(RESP_CONTEXT_0.author, self.post.author)
        self.assertEqual(RESP_CONTEXT_0.group, self.post.group)
        self.assertEqual(RESP_CONTEXT_0.image.name, self.post.image)

    def test_context_to_group_list(self):
        """Тест контекста для списка постов отфильтрованного по группе"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        )
        )
        self.funс_post_in_context(response)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertGreater(response.context['page_obj'].paginator.count, 0)
        self.assertIn('group', response.context)
        self.assertIsInstance(response.context['group'], Group)
        RESP_CONTEXT_0 = response.context['page_obj'][0]
        self.assertEqual(RESP_CONTEXT_0 .text, self.post.text)
        self.assertEqual(RESP_CONTEXT_0 .author, self.user)
        self.assertEqual(RESP_CONTEXT_0 .group, self.group)
        self.assertEqual(
            RESP_CONTEXT_0.image.name, self.post.image
        )
        self.assertEqual(response.context['group'], self.group)

    def test_context_to_profile(self):
        """Тест контекста для списка постов отфильтрованного по автору"""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}
        )
        )
        self.funс_post_in_context(response)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertGreater(response.context['page_obj'].paginator.count, 0)
        self.assertIn('author', response.context)
        self.assertIsInstance(response.context['author'], User)
        RESP_CONTEXT_0 = response.context['page_obj'][0]
        self.assertEqual(RESP_CONTEXT_0.text, self.post.text)
        self.assertEqual(RESP_CONTEXT_0.author, self.user)
        self.assertEqual(RESP_CONTEXT_0.group, self.group)
        self.assertEqual(
            RESP_CONTEXT_0.image.name, self.post.image
        )
        self.assertEqual(response.context['author'], self.user)

    def test_context_to_post_detail(self):
        """Тест контекста для одного поста"""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        )
        )
        self.assertIn('post', response.context)
        RESP_CONTEXT_0 = response.context['post']
        self.assertIsInstance(RESP_CONTEXT_0, Post)
        self.assertEqual(RESP_CONTEXT_0.text, self.post.text)
        self.assertEqual(RESP_CONTEXT_0.author, self.user)
        self.assertEqual(RESP_CONTEXT_0.group, self.group)
        self.assertEqual(
            RESP_CONTEXT_0.image.name, self.post.image
        )

    def test_context_to_create_and_edit_post(self):
        """Тест контекста для редактирования и создания поста."""
        response_edit = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}
        )
        )
        response_create = self.authorized_client.get(
            reverse('posts:post_create')
        )
        response_list = (
            response_edit, response_create
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for responses in response_list:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    self.assertIn('form', responses.context)
                    self.assertIsInstance(responses.context['form'], PostForm)
                    self.assertIsInstance(
                        responses.context['form'].fields[value], expected
                    )

    def test_post_in_group(self):
        """Тест что пост создается в нужной группе."""
        new_group = Group.objects.create(
            title='Тестовая новая группа',
            slug='test-new-slug',
            description='Тестовое новое описание'
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': new_group.slug}
        )
        )
        self.funс_post_in_context(response)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_aftorized_user_can_comment(self):
        """Тест доступности комментирования авторизированному пользователю."""

        response_form = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        )
        )
        self.assertIn('form', response_form.context)
        self.assertIsInstance(response_form.context['form'], CommentForm)

    def test_cach_in_index(self):
        """Тест кэширования начальной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Текстовый текст',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_old.content, response.content)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response_old.content, response_new.content)


class FollowViewsTests(TestCase):
    def setUp(self):
        self.follower = Client()
        self.following = Client()
        self.user_follower = User.objects.create_user(username='Follower')
        self.user_following = User.objects.create_user(username='Following')
        self.follower.force_login(self.user_follower)
        self.following.force_login(self.user_following)
        self.post = Post.objects.create(
            text='Текст подписок',
            author=self.user_following
        )

    def test_aftorized_user_can_subscribe(self):
        """Тест возможности подписаться авторизированным пользователем."""
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following).exists())
        self.follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following).exists())

    def test_aftorized_user_can_unsubscribe(self):
        """Тест возможности отписаться авторизированным пользователем."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        self.follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_following.username}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following).exists())

    def test_post_in_subscription(self):
        """Посты появляются в избранном при подписке."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.follower.get(reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertGreater(
            response.context['page_obj'].paginator.count, 0)
        self.assertIn(self.post, response.context['page_obj'])

    def test_nopost_in_nosubscription(self):
        """Постов нет в избранном у не подписаных."""
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_following,
                author=self.user_follower).exists())
        response = self.following.get(reverse('posts:follow_index'))
        self.assertIn('page_obj', response.context)
        self.assertIsInstance(response.context['page_obj'], Page)
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(username='Name')
        self.guest_client = Client()
        self.autorized_client = Client()
        self.autorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    def test_posts_in_pages(self):
        """Тест паджинатора."""
        post = []
        for i in range(PAGINATOR_TEST_POSTS):
            post.append(Post(
                text=f'Текстовый текст {i}',
                author=self.user,
                group=self.group
            )
            )
        Post.objects.bulk_create(post)
        list_url = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        post_in_page = [
            ('?page=1', NUMBER_OF_POSTS_PER_PAGE_BY_DEFAULT),
            ('?page=2',
             PAGINATOR_TEST_POSTS - NUMBER_OF_POSTS_PER_PAGE_BY_DEFAULT
             )
        ]
        for url in list_url:
            for page, meaning in post_in_page:
                with self.subTest(page=page, meaning=meaning):
                    response = self.guest_client.get(url + page)
                    self.assertIn('page_obj', response.context)
                    self.assertIsInstance(response.context['page_obj'], Page)
                    self.assertEqual(
                        len(response.context['page_obj']), meaning
                    )
