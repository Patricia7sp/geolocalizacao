# 🔐 Como Usar com Colab Secrets

## ✅ Correção Aplicada

O código agora suporta **Colab Secrets** automaticamente! Não precisa mais criar arquivo `.env`.

---

## 🔑 Configurar Secrets no Colab

### **Passo 1: Adicionar Secrets**

1. No Colab, clique no ícone de **🔑 chave** na barra lateral esquerda
2. Clique em **"Add new secret"**
3. Adicione as duas chaves:

**Secret 1:**
- **Name:** `GOOGLE_KEY`
- **Value:** `sua_chave_google_aqui`
- ✅ Marque "Notebook access"

**Secret 2:**
- **Name:** `OPENAI_API_KEY`
- **Value:** `sk-proj-sua_chave_openai_aqui`
- ✅ Marque "Notebook access"

---

## 🚀 Usar no Colab

Agora é só clonar e usar:

```python
# 1. Clone do repositório
!git clone https://github.com/Patricia7sp/geolocalizacao.git
%cd geolocalizacao

# 2. Instalar dependências
!pip install -q -r requirements.txt

# 3. Fazer upload da foto
from google.colab import files
uploaded = files.upload()
foto_path = list(uploaded.keys())[0]

# 4. Configurar busca
cidade = "São Paulo"
bairro = "Alto da Boa Vista"
center_lat = -23.6505
center_lon = -46.6815
radius_m = 2000

# 5. EXECUTAR (as chaves serão lidas automaticamente dos Secrets!)
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

# 6. Ver resultado
if resultado["success"]:
    print(f"📍 Endereço: {resultado['endereco']}")
    print(f"🎯 Confiança: {resultado['confianca']:.1%}")
    print(f"\n📊 Scores:")
    print(f"   CLIP: {resultado['scores']['clip']:.3f}")
    print(f"   SIFT: {resultado['scores']['geometria']:.3f}")
    print(f"   LLM:  {resultado['scores']['llm']:.3f}")
else:
    print(f"❌ Erro: {resultado['error']}")
```

---

## 🔍 Como Funciona

O código agora tenta ler as chaves de API em 3 lugares (nesta ordem):

1. **Variáveis de ambiente** (`os.environ`)
2. **Colab Secrets** (`google.colab.userdata`)
3. **Arquivo .env** (para uso local)

Se encontrar em qualquer um desses lugares, funciona! ✅

---

## ⚠️ Importante

- **NÃO** coloque as chaves diretamente no código
- **NÃO** commite arquivo `.env` no Git
- **USE** sempre Colab Secrets no Colab
- **USE** arquivo `.env` apenas localmente

---

## 🆘 Se Ainda Der Erro

Execute esta célula para verificar:

```python
# Verificar se as chaves estão acessíveis
import os

print("🔍 Verificando chaves de API:\n")

# Tentar ler dos Secrets
try:
    from google.colab import userdata
    
    try:
        google_key = userdata.get('GOOGLE_KEY')
        print("✅ GOOGLE_KEY encontrada nos Secrets")
    except:
        print("❌ GOOGLE_KEY NÃO encontrada nos Secrets")
    
    try:
        openai_key = userdata.get('OPENAI_API_KEY')
        print("✅ OPENAI_API_KEY encontrada nos Secrets")
    except:
        print("❌ OPENAI_API_KEY NÃO encontrada nos Secrets")
        
except ImportError:
    print("⚠️  Não está no Colab")
    
# Verificar variáveis de ambiente
if os.getenv('GOOGLE_KEY'):
    print("✅ GOOGLE_KEY em variável de ambiente")
else:
    print("❌ GOOGLE_KEY não está em variável de ambiente")
    
if os.getenv('OPENAI_API_KEY'):
    print("✅ OPENAI_API_KEY em variável de ambiente")
else:
    print("❌ OPENAI_API_KEY não está em variável de ambiente")
```

---

## 💡 Dica

Se você já tinha configurado as chaves com `os.environ`, pode continuar usando:

```python
import os
from getpass import getpass

os.environ["GOOGLE_KEY"] = getpass("Google API Key: ")
os.environ["OPENAI_API_KEY"] = getpass("OpenAI API Key: ")
```

O código vai funcionar das duas formas! ✨
