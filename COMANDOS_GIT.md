# 🚀 Comandos para Subir no GitHub

## 1️⃣ Preparar Repositório Local

```bash
cd /usr/local/anaconda3/Agentes_youtube/geolocalizacao/geolocaliza

# Adicionar todos os arquivos
git add .

# Commit inicial
git commit -m "Initial commit: Sistema de Geolocalização de Imóveis

- Sistema multi-agente com GPT-4o e Google Maps APIs
- Análise visual, busca geográfica, matching e validação
- Suporte para Google Colab com GPU
- Documentação completa em português
"
```

## 2️⃣ Criar Repositório no GitHub

1. Acesse [github.com/new](https://github.com/new)
2. **Repository name:** `geolocalizacao-imoveis`
3. **Description:** `Sistema de geolocalização de imóveis usando IA e visão computacional`
4. **Public** ou **Private** (sua escolha)
5. **NÃO** marque "Add a README file" (já temos)
6. **NÃO** marque "Add .gitignore" (já temos)
7. Clique em **Create repository**

## 3️⃣ Conectar e Fazer Push

Após criar o repositório, o GitHub vai mostrar comandos. Use estes:

```bash
# Adicionar remote (substitua SEU-USUARIO pelo seu username)
git remote add origin https://github.com/SEU-USUARIO/geolocalizacao-imoveis.git

# Renomear branch para main (se necessário)
git branch -M main

# Push inicial
git push -u origin main
```

## 4️⃣ Verificar

Acesse: `https://github.com/SEU-USUARIO/geolocalizacao-imoveis`

Você deve ver:
- ✅ README.md renderizado
- ✅ Todos os arquivos .py
- ✅ Documentação em docs/
- ✅ .gitignore funcionando (sem .env, output/, cache/)

---

## 🔄 Atualizações Futuras

Quando fizer mudanças:

```bash
# Ver o que mudou
git status

# Adicionar mudanças
git add .

# Commit
git commit -m "Descrição da mudança"

# Push
git push
```

---

## 📝 Renomear README

Após o push, renomeie o README:

```bash
# Renomear README_GITHUB.md para README.md
mv README_GITHUB.md README.md

# Commit
git add README.md
git commit -m "Rename README"
git push
```

---

## 🎯 Usar no Colab

Depois do push, no Colab use:

```python
!git clone https://github.com/SEU-USUARIO/geolocalizacao-imoveis.git
%cd geolocalizacao-imoveis
!pip install -q -r requirements.txt
```

**Muito mais simples!** ✨
