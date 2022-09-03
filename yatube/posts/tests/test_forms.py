from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

REVERSE_NAME = reverse('posts:post_create')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
        }
        response = self.post_author.post(
            REVERSE_NAME,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(self.post.author,)
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])

    def test_edit_post(self):
        new_post_text = 'new text'
        new_group = Group.objects.create(
            title='New test group',
            slug='new-test-slug',
            description='new description',
        )
        form_data = {
            'text': new_post_text,
            'group': new_group.id,
        }
        response = self.post_author.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )

        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        posts_count = Post.objects.count()
        response = self.post_author.get(reverse(
            'posts:group_list', args=(PostFormTests.group.slug, )))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_title_label(self):
        title_label = PostFormTests.form.fields['text'].label
        self.assertEqual(title_label, 'Текст поста')

    def test_title_help_text(self):
        title_help_text = PostFormTests.form.fields['text'].help_text
        self.assertEqual(title_help_text, 'Текст нового поста')

    def test_not_authorized_cant_create_post(self):
        posts_count = Post.objects.count()
        response = self.client.get(REVERSE_NAME)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)
