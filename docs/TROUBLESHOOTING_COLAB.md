# 🔧 Troubleshooting - Google Colab

## ❌ Erro: "ModuleNotFoundError: No module named 'main'"

### **Causa**
O arquivo `main.py` não está no diretório correto ou não foi feito upload.

### **Solução Passo a Passo**

#### **1. Verificar se os arquivos foram enviados**
Execute esta célula no Colab:

```python
import os
print("📁 Arquivos na raiz:")
!ls -la /content/geolocaliza/

print("\n📁 Arquivos em agents/:")
!ls -la /content/geolocaliza/agents/
```

**Você deve ver:**
```
/content/geolocaliza/
├── config.py
├── main.py
└── agents/
    ├── __init__.py
    ├── vision_agent.py
    ├── search_agent.py
    ├── matching_agent.py
    └── validation_agent.py
```

#### **2. Se os arquivos estão faltando**

**Opção A: Upload Manual Correto**
1. Na célula de upload, selecione **TODOS** os arquivos de uma vez:
   - `config.py`
   - `main.py`
   - `vision_agent.py`
   - `search_agent.py`
   - `matching_agent.py`
   - `validation_agent.py`

2. Execute a célula de upload
3. Execute a célula de verificação

**Opção B: Upload via Google Drive**
```python
# 1. Monte o Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Copie os arquivos do Drive
!cp -r /content/drive/MyDrive/geolocalizacao/geolocaliza/* /content/geolocaliza/

# 3. Crie __init__.py
!touch /content/geolocaliza/agents/__init__.py

# 4. Verifique
!ls -la /content/geolocaliza/
```

**Opção C: Clone do GitHub**
```python
# Se você tem o projeto no GitHub
!git clone https://github.com/seu-usuario/geolocalizacao.git
%cd geolocalizacao/geolocaliza
```

#### **3. Criar estrutura manualmente (se necessário)**
```python
import os

# Criar diretórios
os.makedirs('/content/geolocaliza/agents', exist_ok=True)
os.makedirs('/content/geolocaliza/output', exist_ok=True)
os.makedirs('/content/geolocaliza/cache', exist_ok=True)

# Criar __init__.py
with open('/content/geolocaliza/agents/__init__.py', 'w') as f:
    f.write('')

print("✅ Estrutura criada!")
```

---

## ❌ Erro: "ImportError: cannot import name 'X' from 'agents'"

### **Causa**
Falta o arquivo `__init__.py` na pasta `agents/`.

### **Solução**
```python
# Criar __init__.py vazio
!touch /content/geolocaliza/agents/__init__.py

# Verificar
!ls -la /content/geolocaliza/agents/__init__.py
```

---

## ❌ Erro: "OPENAI_API_KEY não configurada"

### **Causa**
A chave da OpenAI não foi configurada ou o arquivo `.env` não foi criado.

### **Solução**
```python
import os
from getpass import getpass

# Configurar novamente
OPENAI_KEY = getpass("Cole sua OpenAI API Key: ")
os.environ["OPENAI_API_KEY"] = OPENAI_KEY

# Criar .env
with open('/content/geolocaliza/.env', 'w') as f:
    f.write(f"OPENAI_API_KEY={OPENAI_KEY}\n")
    f.write(f"GOOGLE_API_KEY={os.getenv('GOOGLE_API_KEY', '')}\n")

print("✅ Chave configurada!")
```

---

## ❌ Erro: "No module named 'anthropic'"

### **Causa**
O código ainda está tentando importar Anthropic (versão antiga).

### **Solução**
Certifique-se de que você fez upload dos arquivos **atualizados** que usam OpenAI.

Verifique se os arquivos contêm:
```python
# ✅ Correto (OpenAI)
from openai import OpenAI

# ❌ Errado (Anthropic - versão antiga)
import anthropic
```

Se ainda estiver com Anthropic, baixe os arquivos atualizados do projeto.

---

## ❌ Erro: "CUDA out of memory"

### **Causa**
GPU com pouca memória para o modelo CLIP.

### **Solução**
```python
# Forçar uso de CPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Ou editar config.py antes de executar
# Em matching_agent.py, linha ~31:
# self.device = "cpu"
```

---

## ❌ Erro: "Rate limit exceeded" (OpenAI)

### **Causa**
Muitas requisições em pouco tempo.

