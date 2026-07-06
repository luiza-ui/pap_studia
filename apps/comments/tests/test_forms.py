from django.test import TestCase
from apps.comments.forms import CommentForm

class CommentFormTests(TestCase):
    """Testes para o segurança à porta (Formulário) dos Comentários."""

    def test_form_valido(self):
        """Testa se o formulário aceita um comentário bem preenchido."""
        dados = {'texto': 'Este recurso ajudou-me imenso no meu projeto final!'}
        form = CommentForm(data=dados)
        
        self.assertTrue(form.is_valid())

    def test_form_invalido_texto_vazio(self):
        """Testa se o formulário bloqueia tentativas de enviar comentários em branco."""
        dados = {'texto': ''}
        form = CommentForm(data=dados)
        
        # O form NÃO pode ser válido
        self.assertFalse(form.is_valid())
        # Tem de existir um erro associado ao campo 'texto'
        self.assertIn('texto', form.errors)

    def test_form_widgets_e_estilos(self):
        """Verifica se os atributos visuais (Bootstrap, Placeholder) estão corretos."""
        form = CommentForm()
        widget_texto = form.fields['texto'].widget
        
        # Confirma que o CSS e o HTML não foram apagados acidentalmente
        self.assertEqual(widget_texto.attrs.get('class'), 'form-control')
        self.assertEqual(widget_texto.attrs.get('rows'), 3)
        self.assertEqual(widget_texto.attrs.get('placeholder'), 'Escreve o teu comentário aqui...')
        self.assertEqual(widget_texto.attrs.get('aria-label'), 'Comentário')
        
    def test_form_label_vazia(self):
        """Garante que a label do campo texto está mesmo vazia para manter o design limpo."""
        form = CommentForm()
        self.assertEqual(form.fields['texto'].label, '')