# 🎯 Análise Combinada - Múltiplas Fotos Externas

## 📸 Para Que Serve

Use quando você tem **2 ou mais fotos externas** do mesmo imóvel:
- Fachada frontal + lateral
- Diferentes ângulos da casa
- Portão + fachada
- Entrada + lateral

**Vantagens:**
- ✅ **Mais pistas** - Combina informações de todas as fotos
- ✅ **Maior precisão** - Seleciona automaticamente a melhor foto
- ✅ **Mais confiança** - Valida com múltiplos ângulos
- ✅ **Redundância** - Se uma foto falhar, usa outra

---

## 🚀 Como Usar no Colab

### **Uso Básico (2 Fotos)**

```python
# 1. Clone e instale
!git clone https://github.com/Patricia7sp/geolocalizacao.git
%cd geolocalizacao
!pip install -q -r requirements.txt

# 2. Upload das fotos
from google.colab import files

print("📸 Faça upload das fotos externas do imóvel:")
uploaded = files.upload()

# Pegar todas as fotos enviadas
fotos = list(uploaded.keys())
print(f"\n✅ {len(fotos)} foto(s) enviada(s):")
for i, foto in enumerate(fotos, 1):
    print(f"   {i}. {foto}")

# 3. BUSCAR COM MÚLTIPLAS FOTOS
from main import buscar_com_multiplas_fotos

resultado = buscar_com_multiplas_fotos(
    fotos=fotos,  # Lista com todas as fotos
    cidade="São Paulo"
)

# 4. Ver resultado
if resultado["success"]:
    print(f"\n🎉 LOCALIZAÇÃO ENCONTRADA!")
    print(f"📍 Endereço: {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
else:
    print(f"\n❌ Não encontrado: {resultado['error']}")
```

---

## 📋 Exemplo Completo com Visualização

```python
# 1. Upload das fotos
from google.colab import files
from PIL import Image
import matplotlib.pyplot as plt

print("📸 Faça upload de 2-5 fotos externas do imóvel:\n")
uploaded = files.upload()

fotos = list(uploaded.keys())
print(f"\n✅ {len(fotos)} foto(s) enviada(s)")

# 2. Visualizar todas as fotos
fig, axes = plt.subplots(1, len(fotos), figsize=(15, 5))
if len(fotos) == 1:
    axes = [axes]

for i, foto in enumerate(fotos):
    img = Image.open(foto)
    axes[i].imshow(img)
    axes[i].set_title(f"Foto {i+1}: {foto}")
    axes[i].axis('off')

plt.tight_layout()
plt.show()

# 3. Buscar
from main import buscar_com_multiplas_fotos

print("\n🔍 Iniciando análise combinada...")
print(f"   Total de fotos: {len(fotos)}")
print(f"   Cidade: São Paulo")
print("\n⏰ Aguarde 3-10 minutos...\n")

resultado = buscar_com_multiplas_fotos(
    fotos=fotos,
    cidade="São Paulo",
    estado="SP"
)

# 4. Resultado detalhado
print("\n" + "="*70)
if resultado["success"]:
    print("🎉 SUCESSO!")
    print("="*70)
    print(f"\n📍 ENDEREÇO COMPLETO:")
    print(f"   {resultado['endereco']}")
    print(f"\n🎯 CONFIANÇA: {resultado['confianca']:.1%}")
    print(f"\n📊 SCORES:")
    print(f"   CLIP (semântico): {resultado['scores']['clip']:.3f}")
    print(f"   SIFT (geométrico): {resultado['scores']['geometria']:.3f}")
    print(f"   LLM (validação): {resultado['scores']['llm']:.3f}")
    print(f"\n🗺️  GOOGLE MAPS:")
    print(f"   {resultado['street_view_link']}")
else:
    print("❌ NÃO ENCONTRADO")
    print("="*70)
    print(f"\n   Erro: {resultado['error']}")
    if "hint" in resultado:
        print(f"\n💡 Dica: {resultado['hint']}")
print("\n" + "="*70)
```

---

## 🔍 Como Funciona Internamente

### **Etapa 1: Análise de Todas as Fotos**
```
📸 Foto 1: fachada_frontal.jpg
   ✅ Análise concluída
   
📸 Foto 2: fachada_lateral.jpg
   ✅ Análise concluída

✅ 2 foto(s) analisada(s) com sucesso
📝 Pistas combinadas encontradas: 5
```

