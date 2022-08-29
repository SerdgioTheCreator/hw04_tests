import shutil
import tempfile

from posts.forms import PostForm
from posts.models import Group, Post

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.group = PostFormTests.group
        self.post = PostFormTests.post

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        response = self.post_author.post(
            reverse('posts:post_create'),
            data={'text': 'Тестовый пост', 'group': self.group.id},
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.post.author}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост',
                group=self.group.id
            ).exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='text',
            group=self.group
        )

        new_post_text = 'new text'
        new_group = Group.objects.create(
            title='New test group',
            slug='new-test-slug',
            description='new description',
        )

        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data={'text': new_post_text, 'group': new_group.id},
            follow=True,
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, new_post_text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, new_group)

    def test_title_label(self):
        title_label = PostFormTests.form.fields['text'].label
        self.assertEqual(title_label, 'Текст поста')

    def test_title_help_text(self):
        title_help_text = PostFormTests.form.fields['text'].help_text
        self.assertEqual(title_help_text, 'Текст нового поста')
