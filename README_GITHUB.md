# 🌍 Sistema de Geolocalização de Imóveis

Sistema multi-agente que identifica o endereço exato de um imóvel a partir de uma foto, usando visão computacional, Google Maps APIs e LLMs.

## 🎯 Como Funciona

1. **Análise Visual (GPT-4o)** → Extrai características arquitetônicas da foto
2. **Busca Geográfica (Google APIs)** → Encontra candidatos usando Places + Street View
3. **Matching Visual (CLIP + SIFT)** → Compara semanticamente e geometricamente
4. **Validação LLM (GPT-4o)** → Confirma match e extrai endereço completo

**Precisão:** 85-95% de confiança | **Tempo:** 2-5 minutos por busca

---

## 🚀 Uso Rápido no Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/)

```python
# 1. Clone o repositório
!git clone https://github.com/SEU-USUARIO/geolocalizacao-imoveis.git
%cd geolocalizacao-imoveis

# 2. Instale dependências
!pip install -q -r requirements.txt

# 3. Configure APIs
import os
from getpass import getpass

os.environ["GOOGLE_API_KEY"] = getpass("Google API Key: ")
os.environ["OPENAI_API_KEY"] = getpass("OpenAI API Key: ")

# 4. Execute
from main import GeoLocalizador

geo = GeoLocalizador()
resultado = geo.localizar_imovel(
    foto_path="sua_foto.jpg",
    cidade="São Paulo",
    bairro="Alto da Boa Vista",
    center_lat=-23.6505,
    center_lon=-46.6815,
    radius_m=2000
)

print(resultado["endereco"])
```

---

## 📋 Pré-requisitos

### **APIs Necessárias**

1. **Google Cloud Platform**
   - Places API (New)
   - Street View Static API
   - Street View Metadata API
   - **Custo:** ~$2.50-7.00 por busca

2. **OpenAI**
   - GPT-4o (Vision + Chat)
   - **Custo:** ~$0.20-0.80 por busca

### **Obter Chaves de API**

