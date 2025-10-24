# 🚀 Guia Completo de Execução - Sistema de Geolocalização

## ✅ O Que Você Precisa Para Rodar

### 1. **Chaves de API (OBRIGATÓRIO)**

#### Google Cloud Platform
1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto novo
3. Habilite as seguintes APIs:
   - **Places API (New)**
   - **Street View Static API**  
   - **Street View Metadata API**
4. Vá em "Credenciais" → "Criar credenciais" → "Chave de API"
5. Copie a chave gerada

**💰 Custos:** ~$2.50-7.00 por busca (Places + Street View)

#### OpenAI (GPT-4o)
1. Criar conta em [platform.openai.com](https://platform.openai.com/)
2. Adicionar créditos (mínimo $5)
3. Gerar API Key

**Custos estimados por execução:**
- GPT-4o: ~$0.20-0.80 (análise visual + validações)

### 2. **Arquivo .env**

Crie arquivo `.env` na pasta `geolocaliza/`:

```env
GOOGLE_API_KEY=sua_chave_google_aqui
OPENAI_API_KEY=sua_chave_openai_aqui
```

### 3. **Dependências Python**

```bash
cd geolocaliza
pip install -r requirements.txt
```

**Sobre GPU:**
- ❌ **NÃO é obrigatória**
- ✅ CPU funciona perfeitamente (mais lento)
- 🚀 GPU acelera CLIP em ~4x (0.5s vs 2s por imagem)
- Para Colab: use runtime GPU T4 (gratuito)

### 4. **Coordenadas Iniciais**

Você precisa de um ponto de partida (lat/lon). Para obter:

1. Abra [Google Maps](https://maps.google.com/)
2. Navegue até o bairro/região aproximada
3. Clique com botão direito no mapa
4. Clique em "Copiar coordenadas"
5. Formato: `-23.6505, -46.6815` (lat, lon)

### 5. **Foto do Imóvel**

**Requisitos:**
- ✅ Fachada frontal ou lateral visível
- ✅ Boa qualidade (não pixelada)
- ✅ Elementos distintivos (portão, janelas, cores)
- ✅ Imóvel com Street View recente (2024+)

---

## Modo 1: Execução Local

### Linha de Comando

```bash
python main.py \
  --foto casa.jpg \
  --cidade "São Paulo" \
  --bairro "Alto da Boa Vista" \
  --lat -23.6505 \
  --lon -46.6815 \
  --raio 2000
```

### Python Script

```python
from main import GeoLocalizador

# Inicializar
geo = GeoLocalizador()

# Executar
resultado = geo.localizar_imovel(
    foto_path="casa.jpg",
    cidade="São Paulo",
    bairro="Alto da Boa Vista",  # opcional
    center_lat=-23.6505,
    center_lon=-46.6815,
    radius_m=2000
)

# Resultado
if resultado["success"]:
    print(f"📍 {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"🗺️  {resultado['street_view_link']}")
else:
    print(f"❌ {resultado['error']}")
```

---

## Modo 2: Google Colab (RECOMENDADO)

### Passo a Passo

1. **Abra o Colab**
   - Acesse [colab.research.google.com](https://colab.research.google.com/)
   - Crie um novo notebook

2. **Configure GPU (opcional, mas recomendado)**
   - Menu: Runtime → Change runtime type
   - Hardware accelerator: **GPU (T4)**
   - Salvar

3. **Clone/Upload o Projeto**

```python
# Opção A: Clone do repositório
!git clone https://github.com/seu-usuario/geolocalizacao.git
%cd geolocalizacao/geolocaliza

# Opção B: Upload manual
from google.colab import files
uploaded = files.upload()  # Faça upload dos arquivos .py
```

4. **Instale Dependências**

```python
!pip install -q anthropic google-maps-services requests pillow numpy
!pip install -q opencv-python-headless torch open-clip-torch pandas
!pip install -q folium tqdm python-dotenv
```

5. **Configure APIs**

```python
import os
from getpass import getpass

os.environ["GOOGLE_API_KEY"] = getpass("Google API Key: ")
os.environ["OPENAI_API_KEY"] = getpass("OpenAI API Key: ")
```

6. **Upload da Foto**

```python
from google.colab import files
from PIL import Image

uploaded = files.upload()
foto_path = list(uploaded.keys())[0]

# Visualizar
img = Image.open(foto_path)
img.thumbnail((600, 600))
display(img)
```

7. **Configure Busca**

```python
cidade = "São Paulo"
bairro = "Alto da Boa Vista"
center_lat = -23.6505
center_lon = -46.6815
radius_m = 2000
```

8. **Execute**

```python
import sys
sys.path.insert(0, '/content/geolocalizacao/geolocaliza')

from main import GeoLocalizador

geo = GeoLocalizador()

resultado = geo.localizar_imovel(
    foto_path=foto_path,
    cidade=cidade,
    bairro=bairro,
    center_lat=center_lat,
    center_lon=center_lon,
    radius_m=radius_m
)
```

9. **Visualize Resultados**

```python
if resultado["success"]:
    print(f"📍 Endereço: {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"🗺️  Street View: {resultado['street_view_link']}")
    
    # Ver mapa interativo
    from IPython.display import IFrame
    display(IFrame('/content/geolocalizacao/geolocaliza/output/mapa.html', 
                   width=800, height=600))
else:
    print(f"❌ Erro: {resultado['error']}")
```

---

## Outputs Gerados

Após execução, você encontrará em `output/`:

- **`resultado_final.json`** - Endereço completo + confiança
- **`analise_visual.json`** - Análise detalhada da foto (Claude)
- **`candidatos.csv`** - Todos os matches encontrados
- **`candidatos_validados.csv`** - Top candidatos validados pelo LLM
- **`mapa.html`** - Mapa interativo (Folium)
- **`street_views/`** - Imagens baixadas do Street View
- **`geolocaliza.log`** - Log completo da execução

---

## Configurações Avançadas

Edite `config.py` para ajustar:

### Busca
```python
SEARCH_CONFIG = {
    "initial_radius_m": 2000,      # Raio inicial (metros)
    "grid_spacing_m": 50,          # Espaçamento da grade
    "sv_min_year": 2024,           # Ano mínimo do Street View
    "max_sv_downloads": 500,       # Limite de downloads
}
```

### Machine Learning
```python
ML_CONFIG = {
    "clip_threshold": 0.70,        # Threshold CLIP (0-1)
    "min_confidence": 0.85,        # Confiança mínima final
    "clip_weight": 0.5,            # Peso do CLIP
    "geom_weight": 0.3,            # Peso da geometria
    "context_weight": 0.2,         # Peso do contexto LLM
}
```

---

## Troubleshooting

### "Nenhum candidato encontrado"
**Causas:**
- Coordenadas incorretas
- Raio muito pequeno
- Área sem Street View

**Soluções:**
- Verifique coordenadas no Google Maps
- Aumente `radius_m` para 3000-5000
- Confirme que há Street View na área

### "Confiança baixa (< 0.85)"
**Causas:**
- Foto de baixa qualidade
- Ângulo ruim
- Imóvel muito genérico
- Street View desatualizado

**Soluções:**
- Tire foto de outro ângulo (mais elementos visíveis)
- Use foto com melhor resolução
- Reduza `min_confidence` em `config.py` para 0.75

### "Quota exceeded" (Google)
**Causas:**
- Limite de requisições atingido
- Billing não configurado

**Soluções:**
- Verifique billing no Google Cloud Console
- Adicione `time.sleep(0.5)` em `search_agent.py` (linha 319)
- Aguarde reset da quota (diário)

### "API Error" (OpenAI)
**Causas:**
- Chave inválida
- Créditos esgotados
- Rate limit

**Soluções:**
- Verifique chave em platform.openai.com
- Adicione créditos
- Aguarde 1 minuto entre execuções

### "CUDA out of memory"
**Causas:**
- GPU com pouca VRAM
- Modelo CLIP muito grande

**Soluções:**
- Use CPU: mude `device = "cpu"` em `matching_agent.py`
- Ou reduza batch size (processar menos imagens por vez)

---

## ⏱️ Tempo de Execução

**Pipeline completo:** 2-5 minutos

Breakdown:
1. Análise visual (Claude): ~10s
2. Busca Places API: ~20-30s
3. Verificação Street View: ~30-60s
4. Download Street Views: ~1-2min (200-500 imagens)
5. Matching CLIP+SIFT: ~1-2min (GPU) ou ~3-5min (CPU)
6. Validação LLM: ~20-40s (top 5 candidatos)

**Fatores que afetam:**
- Raio de busca (maior = mais candidatos = mais tempo)
- GPU vs CPU (4x mais rápido com GPU)
- Velocidade da internet (downloads SV)
- Densidade da área (mais condomínios = mais candidatos)

---

## 💡 Dicas Para Melhores Resultados

1. **Foto ideal:**
   - Fachada frontal em dia claro
   - Sem obstruções (carros, árvores cobrindo)
   - Elementos únicos visíveis (cores, portão, janelas)

2. **Área de busca:**
   - Comece com raio pequeno (1-2km) se souber a região
   - Aumente gradualmente se não encontrar
   - Bairro ajuda muito a refinar

3. **Interpretação dos scores:**
   - **CLIP > 0.80:** Arquitetura muito similar
   - **GEOM > 0.60:** Geometria bate bem
   - **LLM > 0.85:** Alta confiança contextual
   - **Final > 0.90:** Praticamente certeza

4. **Se confiança < 0.85:**
   - Analise os top 3 candidatos manualmente
   - Verifique links do Street View
   - Compare elementos distintivos
   - Pode ser match mesmo com score mais baixo

---

## 📚 Documentação Adicional

- **README.md** - Visão geral do sistema
- **ARQUITETURA.md** - Detalhes técnicos da arquitetura
- **FAQ.md** - Perguntas frequentes
- **RESUMO_PROJETO.md** - Resumo executivo

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique logs em `output/geolocaliza.log`
2. Teste agentes individualmente (ver seção abaixo)
3. Abra issue no repositório com:
   - Logs completos
   - Configuração usada
   - Descrição do erro

### Testar Agentes Individualmente

```python
# Teste VisionAgent
from agents.vision_agent import VisionAgent
vision = VisionAgent()
result = vision.analyze_image("foto.jpg")
print(result)

# Teste SearchAgent
from agents.search_agent import SearchAgent
search = SearchAgent()
candidates = search.search_area(-23.6505, -46.6815, 1000, "São Paulo")
print(f"Encontrados: {len(candidates)} candidatos")

# Teste MatchingAgent
from agents.matching_agent import MatchingAgent
matching = MatchingAgent()
# ... (requer imagens SV já baixadas)
```

---

**Desenvolvido com ❤️ usando Claude + OpenCLIP + Google APIs**
