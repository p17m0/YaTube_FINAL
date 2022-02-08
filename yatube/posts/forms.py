from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image', )
        labels = {
            'text': ('Текст'),
            'group': ('Группа'),
            'image': ('Картинка:'),
        }
        help_texts = {
            'text': ('Внесите текст какой-нибудь текст:'),
            'group': ('Выберите группу:'),
            'image': ('Картинку выберите:'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        labels = {
            'text': ('Текст:')
        }
        help_texts = {
            'text': ('Напишите комментарий')
        }
