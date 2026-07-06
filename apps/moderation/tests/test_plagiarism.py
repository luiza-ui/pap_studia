from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from apps.resources.models import Resource

User = get_user_model()

def _utilizador(email='plag@escola.pt'):
    u = User.objects.create_user(email=email, password='Teste1234!', nome='Plag', curso='CT', ano_letivo='12', instituicao='Escola Teste')
    User.objects.filter(pk=u.pk).update(is_active=True)
    u.refresh_from_db()
    return u

def _recurso_img(utilizador, nome='img.png'):
    conteudo_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    r = Resource(usuario=utilizador, nome='IMG Teste', curso=utilizador.curso, ano_letivo='12', disciplina='Teste', instituicao=utilizador.instituicao)
    r.arquivo = ContentFile(conteudo_png, name=nome)
    r._skip_full_clean = True
    r.save()
    return r

class VerificarPlagioTestes(TestCase):
    def setUp(self):
        self.utilizador = _utilizador()

    def test_primeiro_recurso_nao_e_plagio(self):
        from apps.moderation.services.plagiarism import verificar_plagio
        recurso = _recurso_img(self.utilizador)
        self.assertFalse(verificar_plagio(recurso))

    def test_funcao_devolve_bool(self):
        from apps.moderation.services.plagiarism import verificar_plagio
        recurso = _recurso_img(self.utilizador, nome='img2.png')
        self.assertIsInstance(verificar_plagio(recurso), bool)
