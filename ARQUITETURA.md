# 🏗️ Arquitetura do Sistema

## 📐 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    FOTO DO IMÓVEL (INPUT)                   │
│                         casa.jpg                            │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             🔍 AGENTE 1: ANÁLISE VISUAL                     │
│                  (Claude Vision)                            │
│                                                             │
│  Extrai:                                                    │
│  • Estilo arquitetônico (moderno/clássico/etc)             │
│  • Cores, materiais, texturas                              │
│  • Elementos distintivos (portão, janelas, varanda)        │
│  • Contexto urbano (árvores, postes, vizinhos)             │
│  • Textos visíveis (números, placas, nomes)                │
│                                                             │
│  Output: analise_visual.json                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          🗺️  AGENTE 2: BUSCA GEOGRÁFICA                     │
│           (Google Places + Grid Search)                     │
│                                                             │
│  Estratégia Funil:                                          │
│  1. Places API → Busca condomínios na área                 │
│  2. Grid Search → Pontos espaçados (50m)                   │
│  3. Metadata API → Verifica Street View disponível         │
│  4. Download SV → 8 headings por ponto                     │
│  5. Refinamento → Grid denso (20m) ao redor dos top-3      │
│                                                             │
│  Output: street_views/ (imagens) + sv_metadata.csv         │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         🎯 AGENTE 3: MATCHING VISUAL                        │
│          (OpenCLIP + SIFT/RANSAC)                           │
│                                                             │
│  Para cada Street View:                                     │
│                                                             │
│  ┌─────────────────────┐     ┌─────────────────────┐       │
│  │  CLIP (ViT-bigG)    │     │  SIFT + RANSAC      │       │
│  │                     │     │                     │       │
│  │  Similaridade       │     │  Geometria          │       │
│  │  semântica:         │     │  (pontos de         │       │
│  │  - Cores            │     │   interesse):       │       │
│  │  - Arquitetura      │     │  - Keypoints        │       │
│  │  - Composição       │     │  - Homografia       │       │
│  │                     │     │  - Inliers          │       │
│  │  Score: 0.0 - 1.0   │     │  Score: 0.0 - 1.0   │       │
│  └──────────┬──────────┘     └──────────┬──────────┘       │
│             │                           │                  │
│             └───────────┬───────────────┘                  │
│                         ▼                                  │
│              Score Combinado:                              │
│              0.5*CLIP + 0.3*GEOM                           │
│                                                            │
│  Output: candidatos.csv (top-20 por query)                │
└─────────────────────────────┬──────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          🤖 AGENTE 4: VALIDAÇÃO LLM                         │
│              (Claude Sonnet)                                │
│                                                             │
│  Para top-5 candidatos:                                     │
│                                                             │
│  1. Analisa Street View com Claude Vision                  │
│  2. Compara descrições (query vs SV)                       │
│  3. Verifica elementos compatíveis:                        │
│     • Arquitetura bate?                                    │
│     • Cores compatíveis?                                   │
│     • Contexto similar?                                    │
│     • Elementos únicos confirmam?                          │
│  4. Detecta discrepâncias                                  │
│  5. Considera mudanças (reforma, pintura)                  │
│                                                             │
│  Output: candidatos_validados.csv + confidence             │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│           📍 RESULTADO FINAL                                │
│                                                             │
│  Confiança >= 85%? ✅                                       │
│                                                             │
│  ┌───────────────────────────────────────────────┐         │
│  │  Endereço: Rua das Flores, 123                │         │
│  │  Bairro: Alto da Boa Vista                    │         │
│  │  Cidade: São Paulo - SP                       │         │
│  │  CEP: 05467-000                               │         │
│  │                                                │         │
│  │  Coordenadas: -23.6505, -46.6815              │         │
│  │  Confiança: 92%                                │         │
│  │                                                │         │
│  │  Scores:                                       │         │
│  │    CLIP: 0.85                                  │         │
│  │    Geometria: 0.78                             │         │
│  │    LLM: 0.94                                   │         │
│  │                                                │         │
│  │  🗺️  Street View Link                          │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
│  Outputs:                                                   │
│  • resultado_final.json                                    │
│  • mapa.html (visualização interativa)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Dados Detalhado

### 1. Input Processing
```
Foto → PIL Image → Resize (2048px) → Base64 → Claude API
                                              ↓
                                        JSON estruturado
```

