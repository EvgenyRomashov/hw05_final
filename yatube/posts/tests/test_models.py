from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст должен быть длиннее 15 символов',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий длинной не менее 15 символов'
        )

    def test_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = self.post
        group = self.group
        comment = self.comment
        str_list = {
            post: post.text[:15],
            group: group.title,
            comment: comment.text[:15]
        }
        for test_models, expected_values in str_list.items():
            with self.subTest(str=str):
                self.assertEqual(
                    str(test_models), expected_values
                )

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verboses_post = {
            'text': 'Текст поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = self.post
        field_help_text_post = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_text_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_follow_self(self):
        constraint_name = 'check_follow_self'
        with self.assertRaisesMessage(Exception, constraint_name):
            Follow.objects.create(user=self.user, author=self.user)
