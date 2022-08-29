from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import forms

from posts.models import Group, Post

User = get_user_model()


class PostViewsTests(TestCase):
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

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.group = PostViewsTests.group
        self.post = PostViewsTests.post

    def test_post_views_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        names_templates = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:post_create'
            ): 'posts/post_create.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_create.html',
        }
        for reverse_name, template in names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        response = self.post_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        context = response.context.get('post')
        self.assertEqual(context, self.post)

    def test_profile_context(self):
        response = self.post_author.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        context = response.context.get('author')
        self.assertEqual(context, self.author)

    def test_group_posts_context(self):
        response = self.post_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        context = response.context.get('group')
        self.assertEqual(context, self.group)

    def test_index_context(self):
        response = self.post_author.get(reverse('posts:index'))
        context = response.context.get('post')
        self.assertEqual(context, self.post)


class PaginatorViewsTest(TestCase):
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

        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.author,
                text='Тестовый пост' + str(i),
                group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.group = PaginatorViewsTest.group
        self.post = PaginatorViewsTest.post

    def test_first_page_index_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_group_list_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_group_list_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_profile_contains_ten_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_profile_contains_three_records(self):
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
