# 🚨 MODO INVESTIGAÇÃO - Busca Apenas por Foto

## 🎯 Para Que Serve

Este modo é ideal para situações onde você tem **APENAS a foto** e precisa encontrar o local, sem saber:
- ❌ Endereço
- ❌ Coordenadas
- ❌ Bairro exato
- ❌ Ponto de referência

**Casos de uso:**
- 🚔 Investigação policial / emergências
- 🏠 Corretagem de imóveis (cliente manda só foto)
- 🔍 Busca e resgate
- 📸 Identificação de locais desconhecidos

---

## 🚀 Como Usar no Colab

### **Modo Simples (Só Foto + Cidade)**

```python
# 1. Clone e instale (se ainda não fez)
!git clone https://github.com/Patricia7sp/geolocalizacao.git
%cd geolocalizacao
!pip install -q -r requirements.txt

# 2. Upload da foto
from google.colab import files
uploaded = files.upload()
foto_path = list(uploaded.keys())[0]

# 3. BUSCAR APENAS POR FOTO
from main import buscar_apenas_por_foto

resultado = buscar_apenas_por_foto(
    foto_path=foto_path,
    cidade="São Paulo",  # Cidade onde você acha que está
    estado="SP"
)

# 4. Ver resultado
if resultado["success"]:
    print(f"\n🎉 LOCALIZAÇÃO ENCONTRADA!")
    print(f"📍 Endereço: {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"\n📊 Detalhes:")
    print(f"   Rua: {resultado['rua']}")
    print(f"   Número: {resultado['numero']}")
    print(f"   Bairro: {resultado['bairro']}")
    print(f"   Cidade: {resultado['cidade']}")
    print(f"\n🗺️  Google Maps: {resultado['street_view_link']}")
else:
    print(f"\n❌ Não encontrado: {resultado['error']}")
    if "pistas_encontradas" in resultado:
        print(f"\n📝 Pistas detectadas na foto:")
        for pista in resultado["pistas_encontradas"]:
            print(f"   • {pista}")
```

---

## 🔍 Como Funciona

### **1. Análise da Foto**
O sistema extrai automaticamente:
- 📝 **Texto visível** (placas, números de casa, nomes de rua)
- 🏛️ **Pontos de referência** (igrejas, lojas, monumentos)
- 🏗️ **Características arquitetônicas** (estilo, cores, materiais)
- 🌳 **Contexto** (vegetação, tipo de rua, padrão urbano)

### **2. Busca Progressiva**
Faz 3 tentativas com raios crescentes:
1. **5 km** - Busca focada no centro da cidade
2. **10 km** - Expande para subúrbios
3. **20 km** - Busca ampla (região metropolitana)

### **3. Refinamento Automático**
- Para assim que encontrar match com **confiança ≥ 85%**
- Guarda o melhor resultado de todas as tentativas
- Otimiza uso de APIs (para quando encontra)

---

## ⏱️ Tempo Esperado

| Raio | Tempo Estimado | Quando Para |
|------|----------------|-------------|
| 5 km | 2-5 min | Se encontrar com alta confiança |
| 10 km | 5-10 min | Se não encontrou no 5km |
| 20 km | 10-20 min | Busca completa |

**Dica:** Se você souber o bairro, use o modo normal (mais rápido).

---

## 💰 Custos

Como faz busca em área ampla, o custo pode ser maior:

| Cenário | Custo Estimado |
|---------|----------------|
| Encontra no 1º raio (5km) | $5-10 |
| Encontra no 2º raio (10km) | $10-20 |
| Busca completa (20km) | $20-40 |

**Otimização:** O sistema para assim que encontra, economizando APIs.

---

## 📊 Taxa de Sucesso

Baseado em testes:

| Tipo de Imóvel | Taxa de Sucesso |
|----------------|-----------------|
| Casa em rua pública | 80-90% |
| Prédio/apartamento | 70-85% |
| Casa em condomínio aberto | 60-75% |
| Casa em condomínio fechado | 30-50% |
| Área rural/isolada | 20-40% |

**Fatores que aumentam sucesso:**
- ✅ Foto de boa qualidade
- ✅ Elementos distintivos visíveis
- ✅ Texto/placas na foto
- ✅ Área com boa cobertura Street View

---

## 🎯 Dicas para Melhores Resultados

### **1. Qualidade da Foto**
```python
# ✅ BOM
- Foto clara, bem iluminada
- Fachada frontal ou lateral
- Elementos únicos visíveis
- Resolução ≥ 1024x768

# ❌ RUIM
- Foto escura/noturna
- Muito zoom/recorte
- Apenas interior
- Baixa resolução
```

