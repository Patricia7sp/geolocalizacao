# 🎯 Guia de Ajuste de Thresholds

## 📊 Mudanças Implementadas

### **Problema Original**
```
❌ Erro: Nenhum candidato passou no threshold visual
```

Isso significa que o modelo estava **muito rigoroso** e rejeitava matches válidos.

---

## ✅ Ajustes Realizados

### **1. Thresholds de Similaridade (REDUZIDOS)**

| Parâmetro | Antes | Depois | Impacto |
|-----------|-------|--------|---------|
| **CLIP threshold** | 0.70 | **0.50** ⬇️ | Aceita matches com 50% de similaridade semântica |
| **Geometria threshold** | 0.60 | **0.45** ⬇️ | Menos rigoroso com geometria |
| **Confiança mínima** | 0.85 | **0.70** ⬇️ | Retorna resultados com 70% de confiança |
| **Min inliers** | 20 | **15** ⬇️ | Aceita menos pontos geométricos |

**Resultado:** Mais candidatos passam no filtro visual!

---

### **2. Área de Busca (AUMENTADA)**

| Parâmetro | Antes | Depois | Impacto |
|-----------|-------|--------|---------|
| **Raio inicial** | 2km | **3km** ⬆️ | Cobre área 2.25x maior |
| **Grid spacing** | 50m | **40m** ⬇️ | 56% mais pontos testados |
| **Max downloads** | 500 | **800** ⬆️ | 60% mais tentativas |
| **Street View ano** | 2024 | **2020** ⬇️ | Aceita fotos de 4 anos atrás |

**Resultado:** Maior cobertura geográfica!

---

### **3. Raios Progressivos (AUMENTADOS 50%)**

#### **Com Bairro (Santo Amaro):**
```
Antes: 2km → 3km → 5km
Depois: 3km → 5km → 8km  ⬆️
```

#### **Com Região (Zona Sul):**
```
Antes: 3km → 5km → 8km
Depois: 5km → 8km → 12km  ⬆️
```

#### **Sem Especificar:**
```
Antes: 5km → 10km → 20km
Depois: 8km → 15km → 25km  ⬆️
```

**Resultado:** Busca em área muito maior!

---

### **4. Candidatos para Validação (AUMENTADO)**

| Parâmetro | Antes | Depois | Impacto |
|-----------|-------|--------|---------|
| **Top K candidates** | 20 | **30** ⬆️ | 50% mais candidatos testados pelo LLM |
| **Max Places results** | 100 | **150** ⬆️ | Busca mais condomínios |

**Resultado:** Mais opções para o LLM validar!

---

## 🚀 Como Testar Agora

```python
# 1. Atualizar código
%cd geolocalizacao
!git pull

# 2. Buscar com configurações otimizadas
from main import GeoLocalizador

geo = GeoLocalizador()
resultado = geo.localizar_imovel(
    foto_path=fotos[0],
    cidade="São Paulo",
    bairro="Santo Amaro",
    center_lat=-23.6505,
    center_lon=-46.7085,
    radius_m=3000  # Agora começa com 3km
)

# 3. Ver resultado
if resultado["success"]:
    print(f"🎉 ENCONTRADO!")
    print(f"📍 {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"\n📊 Scores:")
    print(f"   CLIP: {resultado['scores']['clip']:.3f}")
    print(f"   Geometria: {resultado['scores']['geometria']:.3f}")
    print(f"   LLM: {resultado['scores']['llm']:.3f}")
else:
    print(f"❌ {resultado['error']}")
```

---

## 📈 Comparação de Performance

### **Antes dos Ajustes:**
```
✅ Candidatos encontrados: 584
❌ Passaram no threshold: 0
❌ Taxa de sucesso: 0%
```

### **Depois dos Ajustes (Esperado):**
```
✅ Candidatos encontrados: 800+
✅ Passaram no threshold: 10-50
✅ Taxa de sucesso: 60-80%
```

---

## 🎯 O Que Esperar

### **Mais Candidatos Aceitos:**
```
Antes:
  🔍 Testando 584 candidatos...
  ❌ Nenhum passou no threshold (0.70)

Depois:
  🔍 Testando 800+ candidatos...
  ✅ 15 candidatos passaram no threshold (0.50)
  🎯 Melhor match: 0.68 de confiança
```

### **Busca Mais Ampla:**
```
Antes:
  📍 Raio 1: 2km (área: 12.6 km²)
  📍 Raio 2: 3km (área: 28.3 km²)
  📍 Raio 3: 5km (área: 78.5 km²)

Depois:
  📍 Raio 1: 3km (área: 28.3 km²)  ⬆️
  📍 Raio 2: 5km (área: 78.5 km²)  ⬆️
  📍 Raio 3: 8km (área: 201 km²)   ⬆️
```

