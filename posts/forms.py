from django import forms
from .models import Post, Group, Comment
from django.db import models


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        help_texts = {
            'group': 'Выберите группу или оставьте поле пустым',
            'text': 'Введите текст',
            'image': 'Добавьте картинку',
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        help_texts = {
            'text': 'Введите текст',
        }