**Google:**
1. [console.cloud.google.com](https://console.cloud.google.com/)
2. Criar projeto → Habilitar APIs → Gerar API Key

**OpenAI:**
1. [platform.openai.com](https://platform.openai.com/)
2. API Keys → Create new secret key

---

## 💻 Instalação Local

```bash
# Clone
git clone https://github.com/SEU-USUARIO/geolocalizacao-imoveis.git
cd geolocalizacao-imoveis

# Instale dependências
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edite .env com suas chaves

# Execute
python main.py \
  --foto casa.jpg \
  --cidade "São Paulo" \
  --bairro "Alto da Boa Vista" \
  --lat -23.6505 \
  --lon -46.6815 \
  --raio 2000
```

---

## 📁 Estrutura do Projeto

```
geolocalizacao-imoveis/
├── config.py                    # Configurações centralizadas
├── main.py                      # Orquestrador principal
├── requirements.txt             # Dependências Python
├── .env.example                 # Template de variáveis de ambiente
├── agents/
│   ├── __init__.py
│   ├── vision_agent.py          # Análise visual (GPT-4o)
│   ├── search_agent.py          # Busca geográfica (Google)
│   ├── matching_agent.py        # Matching visual (CLIP+SIFT)
│   └── validation_agent.py      # Validação LLM (GPT-4o)
├── output/                      # Resultados gerados
│   ├── resultado_final.json
│   ├── mapa.html
│   └── street_views/
└── docs/
    ├── GUIA_EXECUCAO.md
    ├── SETUP_COMPLETO.md
    └── TROUBLESHOOTING_COLAB.md
```

---

## 🎓 Uso Programático

```python
from main import GeoLocalizador

# Inicializar
geo = GeoLocalizador()

# Executar
resultado = geo.localizar_imovel(
    foto_path="casa.jpg",
    cidade="São Paulo",
    bairro="Alto da Boa Vista",  # Opcional
    center_lat=-23.6505,
    center_lon=-46.6815,
    radius_m=2000
)

# Resultado
if resultado["success"]:
    print(f"📍 Endereço: {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"📊 Scores:")
    print(f"   CLIP: {resultado['scores']['clip']:.3f}")
    print(f"   SIFT: {resultado['scores']['geometria']:.3f}")
    print(f"   LLM:  {resultado['scores']['llm']:.3f}")
else:
    print(f"❌ Erro: {resultado['error']}")
```

---

## 📊 Outputs Gerados

- **`resultado_final.json`** - Endereço completo + confiança + scores
- **`analise_visual.json`** - Análise detalhada da foto (GPT-4o)
- **`candidatos.csv`** - Todos os matches encontrados
- **`candidatos_validados.csv`** - Top candidatos validados
- **`mapa.html`** - Mapa interativo (Folium)
- **`street_views/`** - Imagens baixadas do Google Street View
- **`geolocaliza.log`** - Log completo da execução

---

## ⚙️ Configurações Avançadas

Edite `config.py`:

```python
# Busca
SEARCH_CONFIG = {
    "initial_radius_m": 2000,      # Raio inicial
    "grid_spacing_m": 50,          # Espaçamento da grade
    "sv_min_year": 2024,           # Ano mínimo Street View
}

# Machine Learning
ML_CONFIG = {
    "clip_threshold": 0.70,        # Threshold CLIP
    "min_confidence": 0.85,        # Confiança mínima
    "clip_weight": 0.5,            # Peso CLIP
    "geom_weight": 0.3,            # Peso geometria
    "context_weight": 0.2,         # Peso LLM
}

# LLM
LLM_CONFIG = {
    "vision_model": "gpt-4o",      # Modelo de visão
    "validation_model": "gpt-4o",  # Modelo de validação
    "temperature": 0.1,
    "max_tokens": 2000,
}
```

---

## 🐛 Troubleshooting

### "Nenhum candidato encontrado"
- Verifique coordenadas no Google Maps
- Aumente `radius_m` para 3000-5000
- Confirme que há Street View na área

### "Confiança baixa (< 0.85)"
- Use foto de melhor qualidade
- Tire de ângulo diferente (mais elementos visíveis)
- Reduza `min_confidence` em `config.py`

### "Quota exceeded" (Google)
- Verifique billing no Google Cloud Console
- Aguarde reset da quota (diário)

### "API Error" (OpenAI)
- Verifique chave em platform.openai.com
- Adicione créditos
- Aguarde 1 minuto entre execuções

Mais detalhes: [TROUBLESHOOTING_COLAB.md](docs/TROUBLESHOOTING_COLAB.md)

---

## 💰 Custos Estimados

| Serviço | Custo por Busca | Detalhes |
|---------|----------------|----------|
| Google Places API | $0.50-2.00 | 200-500 requests |
| Google Street View | $2.00-5.00 | 200-500 imagens |
| OpenAI GPT-4o | $0.20-0.80 | Análise + validação |
| **TOTAL** | **$2.70-7.80** | Por execução completa |

---

## 🔒 Segurança

- **Nunca** commite o arquivo `.env`
- Use `.env.example` como template
- Mantenha chaves de API seguras
- Configure billing alerts no Google Cloud

---

## 📚 Documentação

- [GUIA_EXECUCAO.md](docs/GUIA_EXECUCAO.md) - Guia completo de uso
- [SETUP_COMPLETO.md](docs/SETUP_COMPLETO.md) - Setup passo a passo
- [TROUBLESHOOTING_COLAB.md](docs/TROUBLESHOOTING_COLAB.md) - Solução de problemas
- [MUDANCAS_OPENAI.md](docs/MUDANCAS_OPENAI.md) - Migração Anthropic → OpenAI

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## ✨ Tecnologias Utilizadas

- **Python 3.10+**
- **OpenAI GPT-4o** - Análise visual e validação
- **Google Maps APIs** - Places, Street View
- **OpenCLIP** - Embeddings semânticos de imagens
- **OpenCV** - SIFT/RANSAC para matching geométrico
- **PyTorch** - Backend para CLIP
- **Folium** - Mapas interativos
- **Pandas** - Manipulação de dados

---

## 🙏 Agradecimentos

- OpenAI pela API GPT-4o
- Google pelas Maps APIs
- OpenCLIP pela implementação open-source

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique [TROUBLESHOOTING_COLAB.md](docs/TROUBLESHOOTING_COLAB.md)
2. Veja issues existentes
3. Abra uma nova issue com:
   - Descrição do problema
   - Logs completos
   - Configuração usada

---

**Desenvolvido com ❤️ usando IA e Visão Computacional**
