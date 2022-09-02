from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from posts.models import Group, Post, User


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
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_post_create_edit_context(self):
        """Типы полей формы в словаре context соответствуют ожиданиям."""
        name_args = (
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=(self.post.id, )),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for reverse_name in name_args:
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)

    def func(self, response, boll=False):
        if boll is True:
            post = response.context.get('post')
        else:
            post = response.context.get('page_obj')[0]
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)

    def test_index_context(self):
        response = self.post_author.get(reverse('posts:index'))
        self.func(response)

    def test_group_posts_context(self):
        response = self.post_author.get(reverse(
            'posts:group_list',
            args=(self.group.slug)))
        self.func(response)
        self.assertEqual(response.context.get('group'), self.post.group)

    def test_profile_context(self):
        response = self.post_author.get(
            'posts:profile',
            args=(self.post.author))
        self.func(response)
        self.assertEqual(response.context.get('author'), self.post.author)

    def test_post_detail_context(self):
        response = self.post_author.get(reverse(
            'posts:post_detail',
            args=(self.post.id)))
        self.func(response, boll=True)

    def test_post_is_not_in_another_group(self):
        posts = Post.objects.all()
        posts.delete()
        new_post = Post.objects.create(
            author=self.author,
            text='test_text',
            group=PostViewsTests.group
        )
        new_group = Group.objects.create(
            title='Test_group',
            slug='test-slug1',
            description='test_description'
        )
        response = self.post_author.get(reverse(
            'posts:group_list',
            args=(new_group.id)))
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertIn(PostViewsTests.group, new_post)
        response = self.post_author.get(reverse(
            'posts:group_list',
            args=(PostViewsTests.group)))
        self.assertIn(new_post, response)


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
        cls.post = [
            Post(
                author=cls.author,
                text=f'Тестовый пост {page}',
                group=cls.group
            ) for page in range(settings.TEST_SORT_PAGES)
        ]
        Post.objects.bulk_create(cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_paginator(self):
        """Паджинатор работает верно"""
        name_args = (
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug, )),
            reverse('posts:profile', args=(self.author, )),
        )
        page_posts_count = (
            ('?page=1', settings.SORT_PAGES),
            ('?page=2', settings.TEST_SORT_PAGES - settings.SORT_PAGES)
        )
        for reverse_name in name_args:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                for page, posts_count in page_posts_count:
                    with self.subTest(page=page):
                        response = self.authorized_client.get(
                            reverse_name + page)
                        self.assertEqual(
                            len(response.context['page_obj']),
                            posts_count
                        )
