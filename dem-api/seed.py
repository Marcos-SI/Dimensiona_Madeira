# dem-api/seed.py

import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dem_api.settings')
django.setup()

# Importa o modelo após a configuração
from dimensionamento.models import Madeira

# Dados baseados na NBR 7190 para as classes de resistência C25 e D60.
MADEIRAS_PARA_CADASTRAR = [
    {
        'nome': 'Pinus Taeda (C25)',
        'f_c0k': 14.21,
        'f_t0k': 14.35,
        'f_v0k': 1.92,
        'f_c90k': 3.55,
        'e_c0m': 5960,
        'f_fd': 14.35,  # Novo campo: Resistência à Flexão
        'f_fe': 14.21,  # Novo campo: Resistência ao Embutimento
    },
    {
        'nome': 'Jatobá (D60)',
        'f_c0k': 29.86,
        'f_t0k': 24.09,
        'f_v0k': 3.91,
        'f_c90k': 23.33,
        'e_c0m': 10575.94,
        'f_fd': 24.09,  # Novo campo: Resistência à Flexão
        'f_fe': 29.86,  # Novo campo: Resistência ao Embutimento
    },
]

def run():
    """
    Função principal para popular o banco de dados.
    """
    print("Iniciando o povoamento do banco de dados com espécies de madeira...")

    for dados_madeira in MADEIRAS_PARA_CADASTRAR:
        # Usa update_or_create para evitar duplicatas se o script for rodado novamente.
        obj, created = Madeira.objects.update_or_create(
            nome=dados_madeira['nome'],
            defaults=dados_madeira
        )
        
        if created:
            print(f"- Madeira '{obj.nome}' criada com sucesso.")
        else:
            print(f"- Madeira '{obj.nome}' já existia e foi atualizada com os novos campos.")

    print("Povoamento concluído!")

# Permite que o script seja executado diretamente
if __name__ == '__main__':
    run()