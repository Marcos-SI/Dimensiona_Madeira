from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Madeira, Projeto, PecaDimensionada, Ligacao
from .serializers import (
    MadeiraSerializer,
    ProjetoSerializer,
    PecaDimensionadaSerializer,
    LigacaoSerializer,
)
import math

class MadeiraViewSet(viewsets.ModelViewSet):
    """API endpoint para visualizar e editar as espécies de madeira."""
    queryset = Madeira.objects.all()
    serializer_class = MadeiraSerializer

class ProjetoViewSet(viewsets.ModelViewSet):
    """Endpoint para os Projetos (Configurações de cálculo)."""
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer

class PecaDimensionadaViewSet(viewsets.ModelViewSet):
    """Endpoint para as peças tracionadas e comprimidas com lógica de cálculo NBR 7190."""
    queryset = PecaDimensionada.objects.all()
    serializer_class = PecaDimensionadaSerializer

    @action(detail=False, methods=['post'])
    def calcular(self, request):
        data = request.data
        
        try:
            
            madeira = Madeira.objects.get(id=data['madeira'])
            projeto = Projeto.objects.get(id=data['projeto'])
            
            nd = float(data['forca_solicitante_nd'])
            base = float(data['base_b'])
            altura = float(data['altura_h'])
            tipo_esforco = data['tipo_esforco']

            
            tabela_kmod1 = {
                'permanente': 0.60, 'longa': 0.70, 'media': 0.80, 
                'curta': 0.90, 'instantanea': 1.10
            }
            kmod1 = tabela_kmod1.get(projeto.classe_carregamento, 0.70)
            
            
            kmod2 = 1.0 if projeto.classe_umidade <= 2 else 0.8
            
            
            if 'pinus' in madeira.nome.lower() or 'pinho' in madeira.nome.lower():
                kmod3 = 0.8
            else:
                kmod3 = 1.0 if projeto.categoria_madeira == 1 else 0.8

            kmod_total = kmod1 * kmod2 * kmod3

            
            if tipo_esforco == 'compressao':
                fk = madeira.f_c0k
                gama_w = 1.4
            else:
                fk = madeira.f_t0k
                gama_w = 1.8

            fd = kmod_total * (fk / gama_w)
            
            
            area = base * altura
            sigma_d = (nd / area) * 10
            
            status = "APROVADO" if sigma_d <= fd else "REPROVADO"

            
            # peca = PecaDimensionada.objects.create(
            #     projeto=projeto,
            #     madeira=madeira,
            #     identificacao=data.get('identificacao', 'Peça Avulsa'),
            #     tipo_esforco=tipo_esforco,
            #     base_b=base,
            #     altura_h=altura,
            #     forca_solicitante_nd=nd
            # )

            return Response({
                'status': status,
                'fd': round(fd, 2),
                'sigma_d': round(sigma_d, 2),
                'kmod': round(kmod_total, 2),
                #'peca_id': peca.id
            })

        except Exception as e:
            print("Erro no cálculo:", e)
            return Response({'error': str(e)}, status=400)

class LigacaoViewSet(viewsets.ModelViewSet):
    """Endpoint para as ligações (pinos e entalhes)."""
    queryset = Ligacao.objects.all()
    serializer_class = LigacaoSerializer

    def _get_kmod(self, projeto, madeira):
        tabela_kmod1 = {
            'permanente': 0.60, 'longa': 0.70, 'media': 0.80,
            'curta': 0.90, 'instantanea': 1.10
        }
        kmod1 = tabela_kmod1.get(projeto.classe_carregamento, 0.70)
        kmod2 = 1.0 if projeto.classe_umidade <= 2 else 0.8
        if 'pinus' in madeira.nome.lower() or 'pinho' in madeira.nome.lower():
            kmod3 = 0.8
        else:
            kmod3 = 1.0 if projeto.categoria_madeira == 1 else 0.8
        return kmod1 * kmod2 * kmod3

    @action(detail=False, methods=['post'], url_path='verificar-pino')
    def verificar_pino(self, request):
        """
        Verificação de ligações com pino metálico (corte simples).
        Assume ligação simétrica com duas peças de mesma espessura t1.
        """
        data = request.data
        try:
            madeira = Madeira.objects.get(id=data['madeira'])
            projeto = Projeto.objects.get(id=data['projeto'])
            
            vd = float(data['forca_cortante_vd'])
            d = float(data['diametro_pino'])
            t1 = float(data['espessura_t1'])
            
            kmod = self._get_kmod(projeto, madeira)
            
            
            fe0k = 0.82 * (madeira.densidade_aparente ** 0.85) * (d ** -0.3)
            fe0d = kmod * fe0k / 1.4 


            rvd = fe0d * t1 * d
            
            status = "APROVADO" if rvd >= vd else "REPROVADO"

            Ligacao.objects.create(
                projeto=projeto, madeira=madeira,
                identificacao=data.get('identificacao', 'Ligação Pino'),
                tipo_ligacao='pino', forca_cortante_vd=vd,
                diametro_pino=d, espessura_t1=t1
            )

            return Response({
                'status': status,
                'resistencia_calculo_rd_kn': round(rvd, 2),
                'forca_solicitante_vd_kn': round(vd, 2),
                'resistencia_embutimento_fed_mpa': round(fe0d, 2),
                'kmod': round(kmod, 2)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='verificar-entalhe')
    def verificar_entalhe(self, request):
        """
        Verificação de ligações por entalhe (cisalhamento).
        """
        data = request.data
        try:
            madeira = Madeira.objects.get(id=data['madeira'])
            projeto = Projeto.objects.get(id=data['projeto'])

            vd = float(data['forca_cortante_vd'])
            lc = float(data['comprimento_corte_entalhe'])
            be = float(data['largura_entalhe_be']) 

            kmod = self._get_kmod(projeto, madeira)

            
            fvk = madeira.f_v0k
            fvd = kmod * fvk / 1.8 

            
            area_cisalhamento = lc * be
            tau_vd = (vd / area_cisalhamento) * 10 

            status = "APROVADO" if fvd >= tau_vd else "REPROVADO"

            Ligacao.objects.create(
                projeto=projeto, madeira=madeira,
                identificacao=data.get('identificacao', 'Ligação Entalhe'),
                tipo_ligacao='entalhe', forca_cortante_vd=vd,
                comprimento_corte_entalhe=lc,
                largura_entalhe_be=be

            )

            return Response({
                'status': status,
                'resistencia_cisalhamento_fvd_mpa': round(fvd, 2),
                'tensao_solicitante_tau_vd_mpa': round(tau_vd, 2),
                'kmod': round(kmod, 2)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)


def page_catalogo(request):
    return render(request, 'dimensionamento/pages/catalogo.html')

def page_home(request):
    return render(request, 'dimensionamento/pages/home.html')

def page_calculadora(request):
    return render(request, 'dimensionamento/pages/calculadora.html')

def page_projeto(request):
    return render(request, 'dimensionamento/pages/projeto.html')