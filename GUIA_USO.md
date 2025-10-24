# 🚀 Guia de Uso - Sistema de Geolocalização

## 📋 Pré-requisitos

### 1. Instalar Dependências

```bash
cd /usr/local/anaconda3/Agentes_youtube/langgraph_system/LANGGRAPH_MCP/geolocaliza
pip install -r requirements.txt
```

### 2. Configurar APIs

Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Edite `.env` e adicione suas chaves:
```env
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Habilitar APIs no Google Cloud

Acesse [Google Cloud Console](https://console.cloud.google.com) e habilite:
- ✅ Places API (New)
- ✅ Street View Static API
- ✅ Street View Metadata API

---

## 🎯 Uso Básico

### Modo 1: Python Script

```python
from main import GeoLocalizador

# Inicializar
geo = GeoLocalizador()

# Localizar imóvel
resultado = geo.localizar_imovel(
    foto_path="minha_casa.jpg",
    cidade="São Paulo",
    bairro="Alto da Boa Vista",  # opcional
    center_lat=-23.6505,         # opcional
    center_lon=-46.6815,         # opcional
    radius_m=2000                # opcional
)

# Resultado
if resultado["success"]:
    print(f"📍 {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
else:
    print(f"❌ {resultado['error']}")
```

### Modo 2: Linha de Comando

```bash
python main.py \
  --foto minha_casa.jpg \
  --cidade "São Paulo" \
  --bairro "Alto da Boa Vista" \
  --lat -23.6505 \
  --lon -46.6815 \
  --raio 2000
```

### Modo 3: Teste Rápido

```bash
# Copie sua foto para test_image.jpg
cp /caminho/foto.jpg test_image.jpg

# Execute o teste
python test_sistema.py
```

---

## 📊 Outputs Gerados

Todos os arquivos são salvos em `output/`:

| Arquivo | Descrição |
|---------|-----------|
| `analise_visual.json` | Análise detalhada da foto (arquitetura, contexto) |
| `sv_metadata.csv` | Metadados das imagens Street View baixadas |
| `candidatos.csv` | Todos os candidatos com scores CLIP/SIFT |
| `candidatos_validados.csv` | Candidatos após validação LLM |
| `resultado_final.json` | Endereço final com confiança |
| `mapa.html` | Mapa interativo (abra no navegador) |
| `geolocaliza.log` | Log completo da execução |

---

## 🎛️ Ajuste de Parâmetros

Edite `config.py` para customizar o comportamento:

### Busca Geográfica

```python
SEARCH_CONFIG = {
    "initial_radius_m": 2000,        # Raio inicial de busca
    "grid_spacing_m": 50,            # Espaçamento da grade
    "refinement_radius_m": 200,      # Raio do refinamento
    "sv_min_year": 2024,             # Ano mínimo do Street View
    "max_sv_downloads": 500,         # Limite de downloads
}
```

### Machine Learning

```python
ML_CONFIG = {
    "clip_threshold": 0.70,          # ↓ = mais candidatos, ↑ = mais precisão
    "geom_threshold": 0.60,          # Threshold da geometria
    "min_confidence": 0.85,          # Confiança mínima final
    
    # Pesos do score combinado (soma = 1.0)
    "clip_weight": 0.5,              # Semântica
    "geom_weight": 0.3,              # Geometria
    "context_weight": 0.2,           # Validação LLM
}
```

---

## 🔍 Estratégias de Busca

### Cenário 1: Área Conhecida (Melhor Performance)

```python
resultado = geo.localizar_imovel(
    foto_path="casa.jpg",
    cidade="São Paulo",
    bairro="Alto da Boa Vista",      # ✅ Especifique o bairro!
    center_lat=-23.6505,
    center_lon=-46.6815,
    radius_m=1000                    # Raio pequeno
)
```

### Cenário 2: Área Desconhecida (Busca Ampla)

```python
resultado = geo.localizar_imovel(
    foto_path="casa.jpg",
    cidade="São Paulo",
    radius_m=5000                    # Raio maior
)
```

### Cenário 3: Dicas Visuais (Número/Placa Visível)

O sistema automaticamente detecta textos visíveis (números de endereço, placas de rua) e usa para refinar a busca. Certifique-se que esses elementos estejam bem visíveis na foto!

---

## ⚡ Otimizações

### 1. Usar Cache (Evita Re-downloads)

O sistema cacheia automaticamente:
- ✅ Embeddings CLIP
- ✅ Imagens Street View
- ✅ Buscas do Places API

Para limpar o cache:
```bash
rm -rf cache/
```

### 2. Paralelizar Busca (Avançado)

Edite `search_agent.py` e use `ThreadPoolExecutor` para downloads paralelos.

### 3. Reduzir Quota do Google

```python
SEARCH_CONFIG = {
    "max_sv_downloads": 200,         # ↓ Limite
    "request_delay": 0.5,            # ↑ Delay entre requests
    "sv_headings": [0, 90, 180, 270] # Menos ângulos
}
```

---

## 🐛 Troubleshooting

### ❌ "Nenhum candidato encontrado"

**Causas:**
- Área de busca incorreta
- Raio muito pequeno
- Sem Street View na região

**Soluções:**
```python
# 1. Aumente o raio
radius_m=5000

# 2. Verifique coordenadas
# Use Google Maps para obter lat/lon corretas

# 3. Reduza o ano mínimo do SV
SEARCH_CONFIG["sv_min_year"] = 2020
```

### ❌ "Confiança baixa (< 0.85)"

**Causas:**
- Foto de baixa qualidade
- Ângulo ruim
- Imóvel reformado recentemente

**Soluções:**
1. Tire foto de outro ângulo (frontal é melhor)
2. Certifique-se que há boa iluminação
3. Reduza threshold: `ML_CONFIG["min_confidence"] = 0.75`

### ❌ "API Error: Quota exceeded"

**Soluções:**
```python
# Reduzir downloads
SEARCH_CONFIG["max_sv_downloads"] = 100

# Aumentar delay
SEARCH_CONFIG["request_delay"] = 1.0

# Usar cache (não re-baixar)
CACHE_CONFIG["enabled"] = True
```

### ❌ "CUDA out of memory"

**Solução:**
```python
# Forçar uso de CPU
import torch
torch.cuda.is_available = lambda: False
```

---

## 📈 Melhorias Futuras

Você pode expandir o sistema:

1. **Múltiplas Fotos**: Modificar `main.py` para aceitar lista de fotos e combinar scores
2. **Fine-tuning CLIP**: Treinar em dataset de fachadas brasileiras
3. **Integração OSM**: Usar Overpass API como alternativa ao Google Places
4. **API REST**: Criar endpoint Flask/FastAPI
5. **UI Web**: Interface Streamlit ou Gradio

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs: `output/geolocaliza.log`
2. Teste agentes individualmente: `python test_sistema.py --individual`
3. Ajuste parâmetros em `config.py`

---

## 📄 Licença

MIT License - Use livremente!