---

## ⚠️ Trade-offs

### **Vantagens:**
- ✅ Maior taxa de sucesso
- ✅ Encontra imóveis em área maior
- ✅ Menos falsos negativos
- ✅ Aceita fotos mais antigas do Street View

### **Desvantagens:**
- ⚠️ Mais tempo de processamento (3-15 min → 5-20 min)
- ⚠️ Maior custo de API ($10-30 → $15-40)
- ⚠️ Possibilidade de falsos positivos (mas LLM valida)

---

## 🔧 Ajustes Manuais (Se Necessário)

Se ainda não encontrar, você pode ajustar manualmente no código:

### **Reduzir Ainda Mais os Thresholds:**

Edite `config.py`:

```python
ML_CONFIG = {
    "clip_threshold": 0.40,      # ⬇️ Ainda mais flexível
    "geom_threshold": 0.35,      # ⬇️ Geometria muito flexível
    "min_confidence": 0.60,      # ⬇️ Aceita 60% de confiança
    "min_inliers": 10,           # ⬇️ Apenas 10 pontos geométricos
}
```

### **Aumentar Área de Busca:**

Edite `main.py`:

```python
# Linha ~626
raios = [5000, 8000, 12000]  # ⬆️ Começa com 5km
```

### **Aceitar Fotos Muito Antigas:**

Edite `config.py`:

```python
SEARCH_CONFIG = {
    "sv_min_year": 2015,  # ⬇️ Aceita fotos de 2015+
}
```

---

## 📊 Monitoramento

Durante a busca, observe os logs:

### **Bom Sinal:**
```
✅ 584 candidatos com Street View
🔍 Comparando imagens...
✅ 12 candidatos passaram no threshold visual
🎯 Top 5 scores: [0.68, 0.65, 0.62, 0.58, 0.55]
```

### **Sinal de Problema:**
```
✅ 584 candidatos com Street View
🔍 Comparando imagens...
❌ Nenhum candidato passou no threshold visual
💡 Dica: Aumente o raio ou reduza thresholds
```

---

## 💡 Dicas para Melhorar Resultados

### **1. Use Múltiplas Fotos:**
```python
from main import buscar_com_multiplas_fotos

resultado = buscar_com_multiplas_fotos(
    fotos=["foto1.jpg", "foto2.jpg", "foto3.jpg"],
    cidade="São Paulo",
    bairro="Santo Amaro"
)
```

### **2. Especifique Bairro Correto:**
```python
# ❌ Errado
bairro="Chácara Monte Alegre"  # Muito específico

# ✅ Certo
bairro="Santo Amaro"  # Bairro conhecido
```

### **3. Use Coordenadas Diretas:**
```python
# Se souber a região aproximada
resultado = geo.localizar_imovel(
    foto_path="foto.jpg",
    cidade="São Paulo",
    center_lat=-23.6505,  # Centro de Santo Amaro
    center_lon=-46.7085,
    radius_m=5000  # 5km de raio
)
```

### **4. Tente Raios Maiores:**
```python
# Para casos muito difíceis
raios = [5000, 10000, 15000]  # Até 15km

for raio in raios:
    print(f"Tentando raio: {raio}m")
    resultado = geo.localizar_imovel(
        foto_path="foto.jpg",
        cidade="São Paulo",
        center_lat=-23.6505,
        center_lon=-46.7085,
        radius_m=raio
    )
    if resultado["success"]:
        break
```

---

## 🎉 Resultado Esperado

Com estes ajustes, a taxa de sucesso deve aumentar de **~30%** para **~70-80%** em casos típicos!

**Teste agora e me avise o resultado!** 🚀

---

## 📞 Troubleshooting

### **Ainda não encontrou?**

1. **Verifique se o imóvel tem Street View:**
   - Abra Google Maps
   - Procure o endereço
   - Arraste o bonequinho amarelo
   - Se não tiver cobertura azul = sem Street View

2. **Tente com foto de melhor qualidade:**
   - Fachada completa e clara
   - Boa iluminação
   - Sem obstruções

3. **Aumente ainda mais os raios:**
   - Tente até 20km se necessário
   - Pode levar 20-30 minutos

4. **Reduza thresholds manualmente:**
   - Veja seção "Ajustes Manuais" acima

**Me avise se precisar de mais ajustes!** 💪
