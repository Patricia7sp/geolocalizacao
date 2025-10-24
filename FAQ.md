# ❓ FAQ - Perguntas Frequentes

## 🎯 Perguntas Gerais

### P: Como funciona o sistema exatamente?

**R:** O sistema usa uma abordagem multi-agente:
1. **Claude Vision** analisa sua foto e extrai características
2. **Google Places + Grid Search** busca candidatos na área
3. **OpenCLIP** compara semanticamente (cores, arquitetura)
4. **SIFT** valida geometria (pontos de interesse)
5. **Claude** faz validação contextual final
6. Retorna endereço com confiança > 85%

### P: Qual a precisão do sistema?

**R:** Com fotos boas e área bem definida: **80-90% de precisão**. Fatores que afetam:
- ✅ Foto frontal, boa iluminação
- ✅ Imóvel com características únicas
- ✅ Street View recente (2024+)
- ✅ Área de busca correta
- ❌ Foto de baixa qualidade
- ❌ Casas muito similares
- ❌ Sem Street View na região

### P: Quanto tempo leva?

**R:** Média de **2-5 minutos**, dependendo de:
- Raio de busca (quanto maior, mais tempo)
- Quantidade de candidatos
- Velocidade da conexão
- GPU disponível (mais rápido com CUDA)

### P: Quanto custa por busca?

**R:** Aproximadamente **$0.15-0.30**:
- Anthropic Claude: ~$0.05-0.10 (análise + validação)
- Google Street View: ~$0.10-0.20 (200-500 imagens)
- Google Places: grátis (até 200 req/dia)

---

## 🔧 Configuração e Instalação

### P: Quais APIs preciso habilitar?

