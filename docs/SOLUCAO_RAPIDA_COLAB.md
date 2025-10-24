# ⚡ Solução Rápida - Erro "No module named 'main'"

## 🔧 Execute Esta Célula ANTES da Célula 6

Cole e execute esta célula no seu Colab **ANTES** de executar a célula de geolocalização:

```python
# 🔍 DIAGNÓSTICO E CORREÇÃO AUTOMÁTICA
import sys
import os

print("🔧 Corrigindo estrutura de arquivos...\n")

# 1. Ir para o diretório correto
os.chdir('/content/geolocaliza')
print(f"✅ Diretório atual: {os.getcwd()}")

# 2. Adicionar ao Python path
if '/content/geolocaliza' not in sys.path:
    sys.path.insert(0, '/content/geolocaliza')
    print("✅ Adicionado ao Python path")

# 3. Criar __init__.py se não existir
init_file = '/content/geolocaliza/agents/__init__.py'
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write('')
    print("✅ Criado agents/__init__.py")

# 4. Verificar arquivos
print("\n📁 Verificando arquivos:")
arquivos_necessarios = {
    'config.py': '/content/geolocaliza/config.py',
    'main.py': '/content/geolocaliza/main.py',
    'agents/vision_agent.py': '/content/geolocaliza/agents/vision_agent.py',
    'agents/search_agent.py': '/content/geolocaliza/agents/search_agent.py',
    'agents/matching_agent.py': '/content/geolocaliza/agents/matching_agent.py',
    'agents/validation_agent.py': '/content/geolocaliza/agents/validation_agent.py',
}

todos_ok = True
for nome, caminho in arquivos_necessarios.items():
    existe = os.path.exists(caminho)
    status = "✅" if existe else "❌"
    print(f"   {status} {nome}")
    if not existe:
        todos_ok = False

# 5. Testar importação
print("\n🧪 Testando importação:")
if todos_ok:
    try:
        import config
        print("   ✅ config.py")
    except Exception as e:
        print(f"   ❌ config.py: {e}")
        todos_ok = False
    
    try:
        import main
        print("   ✅ main.py")
    except Exception as e:
        print(f"   ❌ main.py: {e}")
        todos_ok = False
    
    try:
        from agents import vision_agent
        print("   ✅ agents/vision_agent.py")
    except Exception as e:
        print(f"   ❌ agents/vision_agent.py: {e}")
        todos_ok = False

# 6. Resultado final
print("\n" + "="*70)
if todos_ok:
    print("🎉 TUDO OK! Pode executar a célula de geolocalização.")
    print("="*70)
else:
    print("❌ AINDA HÁ PROBLEMAS!")
    print("="*70)
    print("\n💡 SOLUÇÃO:")
    print("   1. Execute a célula abaixo para listar os arquivos")
    print("   2. Se algum arquivo estiver faltando, volte para célula 2")
    print("   3. Faça upload de TODOS os arquivos .py novamente")
    print("   4. Execute esta célula de diagnóstico novamente")
```

---

## 📋 Se Ainda Não Funcionar

Execute esta célula para ver EXATAMENTE o que está no Colab:

```python
# 📁 LISTAR TODOS OS ARQUIVOS
import os

print("="*70)
print("📁 ESTRUTURA COMPLETA")
print("="*70)

print("\n📂 /content/geolocaliza/")
if os.path.exists('/content/geolocaliza'):
    for item in os.listdir('/content/geolocaliza'):
        path = f'/content/geolocaliza/{item}'
        if os.path.isdir(path):
            print(f"   📁 {item}/")
            # Listar conteúdo da pasta
            for subitem in os.listdir(path):
                print(f"      📄 {subitem}")
        else:
            size = os.path.getsize(path)
            print(f"   📄 {item} ({size} bytes)")
else:
    print("   ❌ Diretório não existe!")

print("\n" + "="*70)
```

---

## 🚨 Solução Definitiva

Se nada funcionar, execute estas células em sequência:

### **Célula 1: Limpar Tudo**
```python
# Limpar e recomeçar
!rm -rf /content/geolocaliza
!mkdir -p /content/geolocaliza/agents
!mkdir -p /content/geolocaliza/output
!mkdir -p /content/geolocaliza/cache
print("✅ Estrutura limpa e recriada")
```

### **Célula 2: Upload dos Arquivos**
```python
from google.colab import files
import shutil
import os

os.chdir('/content/geolocaliza')

print("📤 Faça upload de TODOS os arquivos .py:")
print("   • config.py")
print("   • main.py")
print("   • vision_agent.py")
print("   • search_agent.py")
print("   • matching_agent.py")
print("   • validation_agent.py")
print("\nSelecione TODOS de uma vez!\n")

uploaded = files.upload()

# Organizar
for filename in uploaded.keys():
    if 'agent' in filename.lower():
        dest = f'/content/geolocaliza/agents/{filename}'
        shutil.move(filename, dest)
        print(f"✓ {filename} → agents/")
    else:
        dest = f'/content/geolocaliza/{filename}'
        if filename != dest:
            shutil.move(filename, dest)
        print(f"✓ {filename} → raiz")

# Criar __init__.py
with open('/content/geolocaliza/agents/__init__.py', 'w') as f:
    f.write('')

print("\n✅ Upload completo!")
```

### **Célula 3: Verificar**
```python
import os

print("🔍 Verificação final:\n")

arquivos = [
    '/content/geolocaliza/config.py',
    '/content/geolocaliza/main.py',
    '/content/geolocaliza/agents/__init__.py',
    '/content/geolocaliza/agents/vision_agent.py',
    '/content/geolocaliza/agents/search_agent.py',
    '/content/geolocaliza/agents/matching_agent.py',
    '/content/geolocaliza/agents/validation_agent.py',
]

todos_ok = True
for arquivo in arquivos:
    existe = os.path.exists(arquivo)
    status = "✅" if existe else "❌"
    nome = arquivo.replace('/content/geolocaliza/', '')
    print(f"{status} {nome}")
    if not existe:
        todos_ok = False

if todos_ok:
    print("\n🎉 Perfeito! Agora pode executar a célula de geolocalização.")
else:
    print("\n❌ Ainda faltam arquivos. Repita o upload.")
```

---

## 💡 Causa Mais Comum

O erro acontece porque:

1. **Os arquivos foram enviados para o lugar errado** (ex: `/content/` ao invés de `/content/geolocaliza/`)
2. **Falta o arquivo `__init__.py`** na pasta `agents/`
3. **O Python path não está configurado** corretamente

A solução acima corrige todos esses problemas!

---

## 📞 Ainda com Problemas?

Execute esta célula e me envie a saída:

```python
import sys
import os

print("DIAGNÓSTICO COMPLETO:")
print("="*70)
print(f"Diretório atual: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")
print("\nArquivos em /content:")
!ls -la /content/
print("\nArquivos em /content/geolocaliza:")
!ls -la /content/geolocaliza/
print("\nArquivos em /content/geolocaliza/agents:")
!ls -la /content/geolocaliza/agents/
print("="*70)
```

Com essa saída, posso te ajudar melhor! 🚀
