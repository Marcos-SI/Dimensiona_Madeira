from rest_framework import serializers
from .models import Madeira, Projeto, PecaDimensionada, Ligacao

class MadeiraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Madeira
        fields = '__all__' 

class PecaDimensionadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PecaDimensionada
        fields = '__all__'

class LigacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ligacao
        fields = '__all__'

class ProjetoSerializer(serializers.ModelSerializer):
   
    pecas = PecaDimensionadaSerializer(many=True, read_only=True)
    ligacoes = LigacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Projeto
        fields = ['id', 'nome', 'classe_carregamento', 'classe_umidade', 'categoria_madeira', 'pecas', 'ligacoes']