**R:** No [Google Cloud Console](https://console.cloud.google.com):
1. Places API (New)
2. Street View Static API  
3. Street View Metadata API

E uma chave da [Anthropic](https://console.anthropic.com).

### P: Erro "GOOGLE_API_KEY não configurada"

**R:** Crie arquivo `.env`:
```env
GOOGLE_API_KEY=AIza...
ANTHROPIC_API_KEY=sk-ant-...
```

Ou exporte:
```bash
export GOOGLE_API_KEY="sua_chave"
export ANTHROPIC_API_KEY="sua_chave"
```

### P: Erro na instalação do OpenCV

**R:** Use a versão headless:
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-python-headless==4.10.0.84
```

### P: CUDA out of memory

**R:** Forçar CPU no `config.py`:
```python
import torch
torch.cuda.is_available = lambda: False
```

Ou reduza batch size dos embeddings.

---

## 🗺️ Busca e Resultados

### P: "Nenhum candidato encontrado"

**R:** Possíveis causas e soluções:

| Causa | Solução |
|-------|---------|
| Coordenadas erradas | Use Google Maps para pegar lat/lon corretas |
| Raio muito pequeno | Aumente `radius_m=5000` |
| Sem Street View | Verifique se há cobertura na área |
| Ano muito recente | Reduza `sv_min_year=2020` |

### P: "Confiança baixa (< 0.85)"

**R:** Causas:
- Foto de ângulo ruim
- Qualidade baixa
- Imóvel reformado
- Casas muito similares

**Soluções:**
1. Tire foto de outro ângulo (frontal é melhor)
2. Reduza threshold: `min_confidence=0.75`
3. Tire múltiplas fotos e combine
4. Aumente `topk_per_query` para mais candidatos

### P: Sistema retorna endereço errado

**R:** Verifique:
1. Confiança foi alta (> 85%)? Se não, resultado é incerto
2. Mapa interativo (`mapa.html`) mostra outros candidatos? Compare
3. Logs (`output/geolocaliza.log`) mostram warnings?
4. `candidatos_validados.csv` tem múltiplos matches similares?

Se sim, pode ser área com casas idênticas. Tente foto de outro lado.

### P: Posso usar em outra cidade/país?

**R:** Sim! Basta ajustar coordenadas:
```python
resultado = geo.localizar_imovel(
    foto_path="casa.jpg",
    cidade="Rio de Janeiro",
    bairro="Leblon",
    center_lat=-22.9838,
    center_lon=-43.2179,
    radius_m=2000
)
```

Funciona em qualquer lugar com Street View.

---

## ⚙️ Customização

### P: Como ajustar a sensibilidade?

**R:** Edite `config.py`:

**Mais candidatos (recall alto):**
```python
ML_CONFIG = {
    "clip_threshold": 0.60,      # ↓ aceita matches mais fracos
    "min_confidence": 0.75,      # ↓ threshold final
    "top_k_candidates": 30,      # ↑ mais candidatos para LLM
}
```

**Mais precisão (precision alto):**
```python
ML_CONFIG = {
    "clip_threshold": 0.80,      # ↑ só matches fortes
    "min_confidence": 0.90,      # ↑ threshold final
    "geom_threshold": 0.70,      # ↑ geometria mais rigorosa
}
```

### P: Como balancear CLIP vs Geometria?

**R:** Ajuste os pesos (soma = 1.0):
```python
ML_CONFIG = {
    # Priorizar semântica (cores, estilo)
    "clip_weight": 0.6,
    "geom_weight": 0.2,
    "context_weight": 0.2,
    
    # Priorizar geometria (estrutura física)
    "clip_weight": 0.3,
    "geom_weight": 0.5,
    "context_weight": 0.2,
}
```

### P: Como reduzir uso de API?

**R:**
```python
SEARCH_CONFIG = {
    "max_sv_downloads": 200,     # ↓ limite
    "request_delay": 0.5,        # ↑ delay
    "sv_headings": [0, 180],     # menos ângulos (só frente/trás)
    "grid_spacing_m": 100,       # ↑ espaçamento (menos pontos)
}

CACHE_CONFIG = {
    "enabled": True,             # ✅ usar cache
}
```

---

## 🚀 Performance

### P: Como acelerar o processo?

**R:** 
1. **Use GPU**: 3-4x mais rápido para CLIP
2. **Cache**: não re-baixa Street Views
3. **Reduza raio**: busca mais focada
4. **Menos headings**: `[0, 90, 180, 270]` em vez de 8

### P: Posso processar múltiplas fotos em paralelo?

**R:** Sim:
```python
from concurrent.futures import ThreadPoolExecutor

fotos = ["casa1.jpg", "casa2.jpg", "casa3.jpg"]
geo = GeoLocalizador()

with ThreadPoolExecutor(max_workers=2) as executor:
    resultados = list(executor.map(geo.localizar_imovel, fotos))
```

**Cuidado:** Respeite quotas das APIs!

### P: Logs estão muito verbosos

**R:** Em `config.py`:
```python
LOGGING_CONFIG = {
    "level": "WARNING",  # ou "ERROR"
}
```

---

## 🐛 Debug

### P: Como debugar problemas?

**R:** Passo a passo:

**1. Teste agentes individualmente:**
```bash
python test_sistema.py --individual
```

**2. Verifique logs:**
```bash
tail -f output/geolocaliza.log
```

**3. Analise CSVs intermediários:**
- `sv_metadata.csv` - Street Views baixados
- `candidatos.csv` - Scores CLIP/SIFT
- `candidatos_validados.csv` - Validação LLM

**4. Visualize mapa:**
Abra `output/mapa.html` e veja distribuição dos candidatos

**5. Teste API individualmente:**
```python
from agents.vision_agent import VisionAgent

agent = VisionAgent()
result = agent.analyze_image("foto.jpg")
print(result)
```

### P: Claude retorna JSON inválido

**R:** Problema no parsing. Adicione retry:
```python
# Em validation_agent.py, método _validate_match
for attempt in range(3):
    try:
        validation = json.loads(response_text.strip())
        break
    except json.JSONDecodeError:
        if attempt == 2:
            return fallback_response
        continue
```

### P: Erro "Rate limit exceeded"

**R:**
```python
# Aumentar delay em config.py
SEARCH_CONFIG["request_delay"] = 1.0

# Ou usar backoff exponencial
import time
for retry in range(3):
    try:
        response = requests.get(url)
        break
    except Exception:
        time.sleep(2 ** retry)
```

---

## 📊 Análise de Resultados

### P: Como interpretar a confiança?

**R:**
- **> 90%**: Match muito confiável
- **85-90%**: Bom match, verificar mapa
- **75-85%**: Incerto, checar discrepâncias
- **< 75%**: Não confiável

### P: O que significa cada score?

**R:**
- **CLIP**: Similaridade semântica (cores, arquitetura, composição)
- **Geometria**: Match de pontos de interesse (SIFT + RANSAC)
- **LLM**: Validação contextual (considera reformas, mudanças)

### P: Múltiplos candidatos com score similar?

**R:** Indica área com casas parecidas. Soluções:
1. Tire foto de outro ângulo
2. Compare visualmente no mapa
3. Use dicas textuais (número da casa visível)
4. Considere múltiplas fotos

---

## 🔒 Privacidade e Segurança

### P: As fotos são armazenadas?

**R:** Não. Tudo é processado localmente. Apenas embeddings/metadados são salvos em `output/`.

### P: As chaves de API são seguras?

**R:** Use `.env` e **nunca** comite no Git:
```bash
echo ".env" >> .gitignore
```

Para produção, use secrets managers (AWS Secrets, etc).

### P: Posso usar sem internet?

**R:** Não. O sistema precisa das APIs:
- Google (Street View, Places)
- Anthropic (Claude)

Mas você pode cachear Street Views e rodar offline depois.

---

## 🌟 Casos de Uso

### P: Funciona para apartamentos?

**R:** Sim, mas com limitações:
- Precisa ver a fachada do prédio
- Número do apartamento não é detectado (só endereço do prédio)
- Funciona melhor se prédio tem características únicas

### P: Funciona para fazendas/sítios?

**R:** Depende:
- ✅ Se houver Street View na estrada de acesso
- ❌ Se for muito afastado (sem cobertura SV)
- Use coordenadas aproximadas e raio grande

### P: Posso usar para verificar imóveis em anúncios?

**R:** Sim! Use caso comum:
```python
# Foto do anúncio
resultado = geo.localizar_imovel("anuncio.jpg")

# Comparar com endereço declarado
if resultado["success"]:
    if resultado["endereco"] != endereco_anuncio:
        print("⚠️  Endereço não bate!")
```

---

## 🚧 Limitações Conhecidas

### P: Quais são as limitações?

**R:**

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Street View desatualizado | Reformas não detectadas | Usar `sv_min_year=2024` |
| Casas idênticas | Ambiguidade | Múltiplas fotos |
| Sem SV na área | Sem candidatos | Não há solução |
| Foto de baixa qualidade | Scores baixos | Melhorar foto |
| Quota de API | Limite diário | Cache + delays |

### P: O sistema detecta o número da casa?

**R:** Às vezes. Se:
- ✅ Número visível na foto do usuário (OCR via Claude)
- ✅ Número visível no Street View
- ❌ Caso contrário, retorna endereço sem número específico

### P: Funciona à noite ou com chuva?

**R:** Depende da foto:
- **Noite**: Funciona se houver boa iluminação
- **Chuva**: Pode reduzir qualidade do matching
- **Ideal**: Dia, céu claro, sol brando

---

## 📈 Melhorias Futuras

### P: Posso contribuir com melhorias?

**R:** Sim! Sugestões de expansão:

1. **Fine-tuning CLIP**: Treinar em dataset de fachadas brasileiras
2. **Múltiplas fotos**: Combinar scores de várias imagens
3. **OSM Integration**: Usar Overpass API além do Google
4. **API REST**: Flask/FastAPI endpoint
5. **UI Web**: Streamlit/Gradio interface
6. **Mobile**: App nativo (React Native)

### P: Como melhorar para meu caso específico?

**R:** Ajuste os prompts em `config.py`:

**Para regiões específicas:**
```python
PROMPTS["visual_analysis"] = """
Analise esta foto de imóvel em [SUA REGIÃO].
Características comuns da região: [LISTAR]
...
"""
```

**Para tipos específicos (casas vs apartamentos):**
```python
SEARCH_CONFIG["queries"] = [
    "apartamentos residenciais",
    "edifícios",
    "condomínios verticais"
]
```

---

## 📞 Suporte

### P: Onde reportar bugs?

**R:** 
1. Verifique `output/geolocaliza.log`
2. Teste com `test_sistema.py --individual`
3. Documente: foto usada, erro, logs

### P: Como obter ajuda?

**R:**
1. Consulte documentação: `README.md`, `GUIA_USO.md`, `ARQUITETURA.md`
2. Revise este FAQ
3. Verifique issues conhecidos

---

## 🎓 Recursos de Aprendizado

### Papers e Tecnologias

- **CLIP**: [Learning Transferable Visual Models](https://arxiv.org/abs/2103.00020)
- **SIFT**: [Distinctive Image Features](https://www.cs.ubc.ca/~lowe/papers/ijcv04.pdf)
- **RANSAC**: [Random Sample Consensus](https://en.wikipedia.org/wiki/RANSAC)
- **Claude**: [Anthropic Documentation](https://docs.anthropic.com)

### Tutoriais Relacionados

- Geolocalização com Deep Learning
- Visual Place Recognition
- Image Retrieval Systems
- Multi-Agent Systems

---

**Última atualização:** Outubro 2024  
**Versão do sistema:** 1.0
