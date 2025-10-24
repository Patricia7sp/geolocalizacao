"""
Configuração do Sistema de Geolocalização de Imóveis
"""

import os
from pathlib import Path

# Tentar carregar do .env (local) ou do Colab Secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Diretórios
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"

# Criar diretórios
for d in [OUTPUT_DIR, CACHE_DIR, DATA_DIR]:
    d.mkdir(exist_ok=True, parents=True)

# APIs - Tentar múltiplas fontes
def get_api_key(key_name):
    """Obtém chave de API de múltiplas fontes."""
    # 1. Variável de ambiente
    key = os.getenv(key_name, "")
    if key:
        return key
    
    # 2. Colab Secrets (se disponível)
    try:
        from google.colab import userdata
        key = userdata.get(key_name)
        if key:
            return key
    except (ImportError, Exception):
        pass
    
    return ""

GOOGLE_API_KEY = get_api_key("GOOGLE_API_KEY")
OPENAI_API_KEY = get_api_key("OPENAI_API_KEY")

# Configurações de busca
SEARCH_CONFIG = {
    # Área de busca inicial
    "default_city": "São Paulo",
    "default_state": "SP",
    
    # Estratégia de busca
    "search_strategy": "funnel",  # funnel (macro→micro) ou grid (grade)
    "initial_radius_m": 2000,     # raio inicial
    "grid_spacing_m": 50,         # espaçamento da grade
    "refinement_radius_m": 200,   # raio de refinamento após match
    "refinement_spacing_m": 20,   # espaçamento no refinamento
    
    # Street View
    "sv_min_year": 2024,
    "sv_size": "640x640",
    "sv_fov": 90,
    "sv_headings": [0, 45, 90, 135, 180, 225, 270, 315],
    
    # Limites
    "max_sv_downloads": 500,
    "max_places_results": 100,
    "request_delay": 0.1,  # delay entre requisições (segundos)
}

# Configurações de ML
ML_CONFIG = {
    # OpenCLIP
    "clip_model": "ViT-bigG-14",
    "clip_pretrained": "laion2b_s39b_b160k",
    "clip_threshold": 0.70,  # threshold mínimo para considerar match
    
    # SIFT (geometria)
    "sift_features": 4000,
    "sift_match_ratio": 0.75,
    "min_inliers": 20,
    "geom_threshold": 0.60,
    
    # Score combinado (soma = 1.0)
    "clip_weight": 0.5,
    "geom_weight": 0.3,
    "context_weight": 0.2,
    
    # Validação final
    "min_confidence": 0.85,  # confiança mínima para retornar resultado
    "top_k_candidates": 20,  # quantos candidatos levar para validação LLM
}

# Configurações do LLM
LLM_CONFIG = {
    "vision_model": "gpt-4o",  # ou gpt-4-vision-preview
    "validation_model": "gpt-4o",
    "temperature": 0.1,
    "max_tokens": 2000,
}

# Prompts
PROMPTS = {
    "visual_analysis": """Analise esta foto de imóvel residencial e extraia características detalhadas.

IMPORTANTE: Seja objetivo e específico. Foque em elementos que podem ser usados para identificar o imóvel.

Responda APENAS com JSON válido (sem markdown, sem explicações):

{
  "architecture": {
    "style": "moderno/clássico/colonial/industrial/contemporâneo",
    "floors_visible": 1-3,
    "roof_type": "telha aparente/laje/telha escondida/outro",
    "main_color": "cor predominante da fachada",
    "material": "concreto/tijolo/madeira/misto"
  },
  "distinctive_features": {
    "gate_type": "grade/portão madeira/metal/automático/manual",
    "windows": {
      "style": "veneziana/vidro/madeira/alumínio",
      "count_visible": número aproximado
    },
    "balcony_garage": "sim/não/não visível",
    "garden_plants": "sim/não/plantas específicas se visível",
    "unique_elements": ["elemento 1", "elemento 2"]
  },
  "urban_context": {
    "street_type": "residencial/avenida/rua íngreme/travessa",
    "sidewalk": "larga/estreita/ausente/bem conservada/deteriorada",
    "trees_visible": "sim/não/tipo se identificável",
    "utility_poles": "sim/não",
    "adjacent_buildings": "casas similares/prédios/misto/isolado",
    "street_slope": "plana/íngreme/leve inclinação"
  },
  "visible_text": {
    "address_number": "número ou 'não visível'",
    "street_signs": ["placa 1", "placa 2"] ou [],
    "condo_name": "nome ou 'não visível'",
    "other_text": ["texto 1"] ou []
  },
  "photography": {
    "angle": "frontal/lateral/diagonal",
    "distance": "próxima/média/distante",
    "quality": "boa/regular/baixa"
  }
}""",

    "match_validation": """Compare estas duas descrições de imóveis e determine se são do MESMO local.

**Foto do Usuário:**
{desc_user}

**Street View (candidato):**
{desc_sv}

**Coordenadas do candidato:** {lat}, {lon}
**Confiança visual (CLIP+SIFT):** {visual_score:.3f}

Analise criteriosamente:
1. Arquitetura bate? (estilo, andares, telhado, cores)
2. Elementos distintivos coincidem? (portão, janelas, varanda)
3. Contexto urbano é compatível? (árvores, postes, rua, vizinhos)
4. Há elementos ÚNICOS que confirmam ou negam o match?
5. Considere possíveis mudanças (reforma, pintura, vegetação crescida)

Responda APENAS com JSON válido:

{
  "is_match": true ou false,
  "confidence": 0.0 a 1.0,
  "reasoning": "explicação concisa em 1-2 frases",
  "matching_elements": ["elemento 1 que bate", "elemento 2"],
  "discrepancies": ["diferença 1", "diferença 2"] ou [],
  "likely_changes": ["possível reforma", "pintura"] ou []
}""",

    "address_extraction": """Determine o endereço mais provável deste imóvel baseado nas informações disponíveis.

**Coordenadas confirmadas:** {lat}, {lon}
**Análise visual:** {visual_analysis}
**Contexto geográfico:** {geo_context}

Use Google Maps reverse geocoding interno e as informações visuais para determinar:

Responda APENAS com JSON válido:

{
  "street": "nome da rua",
  "number": "número (se identificado visualmente ou por proximidade)",
  "complement": "apto/casa/bloco se aplicável",
  "neighborhood": "bairro",
  "city": "cidade",
  "state": "UF",
  "zip_code": "CEP se disponível",
  "full_address": "endereço completo formatado",
  "confidence": 0.0 a 1.0,
  "source": "visual+gps/gps_only/visual_hint"
}"""
}

# Configurações de cache
CACHE_CONFIG = {
    "enabled": True,
    "cache_embeddings": True,  # cachear embeddings CLIP
    "cache_street_view": True,  # cachear downloads SV
    "cache_places": True,       # cachear buscas Places
    "ttl_days": 30,             # tempo de vida do cache
}

# Configurações de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    "file": OUTPUT_DIR / "geolocaliza.log",
}
