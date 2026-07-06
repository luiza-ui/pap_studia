# Studia — Inicialização do Projeto

## Comandos

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_bd
python manage.py runserver
```

## Utilizadores criados pelo popular_bd

| Email | Password | Perfil |
|---|---|---|
| admin@escola.pt | admin123 | Superutilizador (acesso a /admin/) |
| ana@escola.pt | teste123 | TGPSI 12º — tem uploads e recursos |
| joao@escola.pt | teste123 | CT 11º — tem comentários e favoritos |
| maria@escola.pt | teste123 | LH 10º — escola diferente |
| semcreditos@escola.pt | teste123 | Sem créditos para download |
| bloqueado@escola.pt | teste123 | Conta bloqueada (não consegue fazer login) |
| denunciante@escola.pt | teste123 | 3 reports falsos registados |

## O que é criado

- 7 recursos (PDF, DOCX, PPTX, IMG)
- 5 comentários
- 5 favoritos
- 5 denúncias (3 pendentes, 1 aceite, 1 rejeitada) com todos os motivos

## Notas sobre migrações

| Migração | O que faz |
|---|---|
| `resources/0005` | Preenche campos normalizados (corrige autocomplete) |
| `resources/0006` | Remove campo `link` |
| `reports/0004` | Adiciona `motivo_tipo` às denúncias |
| `accounts/0003` | Converte `curso` para lista de choices oficial |