### **Solução**
```python
# Adicionar delay entre requisições
import time
time.sleep(2)  # Aguardar 2 segundos

# Ou verificar seu tier em platform.openai.com
# Tier 1: 500 req/min
# Tier Free: 3 req/min
```

---

## ❌ Erro: "Insufficient credits" (OpenAI)

### **Causa**
Créditos da OpenAI esgotados.

### **Solução**
1. Acesse [platform.openai.com](https://platform.openai.com/)
2. Vá em **Settings** → **Billing**
3. Adicione mais créditos
4. Aguarde alguns minutos para processar

---

## 🔄 Reiniciar Tudo do Zero

Se nada funcionar, reinicie completamente:

```python
# 1. Limpar tudo
!rm -rf /content/geolocaliza
!rm -rf /content/sample_data

# 2. Reiniciar runtime
# Menu: Runtime → Restart runtime

# 3. Começar do zero
# Execute célula por célula desde o início
```

---

## 📋 Checklist de Verificação

Antes de executar a célula 6 (Executar Geolocalização):

- [ ] ✅ Célula 1 (Instalação) executada sem erros
- [ ] ✅ Célula 2 (Upload) - Todos os arquivos enviados
- [ ] ✅ Célula 2.5 (Verificação) - Todos os arquivos ✅
- [ ] ✅ Célula 3 (APIs) - Chaves configuradas
- [ ] ✅ Célula 4 (Foto) - Foto enviada
- [ ] ✅ Célula 5 (Busca) - Coordenadas configuradas
- [ ] ✅ Diretório correto: `/content/geolocaliza`
- [ ] ✅ Arquivo `main.py` existe
- [ ] ✅ Arquivo `.env` criado

---

## 🆘 Comando de Debug Completo

Execute esta célula para diagnóstico completo:

```python
import os
import sys

print("=" * 70)
print("🔍 DIAGNÓSTICO COMPLETO")
print("=" * 70)

# 1. Diretório atual
print(f"\n📂 Diretório atual: {os.getcwd()}")

# 2. Python path
print(f"\n🐍 Python path:")
for p in sys.path[:5]:
    print(f"   {p}")

# 3. Arquivos na raiz
print(f"\n📁 Arquivos em /content/geolocaliza/:")
if os.path.exists('/content/geolocaliza'):
    for f in os.listdir('/content/geolocaliza'):
        path = f'/content/geolocaliza/{f}'
        tipo = "📁" if os.path.isdir(path) else "📄"
        print(f"   {tipo} {f}")
else:
    print("   ❌ Diretório não existe!")

# 4. Arquivos em agents/
print(f"\n📁 Arquivos em /content/geolocaliza/agents/:")
if os.path.exists('/content/geolocaliza/agents'):
    for f in os.listdir('/content/geolocaliza/agents'):
        print(f"   📄 {f}")
else:
    print("   ❌ Diretório não existe!")

# 5. Variáveis de ambiente
print(f"\n🔑 APIs configuradas:")
print(f"   GOOGLE_API_KEY: {'✅' if os.getenv('GOOGLE_API_KEY') else '❌'}")
print(f"   OPENAI_API_KEY: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")

# 6. Arquivo .env
print(f"\n📄 Arquivo .env:")
env_path = '/content/geolocaliza/.env'
if os.path.exists(env_path):
    print(f"   ✅ Existe")
    with open(env_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            key = line.split('=')[0]
            print(f"   • {key}")
else:
    print(f"   ❌ Não existe")

# 7. Tentar importar
print(f"\n🧪 Teste de importação:")
try:
    sys.path.insert(0, '/content/geolocaliza')
    import config
    print("   ✅ config.py")
except Exception as e:
    print(f"   ❌ config.py: {e}")

try:
    import main
    print("   ✅ main.py")
except Exception as e:
    print(f"   ❌ main.py: {e}")

try:
    from agents import vision_agent
    print("   ✅ agents/vision_agent.py")
except Exception as e:
    print(f"   ❌ agents/vision_agent.py: {e}")

print("\n" + "=" * 70)
```

---

## 💡 Dicas Gerais

1. **Execute as células em ordem** - Não pule células
2. **Aguarde cada célula terminar** - Não execute múltiplas ao mesmo tempo
3. **Leia as mensagens de erro** - Elas indicam o problema
4. **Use a célula de verificação** - Sempre execute após o upload
5. **Reinicie se necessário** - Runtime → Restart runtime

---

**Se o erro persistir, copie a saída do "Comando de Debug Completo" e peça ajuda!**
