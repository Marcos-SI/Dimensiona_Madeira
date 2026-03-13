from django.db import models


from django.db import models


class Madeira(models.Model):
    nome = models.CharField('Nome da Espécie (ex: Pinus Taeda)', max_length=100, unique=True)
    f_c0k = models.FloatField('Compressão Paralela (fc0,k) [MPa]')
    f_t0k = models.FloatField('Tração Paralela (ftn,k) [MPa]')
    f_v0k = models.FloatField('Cisalhamento (fv0,k) [MPa]')
    f_fe = models.FloatField('Embutimento (fe)')
    f_c90k = models.FloatField('Compressão Normal (fcn,k) [MPa]') 
    e_c0m = models.FloatField('Módulo de Elasticidade (Ecn0,m) [MPa]')
    f_fd = models.FloatField('Flexão')
    # densidade_aparente = models.FloatField('Densidade (ρap) [kg/m³]')

    class Meta:
        verbose_name = 'Madeira'
        verbose_name_plural = 'Madeiras'

    def __str__(self):
        return self.nome

class Projeto(models.Model):
    CARREGAMENTO_CHOICES = [
        ('permanente', 'Permanente'),
        ('longa', 'Longa Duração'),
        ('media', 'Média Duração'),
        ('curta', 'Curta Duração'),
        ('instantanea', 'Instantânea'),
    ]
    
    UMIDADE_CHOICES = [
        (1, 'Classe 1 (≤ 12%)'),
        (2, 'Classe 2 (15%)'),
        (3, 'Classe 3 (18%)'),
        (4, 'Classe 4 (≥ 21%)'),
    ]

    nome = models.CharField('Nome do Projeto ou Exercício', max_length=200)
    classe_carregamento = models.CharField(max_length=20, choices=CARREGAMENTO_CHOICES)
    classe_umidade = models.IntegerField(choices=UMIDADE_CHOICES)
    categoria_madeira = models.IntegerField('Categoria da Madeira (1, 2 ou 3)', default=2)

    class Meta:
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def __str__(self):
        return self.nome


class PecaDimensionada(models.Model):
    TIPO_ESFORCO = [
        ('tracao', 'Tração Paralela'),
        ('compressao', 'Compressão Paralela'),
    ]

    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='pecas')
    madeira = models.ForeignKey(Madeira, on_delete=models.PROTECT)

    identificacao = models.CharField('Nome da Peça (ex: Viga V1)', max_length=100)
    tipo_esforco = models.CharField(max_length=20, choices=TIPO_ESFORCO)
    base_b = models.FloatField('Base da Seção b [cm]')
    altura_h = models.FloatField('Altura da Seção h [cm]')
    comprimento_flambagem = models.FloatField('Comprimento de Flambagem L0 [cm] (Apenas Compressão)', blank=True, null=True)
    forca_solicitante_nd = models.FloatField('Força Atuante Nd [kN]')

    def __str__(self):
        return f"{self.identificacao} - {self.get_tipo_esforco_display()}"

class Ligacao(models.Model):
    TIPO_LIGACAO = [
        ('pino', 'Pino Metálico/Prego/Parafuso'),
        ('entalhe', 'Entalhe (Cisalhamento)'),
    ]
    largura_entalhe_be = models.FloatField('Largura do Entalhe be [cm] (Apenas Entalhe)', blank=True, null=True)
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='ligacoes')
    madeira = models.ForeignKey(Madeira, on_delete=models.PROTECT)

    identificacao = models.CharField('Nome da Ligação (ex: Nó da Treliça)', max_length=100)
    tipo_ligacao = models.CharField(max_length=20, choices=TIPO_LIGACAO)
    

    forca_cortante_vd = models.FloatField('Força Cortante Vd [kN]')
    diametro_pino = models.FloatField('Diâmetro do Pino d [cm] (Se aplicável)', blank=True, null=True)
    espessura_t1 = models.FloatField('Espessura t1 [cm] (Se aplicável)', blank=True, null=True)
    comprimento_corte_entalhe = models.FloatField('Comprimento de Corte [cm] (Apenas Entalhe)', blank=True, null=True)

    def __str__(self):
        return f"{self.identificacao} - {self.get_tipo_ligacao_display()}"