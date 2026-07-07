"""Testes para o endpoint de autocomplete de pesquisa por relevância."""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.resources.models import Resource

User = get_user_model()


def criar_utilizador(email='teste@escola.pt', **kwargs):
    """Cria um utilizador de teste activo (bypass do email de confirmação)."""
    defaults = dict(
        nome='Teste', curso='CT', ano_letivo='12',
        instituicao='Escola Teste',
    )
    defaults.update(kwargs)
    user = User.objects.create_user(email=email, password='Senha123!', **defaults)
    User.objects.filter(pk=user.pk).update(is_active=True)
    user.refresh_from_db()
    return user


_contador_recurso = 0


def criar_recurso(utilizador, disciplina, professor=''):
    """Cria um recurso mínimo de teste com conteúdo único para evitar colisões de hash."""
    global _contador_recurso
    _contador_recurso += 1
    conteudo_unico = f'%PDF conteudo-{disciplina}-{_contador_recurso}'.encode()
    r = Resource(
        usuario=utilizador,
        nome=f'Recurso {disciplina}',
        curso=utilizador.curso,
        ano_letivo='12',
        disciplina=disciplina,
        instituicao=utilizador.instituicao,
        professor=professor,
    )
    r.arquivo = ContentFile(conteudo_unico, name=f'{disciplina}-{_contador_recurso}.pdf')
    r._skip_full_clean = True
    r.save()
    return r


class AutocompleteViewTestes(TestCase):

    def setUp(self):
        self.utilizador = criar_utilizador()
        self.client.login(username='teste@escola.pt', password='Senha123!')
        self.url = reverse('resources:autocomplete')

    def test_resposta_json_com_query_curta_vazia(self):
        """Query com menos de 2 caracteres devolve lista vazia."""
        resposta = self.client.get(self.url, {'q': 'm'})
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertEqual(dados['sugestoes'], [])

    def test_resposta_json_sem_query(self):
        """Sem parâmetro q devolve lista vazia."""
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['sugestoes'], [])

    def test_disciplinas_ordenadas_por_frequencia(self):
        """Disciplina com mais recursos aparece primeiro."""
        criar_recurso(self.utilizador, 'Matemática A')
        criar_recurso(self.utilizador, 'Matemática A')
        criar_recurso(self.utilizador, 'Matemática B')

        resposta = self.client.get(self.url, {'q': 'mat'})
        dados = resposta.json()

        self.assertIn('Matemática A', dados['sugestoes'])
        self.assertIn('Matemática B', dados['sugestoes'])
        indice_a = dados['sugestoes'].index('Matemática A')
        indice_b = dados['sugestoes'].index('Matemática B')
        self.assertLess(indice_a, indice_b)

    def test_pesquisa_insensivel_a_acentos(self):
        """'mat' encontra 'Matemática' (normalização de diacríticos)."""
        criar_recurso(self.utilizador, 'Matemática A')
        resposta = self.client.get(self.url, {'q': 'mat'})
        self.assertIn('Matemática A', resposta.json()['sugestoes'])

    def test_professores_incluidos_nas_sugestoes(self):
        """Professores também aparecem nas sugestões."""
        criar_recurso(self.utilizador, 'Física', professor='Prof. Silva')
        resposta = self.client.get(self.url, {'q': 'sil'})
        self.assertIn('Prof. Silva', resposta.json()['sugestoes'])

    def test_maximo_oito_sugestoes(self):
        """Nunca devolvem mais de 8 sugestões."""
        for i in range(15):
            criar_recurso(self.utilizador, f'Disciplina{i:02d}')
        resposta = self.client.get(self.url, {'q': 'disc'})
        self.assertLessEqual(len(resposta.json()['sugestoes']), 8)

    def test_requer_autenticacao(self):
        """Endpoint requer login."""
        self.client.logout()
        resposta = self.client.get(self.url, {'q': 'mat'})
        self.assertEqual(resposta.status_code, 302)