### **2. Especificar a Cidade Correta**
```python
# Se você sabe a cidade, especifique!
resultado = buscar_apenas_por_foto(
    foto_path="foto.jpg",
    cidade="Campinas",  # Cidade correta
    estado="SP"
)
```

### **3. Tentar Múltiplas Cidades**
```python
# Se não tem certeza da cidade
cidades = ["São Paulo", "Guarulhos", "Osasco"]

for cidade in cidades:
    print(f"\n🔍 Tentando em {cidade}...")
    resultado = buscar_apenas_por_foto(
        foto_path="foto.jpg",
        cidade=cidade
    )
    
    if resultado["success"] and resultado["confianca"] >= 0.85:
        print(f"✅ Encontrado em {cidade}!")
        break
```

---

## 🆘 Troubleshooting

### **"Não foi possível localizar o imóvel"**

**Possíveis causas:**
1. Imóvel em área sem Street View
2. Foto de baixa qualidade
3. Cidade errada especificada
4. Imóvel em condomínio fechado

**Soluções:**
```python
# 1. Tentar com foto de melhor qualidade
# 2. Especificar bairro (se souber)
from main import GeoLocalizador

geo = GeoLocalizador()
resultado = geo.localizar_imovel(
    foto_path="foto.jpg",
    cidade="São Paulo",
    bairro="Moema",  # Adicionar bairro
    center_lat=-23.6,  # Coordenadas aproximadas do bairro
    center_lon=-46.7,
    radius_m=3000
)

# 3. Verificar se há Street View na região
import requests
from google.colab import userdata

api_key = userdata.get('GOOGLE_API_KEY')
# ... (código de verificação)
```

### **"Confiança baixa (< 50%)"**

Pode ter encontrado, mas não tem certeza:
```python
# Ver os candidatos encontrados
import pandas as pd

df = pd.read_csv("/content/geolocalizacao/output/candidatos_validados.csv")
print(df[["lat", "lon", "final_confidence", "address"]].head(10))

# Verificar manualmente os top 3
for i in range(min(3, len(df))):
    row = df.iloc[i]
    print(f"\n{i+1}. Confiança: {row['final_confidence']:.1%}")
    print(f"   Endereço: {row.get('address', 'N/A')}")
    print(f"   Maps: https://www.google.com/maps/@{row['lat']},{row['lon']},19z")
```

---

## 📱 Exemplo Completo: Caso de Emergência

```python
# CENÁRIO: Pessoa pedindo socorro, só conseguiu enviar uma foto

# 1. Upload da foto recebida
from google.colab import files
print("📸 Faça upload da foto recebida:")
uploaded = files.upload()
foto_path = list(uploaded.keys())[0]

# 2. Busca urgente
from main import buscar_apenas_por_foto
import time

print("\n🚨 BUSCA URGENTE INICIADA")
print(f"⏰ Início: {time.strftime('%H:%M:%S')}")

resultado = buscar_apenas_por_foto(
    foto_path=foto_path,
    cidade="São Paulo",  # Ajustar conforme caso
    estado="SP"
)

print(f"⏰ Fim: {time.strftime('%H:%M:%S')}")

# 3. Resultado para equipe de resgate
if resultado["success"]:
    print("\n" + "="*70)
    print("🎯 LOCALIZAÇÃO IDENTIFICADA")
    print("="*70)
    print(f"\n📍 ENDEREÇO COMPLETO:")
    print(f"   {resultado['endereco']}")
    print(f"\n📊 CONFIANÇA: {resultado['confianca']:.1%}")
    print(f"\n🗺️  COORDENADAS:")
    print(f"   Latitude: {resultado['coordenadas']['lat']}")
    print(f"   Longitude: {resultado['coordenadas']['lon']}")
    print(f"\n🔗 GOOGLE MAPS:")
    print(f"   {resultado['street_view_link']}")
    print("\n" + "="*70)
else:
    print(f"\n❌ Não foi possível localizar")
    print(f"   Erro: {resultado['error']}")
    if "pistas_encontradas" in resultado:
        print(f"\n📝 Pistas detectadas:")
        for pista in resultado["pistas_encontradas"]:
            print(f"   • {pista}")
```

---

## 🔄 Atualizar para Última Versão

```python
# No Colab, sempre puxe a versão mais recente
%cd geolocalizacao
!git pull
```

---

## 📞 Suporte

Se tiver problemas:
1. Verifique se as APIs estão configuradas
2. Confirme que tem créditos suficientes
3. Teste com foto de exemplo conhecida
4. Veja os logs em `/content/geolocalizacao/output/geolocaliza.log`

---

**🎉 Agora você tem um sistema de investigação por foto! Use com responsabilidade.** 🚔
