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
            
            # --- INÍCIO DA MODIFICAÇÃO ---
            # 1. Majoração da Carga: O sistema agora espera a força característica (nk)
            # e a multiplica pelo coeficiente de majoração (gamma_f) para obter a força de cálculo (nd).
            nk = float(data['forca_solicitante_nk'])
            gamma_f = 1.4 
            nd = nk * gamma_f
            # --- FIM DA MODIFICAÇÃO ---

            base = float(data['base_b'])
            altura = float(data['altura_h'])
            tipo_esforco = data['tipo_esforco']

            tabela_kmod1 = {
                'permanente': 0.60, 'longa': 0.70, 'media': 0.80, 
                'curta': 0.90, 'instantanea': 1.10
            }
            kmod1 = tabela_kmod1.get(projeto.classe_carregamento, 0.70)
            kmod2 = 1.0 if projeto.classe_umidade <= 2 else 0.8
            kmod3 = 1.0 if projeto.categoria_madeira == 1 else 0.8
            kmod_total = kmod1 * kmod2 * kmod3

            if tipo_esforco == 'compressao':
                fk = madeira.f_c0k
                gama_w = 1.4
            elif tipo_esforco == 'tracao':
                fk = madeira.f_t0k
                gama_w = 1.8
            elif tipo_esforco == 'cisalhamento':
                fk = madeira.f_v0k
                gama_w = 1.8
            elif tipo_esforco == 'flexao':
                fk = madeira.f_fd
                gama_w = 1.4
            else:
                return Response({'error': f'Tipo de esforço desconhecido: {tipo_esforco}'}, status=400)

            fd = (kmod_total * fk) / gama_w
            
            area = base * altura
            sigma_d_mpa = (nd / area) * 10
            
            status = "APROVADO" if sigma_d_mpa <= fd else "REPROVADO"

            return Response({
                'status': status,
                'fd': round(fd, 2),
                'sigma_d': round(sigma_d_mpa, 2),
                'kmod': round(kmod_total, 2),
                'forca_calculo_nd_kn': round(nd, 2), # Retorna a força já majorada
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)

class LigacaoViewSet(viewsets.ModelViewSet):
    """Endpoint para as ligações (pinos e entalhes)."""
    queryset = Ligacao.objects.all()
    serializer_class = LigacaoSerializer

    def _get_kmod(self, projeto):
        tabela_kmod1 = {
            'permanente': 0.60, 'longa': 0.70, 'media': 0.80,
            'curta': 0.90, 'instantanea': 1.10
        }
        kmod1 = tabela_kmod1.get(projeto.classe_carregamento, 0.70)
        kmod2 = 1.0 if projeto.classe_umidade <= 2 else 0.8
        kmod3 = 1.0 if projeto.categoria_madeira == 1 else 0.8
        return kmod1 * kmod2 * kmod3

    @action(detail=False, methods=['post'], url_path='verificar-pino')
    def verificar_pino(self, request):
        """Verificação de ligações com pino metálico (corte simples)."""
        data = request.data
        try:
            madeira = Madeira.objects.get(id=data['madeira'])
            projeto = Projeto.objects.get(id=data['projeto'])
            
            vd = float(data['forca_cortante_vd'])
            d = float(data['diametro_pino'])
            t1 = float(data['espessura_t1'])
            
            kmod = self._get_kmod(projeto)
            
            fe0k = madeira.f_fe 
            gama_w_lig = 1.4
            fe0d = (kmod * fe0k) / gama_w_lig

            rvd = fe0d * t1 * d
            
            status = "APROVADO" if rvd >= vd else "REPROVADO"

            return Response({
                'status': status,
                'resistencia_rd_kn': round(rvd / 10, 2),
                'forca_solicitante_vd_kn': round(vd, 2),
                'resistencia_embutimento_fed_mpa': round(fe0d, 2),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=False, methods=['post'], url_path='verificar-entalhe')
    def verificar_entalhe(self, request):
        """Verificação de ligações por entalhe (cisalhamento)."""
        data = request.data
        try:
            madeira = Madeira.objects.get(id=data['madeira'])
            projeto = Projeto.objects.get(id=data['projeto'])

            vd = float(data['forca_cortante_vd'])
            lc = float(data['comprimento_corte_entalhe'])
            be = float(data['largura_entalhe_be']) 

            kmod = self._get_kmod(projeto)
            
            fvk = madeira.f_v0k
            gama_w_lig = 1.8
            fvd = (kmod * fvk) / gama_w_lig

            area_cisalhamento = lc * be
            tau_vd_mpa = (vd / area_cisalhamento) * 10

            status = "APROVADO" if fvd >= tau_vd_mpa else "REPROVADO"

            return Response({
                'status': status,
                'resistencia_cisalhamento_fvd_mpa': round(fvd, 2),
                'tensao_solicitante_tau_vd_mpa': round(tau_vd_mpa, 2),
            })

        except Exception as e:
            return Response({'error': str(e)}, status=400)


# Funções de renderização de página (permanecem iguais)
def page_catalogo(request):
    return render(request, 'dimensionamento/pages/catalogo.html')

def page_home(request):
    return render(request, 'dimensionamento/pages/home.html')

def page_calculadora(request):
    return render(request, 'dimensionamento/pages/calculadora.html')

def page_projeto(request):
    return render(request, 'dimensionamento/pages/projeto.html')