### **Etapa 2: Seleção da Melhor Foto**
```
🎯 Pontuação de cada foto:
   Foto 1: score = 12 (3 características + 2 textos + 1 landmark)
   Foto 2: score = 8  (2 características + 1 texto)
   
✅ Melhor foto selecionada: fachada_frontal.jpg
```

### **Etapa 3: Busca com Foto Selecionada**
```
🔍 Executando busca progressiva:
   5km → 10km → 20km
   
✅ Encontrado com confiança: 92%
```

---

## 📊 Critérios de Seleção da Melhor Foto

O sistema pontua cada foto baseado em:

| Característica | Peso | Exemplo |
|----------------|------|---------|
| Texto detectado | 3x | Número da casa, placa de rua |
| Pontos de referência | 2x | Igreja, loja, monumento |
| Características distintivas | 2x | Cor única, portão, janelas |

**Foto com maior pontuação** = Usada para matching

---

## 💡 Dicas para Melhores Resultados

### **✅ Fotos Ideais:**

1. **Fachada frontal** - Vista completa da frente
2. **Fachada lateral** - Mostra outro ângulo
3. **Portão/Entrada** - Detalhes únicos
4. **Vista da rua** - Contexto do entorno

### **❌ Evite:**

- Fotos muito próximas (só detalhes)
- Fotos noturnas/escuras
- Fotos desfocadas
- Fotos internas
- Fotos com muita obstrução

---

## ⏱️ Tempo e Custo

### **Tempo Estimado:**

| Fotos | Análise | Busca | Total |
|-------|---------|-------|-------|
| 2 fotos | 30s | 2-10 min | 3-11 min |
| 3 fotos | 45s | 2-10 min | 3-11 min |
| 5 fotos | 75s | 2-10 min | 3-11 min |

**Nota:** Tempo de busca é o mesmo (usa só a melhor foto)

### **Custo Estimado:**

| Item | Custo |
|------|-------|
| Análise de 2 fotos | $0.02 |
| Análise de 5 fotos | $0.05 |
| Busca (5-20km) | $5-40 |
| **TOTAL** | **$5-40** |

**Custo adicional de análise é mínimo!**

---

## 🆚 Comparação: 1 Foto vs Múltiplas

| Aspecto | 1 Foto | 2-5 Fotos |
|---------|--------|-----------|
| **Precisão** | 80-90% | 85-95% |
| **Confiança** | Média | Alta |
| **Redundância** | Não | Sim |
| **Tempo** | 2-10 min | 3-11 min |
| **Custo** | $5-40 | $5-40 |
| **Recomendado para** | Casos simples | Casos complexos |

---

## 🎯 Quando Usar Cada Modo

### **Use 1 Foto Quando:**
- ✅ Foto de excelente qualidade
- ✅ Fachada muito distintiva
- ✅ Quer resultado mais rápido
- ✅ Quer economizar análise

### **Use Múltiplas Fotos Quando:**
- ✅ Imóvel complexo (condomínio)
- ✅ Quer máxima precisão
- ✅ Tem várias fotos disponíveis
- ✅ Primeira tentativa falhou

---

## 🔄 Atualizar para Última Versão

```python
# No Colab, sempre puxe a versão mais recente
%cd geolocalizacao
!git pull
```

---

## 📞 Exemplo Real: Corretagem

```python
# Cliente te manda 2 fotos de uma casa
# Você não sabe onde é

from google.colab import files
from main import buscar_com_multiplas_fotos

# Upload
print("📸 Envie as fotos que o cliente mandou:")
uploaded = files.upload()
fotos = list(uploaded.keys())

# Buscar
resultado = buscar_com_multiplas_fotos(
    fotos=fotos,
    cidade="São Paulo"  # Ou a cidade que você acha
)

# Responder ao cliente
if resultado["success"]:
    print(f"\n✅ Imóvel localizado!")
    print(f"📍 {resultado['endereco']}")
    print(f"🗺️  {resultado['street_view_link']}")
    
    # Copiar endereço para responder
    endereco = resultado['endereco']
else:
    print(f"\n❌ Não consegui localizar")
    print("💡 Pode pedir mais informações ao cliente?")
```

---

**🎉 Pronto! Agora você tem análise combinada com múltiplas fotos!** 📸✨
