import shutil
import tempfile

from django.contrib.auth import get_user_model
from posts.models import Group, Post
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Name')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.autorized_client = Client()
        self.autorized_client.force_login(PostCreateFormTest.user)

    def test_create_post(self):
        """Валидная форма создаёт новый пост."""
        post_count = Post.objects.count()
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
        form_data = {
            'text': 'Текстовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        self.autorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.last()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_edit_post(self):
        """
        Валидная форма меняет пост при редактировании.
        ID поста не меняется.
        """
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
        post = Post.objects.create(
            text='Текстовый текст',
            author=self.user,
            group=self.group,
            image=uploaded
        )
        new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='new-test-slug',
            description='Новое текстовое описание'
        )
        form_data = {
            'text': 'Новый  текстовый текст',
            'group': new_group.id
        }
        self.autorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        post_for_edit = Post.objects.last()
        self.assertEqual(post_for_edit.text, form_data['text'])
        self.assertNotEqual(post.text, post_for_edit.text)
        self.assertEqual(post_for_edit.group.id, form_data['group'])

    def test_comment_publishing(self):
        """Тест добавления комментария"""
        post = Post.objects.create(
            text='Текстовый текст',
            author=self.user,
            group=self.group
        )
        form_data = {'text': 'Тестовый коммент'}
        self.autorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        response = self.autorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': post.pk}
        )
        )
        self.assertContains(response, 'Тестовый коммент')
