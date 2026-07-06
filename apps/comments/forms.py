from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'class': 'form-control', # Classe para CSS (ex: Bootstrap)
                'rows': 3,
                'placeholder': 'Escreve o teu comentário aqui...',
                'aria-label': 'Comentário'
            })
        }
        labels = {
            'texto': '' # Para não aparecer a palavra "Texto" em cima da caixa
        }