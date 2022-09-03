from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
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
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.hardcode_url_names = (
            ('posts:index', None, '/', ),
            ('posts:post_create', None, '/create/', ),
            ('posts:group_list',
             (self.group.slug, ),
             f'/group/{self.group.slug}/', ),
            ('posts:profile',
             (self.post.author, ),
             f'/profile/{self.post.author}/', ),
            ('posts:post_detail',
             (self.post.id, ),
             f'/posts/{self.post.id}/', ),
            ('posts:post_edit',
             (self.post.id, ),
             f'/posts/{self.post.id}/edit/', ),
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (reverse(
                'posts:index'
            ), 'posts/index.html'),
            (reverse(
                'posts:post_create'
            ), 'posts/post_create.html'),
            (reverse(
                'posts:group_list',
                args=(self.group.slug, )
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile',
                args=(self.post.author, )
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail',
                args=(self.post.id, )
            ), 'posts/post_detail.html'),
            (reverse(
                'posts:post_edit',
                args=(self.post.id, )
            ), 'posts/post_create.html'),
        )
        for reverse_name, template in templates_url_names:
            with self.subTest(reverse_name=reverse_name):
                if self.user == self.post.author:
                    response = self.post_author.get(reverse_name)
                    self.assertTemplateUsed(response, template)

    def test_reverse_name_urls(self):
        """Тест реверсов"""
        for name, args, url in self.hardcode_url_names:
            with self.subTest(name=name):
                self.assertEqual(reverse(name, args=args), url)

    def test_post_author_get_404(self):
        """Автор получит 404 на всех страницах"""
        for name, args, url in self.hardcode_url_names:
            with self.subTest(name=name):
                if self.user == self.post.author:
                    response = self.post_author.get(reverse(name, args=args))
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_client_get_302(self):
        """Авторизованный пользователь не может редачить пост"""
        for name, args, url in self.hardcode_url_names:
            with self.subTest(name=name):
                if name == 'posts:post_edit':
                    response = self.authorized_user.get(reverse(
                        'posts:post_edit',
                        args=(self.post.id, ),
                    ), follow=True)
                    self.assertRedirects(
                        response, (reverse(
                            'posts:post_detail',
                            args=(self.post.id, ))))
                else:
                    response = self.authorized_user.get(reverse(
                        name,
                        args=args), follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_client_cant_create_edit_post(self):
        """Гость не может создавать и редачить пост"""
        for name, args, url in self.hardcode_url_names:
            with self.subTest(name=name):
                login = reverse('users:login')
                reverse_name = reverse(name, args=args)
                if name in (
                    'posts:post_create',
                    'posts:post_edit',
                ):
                    response = self.client.get(reverse(
                        name,
                        args=args,
                    ), follow=True)
                    self.assertRedirects(
                        response, f'{login}?next={reverse_name}')
                else:
                    response = self.authorized_user.get(reverse(
                        name,
                        args=args), follow=True)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Несуществующая страница возвращает ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