### 2. Geographic Search
```
Centro + Raio → Places API → Condomínios
                           ↓
            Grid (lat/lon) → SV Metadata → Filtro ano >= 2024
                                         ↓
                                    Download SV (8 ângulos)
```

### 3. Visual Matching
```
Query Image → CLIP Embedding (1280-dim)
                    ↓
                 Cosine Similarity com cada SV
                    ↓
                Top-K (CLIP >= 0.70)
                    ↓
                SIFT matching (se CLIP > threshold)
                    ↓
                Score combinado
```

### 4. LLM Validation
```
Query Analysis + SV Analysis → Prompt → Claude
                                       ↓
                               is_match: true/false
                               confidence: 0.0-1.0
                               reasoning: string
                                       ↓
                               Final confidence =
                               0.8*visual + 0.2*llm
```

---

## 🧮 Cálculos de Score

### Score CLIP
```python
# Embeddings normalizados L2
query_emb = model.encode_image(query)  # shape: (1280,)
sv_emb = model.encode_image(sv)        # shape: (1280,)

# Similaridade de cosseno (dot product de vetores normalizados)
clip_score = np.dot(query_emb, sv_emb)  # range: [-1, 1] → [0, 1]
```

### Score Geométrico (SIFT)
```python
# Detectar keypoints
kp1, desc1 = SIFT(query)   # ex: 2000 keypoints
kp2, desc2 = SIFT(sv)      # ex: 1800 keypoints

# Matching com ratio test
matches = knnMatch(desc1, desc2, k=2)
good = [m for m,n in matches if m.distance < 0.75*n.distance]

# RANSAC para filtrar outliers
H, mask = findHomography(good, RANSAC)
inliers = mask.sum()  # ex: 45

# Normalização
geom_score = min(1.0, inliers / 60.0)  # 60 inliers = score 1.0
```

### Score Combinado
```python
combined = 0.5 * clip_score + 0.3 * geom_score + 0.2 * context
#          └─ semântica      └─ geometria        └─ LLM

# Threshold final
if combined >= 0.85:
    return address
```

---

## 📊 Performance Esperada

| Métrica | Valor |
|---------|-------|
| **Tempo médio** | 2-5 minutos |
| **Precisão (conf>85%)** | 80-90% |
| **Requisições Google** | 200-500 |
| **Uso de memória** | ~4GB (GPU) / ~8GB (CPU) |
| **Custo por busca** | ~$0.20 (APIs) |

### Breakdown de Tempo
- Análise visual: 5-10s
- Busca geográfica: 30-60s
- Download SV: 60-120s (depende da quantidade)
- Matching CLIP: 30-60s
- Validação LLM: 20-40s

---

## 🔧 Componentes Técnicos

### APIs Usadas
| API | Função | Custo |
|-----|--------|-------|
| Claude Vision (Anthropic) | Análise visual | $3/1000 imgs |
| Google Places (New) | Busca condomínios | Grátis até 200 req/dia |
| Street View Static | Download imagens | $7/1000 imgs |
| Street View Metadata | Verificar disponibilidade | Grátis |

### Modelos ML
| Modelo | Tamanho | Função |
|--------|---------|--------|
| ViT-bigG-14 | 2.5GB | CLIP embedding |
| SIFT | N/A | Feature detection |

---

## 🎯 Casos de Uso

### ✅ Funciona Bem
- Casas com fachada única
- Áreas com boa cobertura de Street View
- Fotos frontais, boa iluminação
- Imóveis em condomínios fechados

### ⚠️  Desafios
- Casas muito similares (condomínios padronizados)
- Áreas sem Street View recente
- Fotos de ângulo ruim ou baixa qualidade
- Imóveis reformados após Street View

---

## 🚀 Escalabilidade

Para processar múltiplas fotos em paralelo:

```python
from concurrent.futures import ThreadPoolExecutor

def processar_lote(fotos_list):
    geo = GeoLocalizador()
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(geo.localizar_imovel, foto)
            for foto in fotos_list
        ]
        
        resultados = [f.result() for f in futures]
    
    return resultados
```

**Limitações:**
- Quota das APIs (principalmente Google)
- Memória GPU (CLIP carrega modelo por worker)
- Disk I/O (cache de imagens)
